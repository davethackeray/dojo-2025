import feedparser
import requests
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import csv
from pathlib import Path
import hashlib
import math
from pydub import AudioSegment
import tempfile
import google.generativeai as genai
from typing import Optional, Dict, Any, List
import threading
from queue import Queue

class PodcastHarvester:
    def __init__(self, download_dir="podcast_downloads", max_workers=5, batch_size=50, 
                 compress_audio=True, target_bitrate=32, transcribe_audio=True, 
                 gemini_api_key=None):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.compress_audio = compress_audio
        self.target_bitrate = target_bitrate
        self.transcribe_audio = transcribe_audio
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Create directory for storing podcast lists
        self.lists_dir = Path("podcast_lists")
        self.lists_dir.mkdir(exist_ok=True)
        
        # Transcription setup
        if transcribe_audio and gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
            self.transcription_queue = Queue()
            self.rate_limiter = self._create_rate_limiter()
        else:
            self.gemini_model = None
            
    def _create_rate_limiter(self):
        """Create rate limiter for Gemini API (10 RPM)"""
        return {
            'last_request_time': 0,
            'request_count': 0,
            'window_start': time.time(),
            'requests_per_minute': 10,
            'requests_per_day': 1500,
            'daily_count': 0,
            'daily_reset': time.time()
        }
    
    def _wait_for_rate_limit(self):
        """Handle Gemini API rate limiting"""
        current_time = time.time()
        
        # Check daily limit
        if current_time - self.rate_limiter['daily_reset'] > 86400:  # 24 hours
            self.rate_limiter['daily_count'] = 0
            self.rate_limiter['daily_reset'] = current_time
            
        if self.rate_limiter['daily_count'] >= self.rate_limiter['requests_per_day']:
            print("⚠️  Daily Gemini API limit reached. Skipping remaining transcriptions.")
            return False
            
        # Check per-minute limit
        if current_time - self.rate_limiter['window_start'] > 60:  # Reset window
            self.rate_limiter['request_count'] = 0
            self.rate_limiter['window_start'] = current_time
            
        if self.rate_limiter['request_count'] >= self.rate_limiter['requests_per_minute']:
            wait_time = 60 - (current_time - self.rate_limiter['window_start'])
            print(f"⏳  Rate limit reached. Waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time + 1)
            self.rate_limiter['request_count'] = 0
            self.rate_limiter['window_start'] = time.time()
            
        # Ensure minimum gap between requests (6 seconds for 10 RPM)
        time_since_last = current_time - self.rate_limiter['last_request_time']
        if time_since_last < 6:
            time.sleep(6 - time_since_last)
            
        return True
        
    def is_recent_episode(self, published_date, days_back=7):
        """Check if episode was published within the last specified days"""
        if not published_date:
            return False
            
        try:
            # Parse the published date
            episode_date = datetime(*published_date[:6])
            cutoff_date = datetime.now() - timedelta(days=days_back)
            return episode_date >= cutoff_date
        except (TypeError, ValueError):
            return False
    
    def extract_audio_url(self, entry):
        """Extract MP3 or audio URL from RSS entry"""
        audio_url = None
        
        # Check enclosures first (most common)
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if 'audio' in enclosure.get('type', '').lower():
                    audio_url = enclosure.get('url') or enclosure.get('href')
                    break
        
        # Check links
        if not audio_url and hasattr(entry, 'links'):
            for link in entry.links:
                if link.get('type', '').startswith('audio'):
                    audio_url = link.get('href')
                    break
        
        # Check media content
        if not audio_url and hasattr(entry, 'media_content'):
            for media in entry.media_content:
                if 'audio' in media.get('type', '').lower():
                    audio_url = media.get('url')
                    break
                    
        return audio_url
    
    def sanitise_filename(self, filename):
        """Clean filename for safe saving"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:200]  # Limit length
    
    def generate_unique_id(self, podcast_title, episode_title, published_date):
        """Generate a unique ID for each episode"""
        content = f"{podcast_title}_{episode_title}_{published_date}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]
    
    def create_batch_directory(self, batch_number):
        """Create a directory for a specific batch"""
        batch_dir = self.download_dir / f"batch_{batch_number:03d}"
        batch_dir.mkdir(exist_ok=True)
        return batch_dir
    
    def _format_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0B"
        size_names = ["B", "KB", "MB", "GB"]
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s}{size_names[i]}"
    
    def compress_audio_file(self, input_path, output_path):
        """Compress audio file for transcription purposes"""
        try:
            print(f"  🔧 Compressing {input_path.name}...")
            
            # Load the audio file
            audio = AudioSegment.from_file(str(input_path))
            
            # Get original file size for comparison
            original_size = input_path.stat().st_size
            
            # Apply aggressive compression for transcription:
            # 1. Convert to mono (speech doesn't need stereo)
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # 2. Reduce sample rate to 22kHz (fine for speech recognition)
            audio = audio.set_frame_rate(22050)
            
            # 3. Normalise volume to ensure consistent levels
            audio = audio.normalize()
            
            # 4. Export with low bitrate
            audio.export(
                str(output_path),
                format="mp3",
                bitrate=f"{self.target_bitrate}k",
                parameters=[
                    "-ac", "1",  # Force mono
                    "-ar", "22050",  # Sample rate
                    "-q:a", "9",  # Lowest quality for maximum compression
                ]
            )
            
            # Get compressed file size
            compressed_size = output_path.stat().st_size
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            print(f"  ✓ Compressed: {self._format_size(original_size)} → {self._format_size(compressed_size)} "
                  f"({compression_ratio:.1f}% reduction)")
            
            return str(output_path)
            
        except Exception as e:
            print(f"  ✗ Compression failed for {input_path.name}: {str(e)}")
            # If compression fails, keep the original
            if input_path != output_path:
                import shutil
                shutil.move(str(input_path), str(output_path))
            return str(output_path)
    
    def transcribe_audio_file(self, audio_file_path: Path, episode_data: Dict) -> Optional[str]:
        """Transcribe audio file using Gemini AI"""
        if not self.gemini_model:
            return None
            
        try:
            # Check rate limits
            if not self._wait_for_rate_limit():
                return None
                
            print(f"  🎯 Transcribing {audio_file_path.name}...")
            
            # Check file size (Gemini has limits)
            file_size = audio_file_path.stat().st_size
            max_size = 20 * 1024 * 1024  # 20MB limit for Gemini
            
            if file_size > max_size:
                print(f"  ⚠️  File too large for transcription: {self._format_size(file_size)}")
                return None
            
            # Upload and transcribe
            audio_file = genai.upload_file(str(audio_file_path))
            
            # Create transcription prompt
            prompt = """
            Please provide a complete, accurate transcription of this podcast episode. 
            
            Format the output as clean, readable text with proper punctuation and paragraph breaks where speakers change or topics shift.
            
            Include speaker labels if you can identify different voices (e.g., "Host:", "Guest:", etc.).
            
            Focus on accuracy and readability - this transcript will be used for content analysis.
            """
            
            # Generate transcription
            response = self.gemini_model.generate_content([prompt, audio_file])
            
            # Update rate limiter
            self.rate_limiter['request_count'] += 1
            self.rate_limiter['daily_count'] += 1
            self.rate_limiter['last_request_time'] = time.time()
            
            # Clean up uploaded file
            genai.delete_file(audio_file.name)
            
            if response and response.text:
                transcript = response.text.strip()
                
                # Save transcript to file
                transcript_filename = audio_file_path.stem + "_transcript.txt"
                transcript_path = audio_file_path.parent / transcript_filename
                
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write(f"PODCAST TRANSCRIPT\n")
                    f.write(f"="*50 + "\n")
                    f.write(f"Podcast: {episode_data.get('podcast_title', 'Unknown')}\n")
                    f.write(f"Episode: {episode_data.get('episode_title', 'Unknown')}\n")
                    f.write(f"Transcribed: {datetime.now().isoformat()}\n")
                    f.write(f"Audio File: {audio_file_path.name}\n")
                    f.write(f"="*50 + "\n\n")
                    f.write(transcript)
                
                print(f"  ✓ Transcribed: {len(transcript)} characters")
                return str(transcript_path)
            else:
                print(f"  ✗ Transcription failed: No response")
                return None
                
        except Exception as e:
            print(f"  ✗ Transcription failed: {str(e)}")
            return None
    
    def extract_basic_metadata(self, entry, feed, rss_url):
        """Extract only the essential metadata needed for CSV"""
        return {
            # Essential data only
            'podcast_title': feed.feed.get('title', 'Unknown Podcast'),
            'episode_title': entry.get('title', 'Untitled'),
            'episode_url': entry.get('link', ''),
            'media_url': self.extract_audio_url(entry),
            
            # Internal processing data (not in CSV)
            'episode_id': self.generate_unique_id(
                feed.feed.get('title', 'Unknown'),
                entry.get('title', 'Untitled'),
                entry.get('published', '')
            ),
            'published_date': entry.get('published', ''),
            'download_status': 'pending',
            'transcription_status': 'pending',
            'local_filename': '',
            'local_filepath': '',
            'transcript_filepath': '',
            'batch_number': 0  # Will be set during batching
        }
    
    def download_audio_file(self, url, final_filepath):
        """Download and optionally compress audio file"""
        try:
            # If compression is enabled, download to temp file first
            if self.compress_audio:
                # Create temp file for original download
                temp_dir = final_filepath.parent / "temp"
                temp_dir.mkdir(exist_ok=True)
                temp_filepath = temp_dir / f"temp_{final_filepath.name}"
            else:
                temp_filepath = final_filepath
            
            # Download the file
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(temp_filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Compress if enabled
            if self.compress_audio:
                compressed_path = self.compress_audio_file(temp_filepath, final_filepath)
                
                # Clean up temp file
                try:
                    temp_filepath.unlink()
                    if temp_dir.exists() and not any(temp_dir.iterdir()):
                        temp_dir.rmdir()
                except:
                    pass
                
                return compressed_path
            else:
                return str(final_filepath)
                
        except Exception as e:
            print(f"Error downloading {final_filepath.name}: {str(e)}")
            return None
    
    def process_podcast_feed(self, rss_url, podcast_name=None, days_back=None, num_episodes=None):
        """Process a single podcast RSS feed with optional filters"""
        episodes_data = []
        
        try:
            print(f"Processing: {rss_url}")
            feed = feedparser.parse(rss_url)
            
            if not hasattr(feed, 'entries'):
                print(f"No entries found in feed: {rss_url}")
                return episodes_data
            
            # Sort entries by published date (newest first)
            entries = sorted(feed.entries, 
                           key=lambda x: x.get('published_parsed', time.struct_time((1970,1,1,0,0,0,0,0,0))), 
                           reverse=True)
            
            processed_count = 0
            for entry in entries:
                # If we're looking for a specific number of episodes
                if num_episodes and processed_count >= num_episodes:
                    break
                
                # Check if episode is recent (if days_back is specified)
                if days_back and not self.is_recent_episode(entry.get('published_parsed'), days_back):
                    continue
                
                # Extract audio URL
                audio_url = self.extract_audio_url(entry)
                if not audio_url:
                    continue
                
                # Extract basic metadata
                episode_data = self.extract_basic_metadata(entry, feed, rss_url)
                episodes_data.append(episode_data)
                processed_count += 1
                
        except Exception as e:
            print(f"Error processing feed {rss_url}: {str(e)}")
            
        return episodes_data
    
    def create_batches(self, episodes_data):
        """Split episodes into batches of specified size"""
        batches = []
        total_episodes = len(episodes_data)
        num_batches = math.ceil(total_episodes / self.batch_size)
        
        for i in range(num_batches):
            start_idx = i * self.batch_size
            end_idx = min(start_idx + self.batch_size, total_episodes)
            batch = episodes_data[start_idx:end_idx]
            
            # Assign batch number to each episode
            for episode in batch:
                episode['batch_number'] = i + 1
            
            batches.append({
                'batch_number': i + 1,
                'episodes': batch,
                'total_episodes': len(batch)
            })
        
        return batches
    
    def download_batch(self, batch_info):
        """Download all episodes in a batch"""
        batch_number = batch_info['batch_number']
        episodes = batch_info['episodes']
        
        print(f"\n=== Processing Batch {batch_number} ({len(episodes)} episodes) ===")
        
        # Create batch directory
        batch_dir = self.create_batch_directory(batch_number)
        
        # Download episodes in this batch
        downloaded_episodes = []
        for episode in episodes:
            try:
                # Create safe filename
                safe_podcast = self.sanitise_filename(episode['podcast_title'])
                safe_episode = self.sanitise_filename(episode['episode_title'])
                episode_id = episode['episode_id']
                
                filename = f"{episode_id}_{safe_podcast}_{safe_episode}.mp3"
                filepath = batch_dir / filename
                
                # Download the file
                downloaded_path = self.download_audio_file(episode['media_url'], filepath)
                
                if downloaded_path:
                    episode['local_filepath'] = downloaded_path
                    episode['local_filename'] = filename
                    episode['download_status'] = 'success'
                    print(f"✓ Downloaded: {filename}")
                    
                    # Transcribe if enabled
                    if self.transcribe_audio and self.gemini_model:
                        transcript_path = self.transcribe_audio_file(filepath, episode)
                        if transcript_path:
                            episode['transcript_filepath'] = transcript_path
                            episode['transcription_status'] = 'success'
                        else:
                            episode['transcription_status'] = 'failed'
                    else:
                        episode['transcription_status'] = 'disabled'
                        
                else:
                    episode['download_status'] = 'failed'
                    episode['transcription_status'] = 'skipped'
                    print(f"✗ Failed: {filename}")
                    
            except Exception as e:
                episode['download_status'] = f'error: {str(e)}'
                episode['transcription_status'] = 'error'
                print(f"✗ Error downloading {episode['episode_title']}: {str(e)}")
            
            downloaded_episodes.append(episode)
            time.sleep(0.1)  # Small delay between downloads
        
        # Save batch CSV
        self.save_batch_csv(batch_dir, batch_number, downloaded_episodes)
        
        return downloaded_episodes
    
    def save_batch_csv(self, batch_dir, batch_number, episodes):
        """Save CSV file for a specific batch with only essential metadata"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"batch_{batch_number:03d}_episodes_{timestamp}.csv"
        csv_filepath = batch_dir / csv_filename
        
        # Define only the required fields
        required_fields = [
            'podcast_title',
            'episode_title', 
            'episode_url',
            'media_url'
        ]
        
        # Filter episodes to only those successfully downloaded
        successful_episodes = [ep for ep in episodes if ep.get('download_status') == 'success']
        
        if successful_episodes:
            with open(csv_filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=required_fields)
                writer.writeheader()
                
                for episode in successful_episodes:
                    # Extract only the required fields
                    row_data = {field: episode.get(field, '') for field in required_fields}
                    writer.writerow(row_data)
            
            print(f"📋 Batch CSV saved: {csv_filename} ({len(successful_episodes)} episodes)")
        else:
            print(f"⚠️  No successful downloads in batch {batch_number}, CSV not created")
        
        # Also create a batch summary file
        summary_file = batch_dir / f"batch_{batch_number:03d}_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            successful_transcriptions = len([ep for ep in episodes if ep.get('transcription_status') == 'success'])
            
            f.write(f"BATCH {batch_number} SUMMARY\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Total episodes processed: {len(episodes)}\n")
            f.write(f"Successful downloads: {len(successful_episodes)}\n")
            f.write(f"Failed downloads: {len(episodes) - len(successful_episodes)}\n")
            f.write(f"Successful transcriptions: {successful_transcriptions}\n")
            f.write(f"CSV file: {csv_filename}\n")
            f.write(f"MP3 files directory: {batch_dir}\n")
            f.write(f"Audio compression: {'Enabled' if self.compress_audio else 'Disabled'}\n")
            f.write(f"Transcription: {'Enabled' if self.transcribe_audio else 'Disabled'}\n")
            if self.compress_audio:
                f.write(f"Target bitrate: {self.target_bitrate}kbps\n")
            f.write("\n")
            
            if successful_episodes:
                f.write("SUCCESSFUL DOWNLOADS:\n")
                for episode in successful_episodes:
                    transcript_status = "✓" if episode.get('transcription_status') == 'success' else "✗"
                    f.write(f"- {episode['podcast_title']}: {episode['episode_title']} [T:{transcript_status}]\n")
    
    def create_content_analysis_prompt(self, batch_dir: Path, batch_number: int) -> str:
        """Create the content analysis prompt with batch-specific CSV data"""
        
        # Read the CSV file for this batch
        csv_files = list(batch_dir.glob("batch_*_episodes_*.csv"))
        if not csv_files:
            return None
            
        csv_file = csv_files[0]  # Get the latest CSV
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        # Your original prompt with the CSV data inserted
        prompt = f"""You are an expert financial content curator and writer with the explosive energy of Jim Cramer, the observational wit of Larry David, and the infectious enthusiasm of Steve Ballmer.

Your mission is to analyse investment and finance podcast episodes and extract the most brilliant, practical, and inspiring trading content for investors of all skill levels. The result will be published on InvestingDojo.co.uk - where investors train to become market masters.

**IMPORTANT DISCLAIMER**: Nothing you extract should be presented as financial advice. Everything is educational content, inspiration, and learning from experts. Always frame insights as "Here's what this expert shared..." or "This trader's approach was..." rather than prescriptive advice.

When you're scouring the transcripts, put yourself in the shoes of investors at different belt levels. What are their primary concerns and needs when it comes to building wealth, understanding markets, and becoming successful traders? Find associations in the transcriptions so we can share with our dojo members the best possible connected content that will help them level up from white belt to black belt mastery.

[... rest of the original prompt content ...]

The episodes in this batch have been extracted from the CSV file below, and their transcripts are available as separate text files in the same directory:

<csv>
{csv_content}
</csv>

Please analyse the transcript files for batch {batch_number:03d} and create the JSON output following this exact structure and style. Remember: we're building an investing education platform, not providing financial advice. Make it educational, exciting, and irresistible!
"""
        return prompt
    
    def save_podcast_list(self, list_name: str, rss_urls: List[str], description: str = ""):
        """Save a list of podcast RSS URLs"""
        list_file = self.lists_dir / f"{list_name}.json"
        
        list_data = {
            "name": list_name,
            "description": description,
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "count": len(rss_urls),
            "urls": rss_urls
        }
        
        with open(list_file, 'w', encoding='utf-8') as f:
            json.dump(list_data, f, indent=2)
        
        print(f"✓ Saved podcast list '{list_name}' with {len(rss_urls)} feeds")
    
    def load_podcast_list(self, list_name: str) -> List[str]:
        """Load a saved podcast list"""
        list_file = self.lists_dir / f"{list_name}.json"
        
        if not list_file.exists():
            print(f"✗ List '{list_name}' not found")
            return []
        
        with open(list_file, 'r', encoding='utf-8') as f:
            list_data = json.load(f)
        
        return list_data.get('urls', [])
    
    def get_available_lists(self) -> List[Dict]:
        """Get all available podcast lists"""
        lists = []
        for list_file in self.lists_dir.glob("*.json"):
            try:
                with open(list_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                lists.append({
                    'name': data.get('name', list_file.stem),
                    'description': data.get('description', ''),
                    'count': data.get('count', 0),
                    'updated': data.get('updated', '')
                })
            except:
                continue
        return lists
    
    def harvest_podcasts_by_recency(self, rss_urls: List[str], days_back: int):
        """Harvest podcasts by recency"""
        return self.harvest_podcasts(rss_urls, days_back=days_back)
    
    def harvest_single_podcast(self, rss_url: str, num_episodes: int = None):
        """Harvest episodes from a single podcast"""
        print(f"Harvesting from single podcast: {rss_url}")
        
        # Get all episodes (or specified number)
        episodes = self.process_podcast_feed(rss_url, num_episodes=num_episodes)
        
        if not episodes:
            print("No episodes found!")
            return []
        
        print(f"Found {len(episodes)} episodes")
        
        # Create batches and process
        batches = self.create_batches(episodes)
        all_downloaded_episodes = []
        
        for batch_info in batches:
            downloaded_batch = self.download_batch(batch_info)
            all_downloaded_episodes.extend(downloaded_batch)
            
            # Create content analysis prompt for this batch
            if self.transcribe_audio:
                batch_dir = self.create_batch_directory(batch_info['batch_number'])
                prompt = self.create_content_analysis_prompt(batch_dir, batch_info['batch_number'])
                
                if prompt:
                    prompt_file = batch_dir / f"batch_{batch_info['batch_number']:03d}_analysis_prompt.txt"
                    with open(prompt_file, 'w', encoding='utf-8') as f:
                        f.write(prompt)
                    print(f"📝 Content analysis prompt saved: {prompt_file.name}")
        
        # Create overall summary
        self.save_harvest_summary(all_downloaded_episodes, batches)
        
        return all_downloaded_episodes
    
    def harvest_podcasts(self, rss_urls, days_back=7):
        """Main method to harvest podcasts with batch processing"""
        all_episodes = []
        
        print(f"Starting harvest of {len(rss_urls)} podcast feeds...")
        print(f"Looking for episodes from the last {days_back} days")
        print(f"Will batch downloads into groups of {self.batch_size} episodes")
        print(f"Audio compression: {'Enabled' if self.compress_audio else 'Disabled'}")
        print(f"Transcription: {'Enabled' if self.transcribe_audio else 'Disabled'}")
        if self.compress_audio:
            print(f"Target bitrate: {self.target_bitrate}kbps (optimised for transcription)")
        
        # Process feeds to find recent episodes
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            feed_futures = {executor.submit(self.process_podcast_feed, url, days_back=days_back): url 
                          for url in rss_urls}
            
            for future in as_completed(feed_futures):
                episodes = future.result()
                all_episodes.extend(episodes)
                time.sleep(0.5)  # Be respectful to servers
        
        print(f"Found {len(all_episodes)} recent episodes")
        
        if not all_episodes:
            print("No recent episodes found!")
            return []
        
        # Create batches
        batches = self.create_batches(all_episodes)
        print(f"Created {len(batches)} batches for download")
        
        # Process each batch
        all_downloaded_episodes = []
        for batch_info in batches:
            downloaded_batch = self.download_batch(batch_info)
            all_downloaded_episodes.extend(downloaded_batch)
            
            # Create content analysis prompt for this batch
            if self.transcribe_audio:
                batch_dir = self.create_batch_directory(batch_info['batch_number'])
                prompt = self.create_content_analysis_prompt(batch_dir, batch_info['batch_number'])
                
                if prompt:
                    # Save the prompt for this batch
                    prompt_file = batch_dir / f"batch_{batch_info['batch_number']:03d}_analysis_prompt.txt"
                    with open(prompt_file, 'w', encoding='utf-8') as f:
                        f.write(prompt)
                    print(f"📝 Content analysis prompt saved: {prompt_file.name}")
        
        # Create overall summary
        self.save_harvest_summary(all_downloaded_episodes, batches)
        
        successful_downloads = len([ep for ep in all_downloaded_episodes 
                                  if ep.get('download_status') == 'success'])
        successful_transcriptions = len([ep for ep in all_downloaded_episodes 
                                       if ep.get('transcription_status') == 'success'])
        
        print(f"\n=== HARVEST COMPLETE ===")
        print(f"Total episodes found: {len(all_downloaded_episodes)}")
        print(f"Successfully downloaded: {successful_downloads}")
        print(f"Successfully transcribed: {successful_transcriptions}")
        print(f"Organised into {len(batches)} batches")
        print(f"Files saved to: {self.download_dir}")
        
        return all_downloaded_episodes
    
    def save_harvest_summary(self, all_episodes, batches):
        """Save overall harvest summary"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = self.download_dir / f"harvest_summary_{timestamp}.txt"
        
        successful_episodes = [ep for ep in all_episodes if ep.get('download_status') == 'success']
        successful_transcriptions = [ep for ep in all_episodes if ep.get('transcription_status') == 'success']
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"PODCAST HARVEST SUMMARY\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"="*50 + "\n\n")
            
            f.write(f"OVERALL STATISTICS:\n")
            f.write(f"Total episodes found: {len(all_episodes)}\n")
            f.write(f"Successfully downloaded: {len(successful_episodes)}\n")
            f.write(f"Successfully transcribed: {len(successful_transcriptions)}\n")
            f.write(f"Failed downloads: {len(all_episodes) - len(successful_episodes)}\n")
            f.write(f"Number of batches: {len(batches)}\n")
            f.write(f"Batch size: {self.batch_size}\n")
            f.write(f"Audio compression: {'Enabled' if self.compress_audio else 'Disabled'}\n")
            f.write(f"Transcription: {'Enabled' if self.transcribe_audio else 'Disabled'}\n")
            if self.compress_audio:
                f.write(f"Target bitrate: {self.target_bitrate}kbps\n")
            f.write("\n")
            
            f.write(f"BATCH BREAKDOWN:\n")
            for batch in batches:
                batch_successful = len([ep for ep in batch['episodes'] 
                                      if ep.get('download_status') == 'success'])
                batch_transcribed = len([ep for ep in batch['episodes'] 
                                       if ep.get('transcription_status') == 'success'])
                f.write(f"Batch {batch['batch_number']:03d}: {batch_successful}/{batch['total_episodes']} downloaded, {batch_transcribed} transcribed\n")
            
            f.write(f"\nBATCH DIRECTORIES:\n")
            for batch in batches:
                f.write(f"batch_{batch['batch_number']:03d}/ - MP3s + transcripts + analysis prompt\n")
        
        print(f"📋 Overall summary saved: {summary_file.name}")

# Your existing podcast URLs list remains the same
INVESTMENT_FINANCE_PODCAST_URLS = [
    # ... (keeping your original list)
    "https://feeds.megaphone.fm/the-investors-podcast",
    # ... rest of the URLs
]

# Parenting for dads podcast URLs
investing_dojo_urls = [
    "https://feeds.megaphone.fm/planetmoney",
"https://feeds.buzzsprout.com/1084430.rss",
"https://feeds.megaphone.fm/motleyfoolmoney",
"https://feeds.npr.org/510325/podcast.xml",
"https://rss.art19.com/money-for-the-rest-of-us",
"https://feeds.megaphone.fm/the-ramsey-show",
"https://feeds.simplecast.com/stacking-benjamins",
"https://feeds.simplecast.com/investing-for-beginners",
"https://feeds.simplecast.com/optimal-finance-daily",
"https://feeds.simplecast.com/choose-fi",
"https://feeds.simplecast.com/chit-chat-money",
"https://feeds.simplecast.com/girls-that-invest",
"https://feeds.simplecast.com/money-clinic",
"https://feeds.simplecast.com/martin-lewis-podcast",
"https://feeds.acast.com/public/shows/money-to-the-masses",
"https://feeds.acast.com/public/shows/meaningful-money",
"https://feeds.megaphone.fm/the-investors-podcast",
"https://feeds.simplecast.com/the-acquirers-podcast",
"https://feeds.simplecast.com/the-disciplined-investor",
"https://feeds.simplecast.com/yet-another-value-podcast",
"https://feeds.simplecast.com/the-compounders",
"https://feeds.simplecast.com/focused-compounding",
"https://feeds.simplecast.com/invest-like-the-best",
"https://feeds.simplecast.com/capital-allocators",
"https://feeds.simplecast.com/rule-breaker-investing",
"https://feeds.simplecast.com/joseph-carlson-show",
"https://feeds.simplecast.com/the-canadian-investor",
"https://feeds.simplecast.com/rational-reminder",
"https://valueandopportunity.libsyn.com/rss",
"https://valueandgrowthstocks.libsyn.com/rss",
"https://dividendgrowthinsights.libsyn.com/rss",
"https://feeds.simplecast.com/best-anchor-stocks",
"https://rss.acast.com/chat-with-traders",
"https://feeds.simplecast.com/top-traders-unplugged",
"https://feeds.simplecast.com/better-system-trader",
"https://feeds.simplecast.com/trading-nut",
"https://feeds.megaphone.fm/options-action-cnbc",
"https://feeds.simplecast.com/futures-radio-show",
"https://feeds.simplecast.com/oneoption",
"https://feeds.simplecast.com/how-to-trade-it",
"https://feeds.simplecast.com/confessions-market-maker",
"https://feeds.simplecast.com/consistent-profits",
"https://feeds.simplecast.com/convergent-trading",
"https://feeds.simplecast.com/speculators-podcast",
"https://feeds.simplecast.com/band-of-traders",
"https://feeds.simplecast.com/desire-to-trade",
"https://feeds.simplecast.com/art-of-trading",
"https://feeds.simplecast.com/words-of-rizdom",
"https://feeds.simplecast.com/mind-over-markets",
"https://feeds.simplecast.com/ic-your-trade",
"https://feeds.megaphone.fm/bloomberg-surveillance",
"https://rss.art19.com/masters-in-business",
"https://video-api.wsj.com/podcast/rss/wsj/your-money-matters",
"https://video-api.wsj.com/podcast/rss/wsj/the-journal",
"https://video-api.wsj.com/podcast/rss/wsj/whats-news",
"https://video-api.wsj.com/podcast/rss/wsj/minute-briefing",
"https://feeds.megaphone.fm/reuters-money-movers",
"https://feeds.megaphone.fm/cnbc-squawk-pod",
"https://feeds.megaphone.fm/marketwatch-money-report",
"https://feeds.megaphone.fm/marketwatch-podcast",
"https://rss.art19.com/steve-forbes-whats-ahead",
"https://rss.art19.com/forbes-daily-briefing",
"https://feeds.bloomberg.com/podcast/etf-report.xml",
"https://rss.art19.com/squawk-box-europe",
"https://rss.art19.com/futuresinfocus",
"https://video-api.barrons.com/podcast/rss/marketwatch/best-new-ideas-in-money",
"https://www.ft.com/behind-the-money?format=rss",
"https://feeds.simplecast.com/odd-lots",
"https://feeds.simplecast.com/the-indicator",
"https://feeds.simplecast.com/marketplace",
"https://feeds.simplecast.com/barrons-streetwise",
"https://feeds.simplecast.com/benzinga-premarket-prep",
"https://feeds.simplecast.com/real-vision-daily",
"https://feeds.simplecast.com/exchanges-goldman-sachs",
"https://feeds.megaphone.fm/halftime-report-cnbc",
"https://feeds.megaphone.fm/power-lunch-cnbc",
"https://feeds.megaphone.fm/closing-bell-cnbc",
"https://feeds.megaphone.fm/worldwide-exchange",
"https://feeds.megaphone.fm/mad-money-cramer",
"https://feeds.megaphone.fm/yahoo-finance-presents",
"https://rss.art19.com/biggerpockets-money-podcast",
"https://rss.art19.com/on-the-market",
"https://feeds.acast.com/public/shows/the-property-podcast",
"https://feeds.acast.com/public/shows/property-hub-podcast",
"https://feeds.acast.com/public/shows/uk-property-investment",
"https://feeds.megaphone.fm/bigger-pockets-podcast",
"https://feeds.captivate.fm/coin-stories/",
"https://unchainedpodcast.com/category/unchained/feed/",
"https://feeds.feedburner.com/etheruem",
"https://feeds.megaphone.fm/freakonomics-radio",
"https://rss.art19.com/the-tim-ferriss-show",
"https://feeds.megaphone.fm/how-i-built-this",
"https://feeds.simplecast.com/animal-spirits",
"https://feeds.simplecast.com/the-compound",
"https://feeds.simplecast.com/acquired",
"https://feeds.simplecast.com/business-breakdowns",
"https://feeds.simplecast.com/unhedged",
"https://feeds.simplecast.com/outthinking-investor",
"https://feeds.simplecast.com/multiple-perspectives",
"https://feeds.simplecast.com/investing-in-integrity",
"https://rss.art19.com/the-bid",
"https://feeds.acast.com/public/shows/the-investors-podcast-uk"
]

def show_menu():
    """Display the main menu"""
    print("\n" + "="*60)
    print("🎙️  PODCAST HARVESTER - MAIN MENU")
    print("="*60)
    print("1. 📅 Download by recency (last N days)")
    print("2. 🎧 Download single podcast (last N episodes)")
    print("3. 📋 Download from custom RSS list")
    print("4. 📚 Download from saved list")
    print("5. 💾 Manage podcast lists")
    print("6. ⚙️  Configure settings")
    print("7. ❌ Exit")
    print("="*60)

def get_user_choice(prompt: str, valid_choices: List[str]) -> str:
    """Get validated user input"""
    while True:
        choice = input(prompt).strip()
        if choice in valid_choices:
            return choice
        print(f"Invalid choice. Please enter one of: {', '.join(valid_choices)}")

def get_recency_settings():
    """Get settings for downloading by recency"""
    print("\n📅 DOWNLOAD BY RECENCY")
    print("-" * 40)
    
    days = input("How many days back to search? (default: 7): ").strip()
    days_back = int(days) if days.isdigit() else 7
    
    print("\nSelect podcast list:")
    print("1. Trading & Investing podcasts")
    print("2. Parenting for Dads podcasts")
    print("3. Load saved list")
    
    list_choice = get_user_choice("Enter choice (1-3): ", ['1', '2', '3'])
    
    if list_choice == '1':
        return days_back, INVESTMENT_FINANCE_PODCAST_URLS
    elif list_choice == '2':
        return days_back, PARENTING_DADS_PODCAST_URLS
    else:
        # Load saved list
        harvester = PodcastHarvester()
        lists = harvester.get_available_lists()
        if not lists:
            print("No saved lists found!")
            return None, None
        
        print("\nAvailable lists:")
        for i, lst in enumerate(lists, 1):
            print(f"{i}. {lst['name']} ({lst['count']} feeds) - {lst['description']}")
        
        list_num = input(f"Select list (1-{len(lists)}): ").strip()
        if list_num.isdigit() and 1 <= int(list_num) <= len(lists):
            selected_list = lists[int(list_num) - 1]
            urls = harvester.load_podcast_list(selected_list['name'])
            return days_back, urls
        
        return None, None

def get_single_podcast_settings():
    """Get settings for downloading single podcast"""
    print("\n🎧 DOWNLOAD SINGLE PODCAST")
    print("-" * 40)
    
    rss_url = input("Enter podcast RSS URL: ").strip()
    if not rss_url:
        return None, None
    
    print("\nHow many episodes to download?")
    print("1. Last 10 episodes")
    print("2. Last 25 episodes")
    print("3. Last 50 episodes")
    print("4. Custom number")
    print("5. All episodes")
    
    choice = get_user_choice("Enter choice (1-5): ", ['1', '2', '3', '4', '5'])
    
    if choice == '1':
        num_episodes = 10
    elif choice == '2':
        num_episodes = 25
    elif choice == '3':
        num_episodes = 50
    elif choice == '4':
        custom = input("Enter number of episodes: ").strip()
        num_episodes = int(custom) if custom.isdigit() else 10
    else:
        num_episodes = None  # All episodes
    
    return rss_url, num_episodes

def get_custom_list_settings():
    """Get custom list of RSS URLs"""
    print("\n📋 CUSTOM RSS LIST")
    print("-" * 40)
    print("Paste RSS URLs (one per line), then press Enter twice when done:")
    
    urls = []
    while True:
        line = input().strip()
        if not line:
            if urls:  # If we have URLs and user pressed enter twice
                break
        elif line.startswith('http'):
            urls.append(line)
    
    if urls:
        save_choice = input(f"\nFound {len(urls)} URLs. Save this list for future use? (y/n): ").lower()
        if save_choice == 'y':
            list_name = input("Enter list name: ").strip()
            description = input("Enter description (optional): ").strip()
            if list_name:
                harvester = PodcastHarvester()
                harvester.save_podcast_list(list_name, urls, description)
    
    return urls

def manage_podcast_lists():
    """Manage saved podcast lists"""
    harvester = PodcastHarvester()
    
    while True:
        print("\n💾 MANAGE PODCAST LISTS")
        print("-" * 40)
        print("1. View saved lists")
        print("2. Create new list")
        print("3. Edit existing list")
        print("4. Delete list")
        print("5. Back to main menu")
        
        choice = get_user_choice("Enter choice (1-5): ", ['1', '2', '3', '4', '5'])
        
        if choice == '5':
            break
        
        if choice == '1':
            lists = harvester.get_available_lists()
            if not lists:
                print("No saved lists found!")
            else:
                print("\nSaved lists:")
                for lst in lists:
                    print(f"- {lst['name']} ({lst['count']} feeds)")
                    if lst['description']:
                        print(f"  Description: {lst['description']}")
                    print(f"  Updated: {lst['updated']}")
        
        elif choice == '2':
            print("\nCreate new list from:")
            print("1. Trading & Investing defaults")
            print("2. Parenting for Dads defaults")
            print("3. Empty list")
            
            source = get_user_choice("Enter choice (1-3): ", ['1', '2', '3'])
            
            list_name = input("Enter list name: ").strip()
            description = input("Enter description (optional): ").strip()
            
            if list_name:
                if source == '1':
                    harvester.save_podcast_list(list_name, INVESTMENT_FINANCE_PODCAST_URLS, description)
                elif source == '2':
                    harvester.save_podcast_list(list_name, PARENTING_DADS_PODCAST_URLS, description)
                else:
                    harvester.save_podcast_list(list_name, [], description)
                print(f"✓ List '{list_name}' created!")

def configure_settings(harvester):
    """Configure harvester settings"""
    print("\n⚙️  CONFIGURE SETTINGS")
    print("-" * 40)
    print(f"Current settings:")
    print(f"- Batch size: {harvester.batch_size}")
    print(f"- Max workers: {harvester.max_workers}")
    print(f"- Audio compression: {'Enabled' if harvester.compress_audio else 'Disabled'}")
    print(f"- Target bitrate: {harvester.target_bitrate}kbps")
    print(f"- Transcription: {'Enabled' if harvester.transcribe_audio else 'Disabled'}")
    
    print("\nWhat would you like to change?")
    print("1. Batch size")
    print("2. Max workers")
    print("3. Toggle audio compression")
    print("4. Change target bitrate")
    print("5. Toggle transcription")
    print("6. Back to main menu")
    
    choice = get_user_choice("Enter choice (1-6): ", ['1', '2', '3', '4', '5', '6'])
    
    if choice == '1':
        new_size = input(f"Enter new batch size (current: {harvester.batch_size}): ").strip()
        if new_size.isdigit():
            harvester.batch_size = int(new_size)
            print(f"✓ Batch size set to {harvester.batch_size}")
    
    elif choice == '2':
        new_workers = input(f"Enter max workers (current: {harvester.max_workers}): ").strip()
        if new_workers.isdigit():
            harvester.max_workers = int(new_workers)
            print(f"✓ Max workers set to {harvester.max_workers}")
    
    elif choice == '3':
        harvester.compress_audio = not harvester.compress_audio
        print(f"✓ Audio compression {'enabled' if harvester.compress_audio else 'disabled'}")
    
    elif choice == '4':
        new_bitrate = input(f"Enter target bitrate in kbps (current: {harvester.target_bitrate}): ").strip()
        if new_bitrate.isdigit():
            harvester.target_bitrate = int(new_bitrate)
            print(f"✓ Target bitrate set to {harvester.target_bitrate}kbps")
    
    elif choice == '5':
        harvester.transcribe_audio = not harvester.transcribe_audio
        print(f"✓ Transcription {'enabled' if harvester.transcribe_audio else 'disabled'}")

def main():
    """Main execution function with interactive menu"""
    # Initialize with default settings
    gemini_api_key = "AIzaSyBwwqspks4SlM8ZWbPie-vMFbvDD_-ysG8"
    
    # Initialize the harvester
    harvester = PodcastHarvester(
        download_dir="podcast_downloads",
        max_workers=3,
        batch_size=10,
        compress_audio=True,
        target_bitrate=32,
        transcribe_audio=True,
        gemini_api_key=gemini_api_key
    )
    
    # Initialize default lists if they don't exist
    if not harvester.get_available_lists():
        print("Creating default podcast lists...")
        harvester.save_podcast_list(
            "trading_investing", 
            INVESTMENT_FINANCE_PODCAST_URLS, 
            "Trading and investment podcasts"
        )
        harvester.save_podcast_list(
            "parenting_dads", 
            PARENTING_DADS_PODCAST_URLS, 
            "Parenting podcasts for dads"
        )
    
    print("🎙️  Welcome to Podcast Harvester!")
    print("This tool downloads and transcribes podcast episodes.")
    
    while True:
        show_menu()
        choice = get_user_choice("Enter your choice (1-7): ", ['1', '2', '3', '4', '5', '6', '7'])
        
        if choice == '7':
            print("\n👋 Goodbye!")
            break
        
        elif choice == '1':
            # Download by recency
            days_back, urls = get_recency_settings()
            if urls:
                harvester.harvest_podcasts_by_recency(urls, days_back)
        
        elif choice == '2':
            # Download single podcast
            rss_url, num_episodes = get_single_podcast_settings()
            if rss_url:
                harvester.harvest_single_podcast(rss_url, num_episodes)
        
        elif choice == '3':
            # Custom RSS list
            urls = get_custom_list_settings()
            if urls:
                days = input("How many days back to search? (default: all): ").strip()
                if days.isdigit():
                    harvester.harvest_podcasts_by_recency(urls, int(days))
                else:
                    harvester.harvest_podcasts_by_recency(urls, 365)  # All episodes from last year
        
        elif choice == '4':
            # Download from saved list
            lists = harvester.get_available_lists()
            if not lists:
                print("No saved lists found!")
                continue
            
            print("\nAvailable lists:")
            for i, lst in enumerate(lists, 1):
                print(f"{i}. {lst['name']} ({lst['count']} feeds) - {lst['description']}")
            
            list_num = input(f"Select list (1-{len(lists)}): ").strip()
            if list_num.isdigit() and 1 <= int(list_num) <= len(lists):
                selected_list = lists[int(list_num) - 1]
                urls = harvester.load_podcast_list(selected_list['name'])
                
                days = input("How many days back to search? (default: 7): ").strip()
                days_back = int(days) if days.isdigit() else 7
                
                harvester.harvest_podcasts_by_recency(urls, days_back)
        
        elif choice == '5':
            # Manage lists
            manage_podcast_lists()
        
        elif choice == '6':
            # Configure settings
            configure_settings(harvester)
        
        # After any operation, ask if user wants to continue
        if choice in ['1', '2', '3', '4']:
            cont = input("\nPress Enter to return to main menu...") 

if __name__ == "__main__":
    # Install required dependencies reminder
    print("Note: This script requires additional packages:")
    print("pip install feedparser requests pydub google-generativeai")
    print("You may also need ffmpeg installed on your system.\n")
    
    main()
