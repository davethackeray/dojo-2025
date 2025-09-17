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
from typing import Optional, Dict, Any
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
            print(f"⏱️  Rate limit reached. Waiting {wait_time:.1f} seconds...")
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
            print(f"  🔄 Compressing {input_path.name}...")
            
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
                
            print(f"  🎤 Transcribing {audio_file_path.name}...")
            
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
    
    def process_podcast_feed(self, rss_url, podcast_name=None):
        """Process a single podcast RSS feed"""
        episodes_data = []
        
        try:
            print(f"Processing: {rss_url}")
            feed = feedparser.parse(rss_url)
            
            if not hasattr(feed, 'entries'):
                print(f"No entries found in feed: {rss_url}")
                return episodes_data
            
            for entry in feed.entries:
                # Check if episode is recent
                if not self.is_recent_episode(entry.get('published_parsed')):
                    continue
                
                # Extract audio URL
                audio_url = self.extract_audio_url(entry)
                if not audio_url:
                    continue
                
                # Extract basic metadata
                episode_data = self.extract_basic_metadata(entry, feed, rss_url)
                episodes_data.append(episode_data)
                
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
            
            print(f"📄 Batch CSV saved: {csv_filename} ({len(successful_episodes)} episodes)")
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

You write using British English spelling, and in sentence case. For example, titles look like this:

The brilliant 5-minute chart pattern that changed everything

NOT:

The Brilliant 5-Minute Chart Pattern That Changed Everything

Remember when you write your genius content that we're specifically empathising with investors at all levels - from the complete novice taking their first tentative steps into the markets, to the seasoned pro looking for that edge. Tailor your interpretation of the incredibly helpful and inspiring stories you find to help people level up their investing game!

## YOUR MISSION
The ultimate goal is to create content so engaging and valuable that readers will:
1. **Sign up to the InvestingDojo community** for more insights
2. **Download our app** to track their learning journey  
3. **Listen to our podcast** for regular market wisdom
4. **Progress through the belt system** from white to black belt

## YOUR TASK
Analyse each MP3 file thoroughly and extract:
1. **Market War Stories** - dramatic, funny, or eye-opening trading moments
2. **Winning Strategies & Techniques** - practical approaches that actually work
3. **Expert Insights** - professional guidance that's accessible and actionable
4. **Universal Market Wisdom** - timeless investing truths that transcend market cycles

## CONTENT CRITERIA
Extract content that is:
- ✅ Genuinely educational and actionable
- ✅ Emotionally resonant (inspiring, amusing, or enlightening)
- ✅ Applicable to real-world investing situations
- ✅ Fresh perspective on common market challenges
- ✅ Evidence-based when possible
- ✅ Clearly presented as educational, not advice
- ❌ Overly academic or theoretical
- ❌ Presented as guaranteed financial advice
- ❌ Outdated or potentially harmful strategies
- ❌ Get-rich-quick schemes or unrealistic promises

## TAXONOMY & CATEGORIES

### Belt Levels (Skill Levels):
- "white-belt" (complete beginner - never invested before)
- "yellow-belt" (basic knowledge - knows what stocks are)
- "orange-belt" (some experience - made a few trades)
- "green-belt" (intermediate - understands fundamentals)
- "blue-belt" (advanced intermediate - using multiple strategies)
- "brown-belt" (advanced - sophisticated portfolio management)
- "black-belt" (expert - advanced techniques and risk management)
- "all-levels" (universal wisdom that applies to everyone)

### Investment Categories:
- "stock-analysis"
- "options-trading"
- "cryptocurrency"
- "real-estate-investing"
- "portfolio-management"
- "risk-management"
- "market-psychology"
- "technical-analysis"
- "fundamental-analysis"
- "dividend-investing"
- "value-investing"
- "growth-investing"
- "day-trading"
- "swing-trading"
- "long-term-investing"
- "retirement-planning"
- "tax-strategies"
- "alternative-investments"
- "international-markets"
- "economic-indicators"
- "market-timing"
- "passive-investing"

### Content Types:
- "market-war-story"
- "practical-strategy"
- "expert-technique"
- "trading-hack"
- "research-insight"
- "problem-solution"
- "epic-fail-lesson"
- "aha-moment"
- "contrarian-view"
- "market-prediction"

### Urgency/Seasonality:
- "timeless"
- "trending"
- "seasonal"
- "urgent"
- "market-cycle-dependent"

## TONE OF VOICE
Write everything in British English with a tone that combines:
- **Cramer's explosive energy**: "This is MASSIVE!" "Are you kidding me?!" "This changes everything!"
- **Larry's observational scepticism**: "Because apparently..." "Which, let's be honest..." "Sure, that sounds reasonable..."
- **Ballmer's infectious enthusiasm**: "This is HUGE!" "I'm telling you..." "This is going to be INCREDIBLE!"
- Accessible and conversational
- Genuinely excited about markets without being reckless
- Educational but never boring

## JSON OUTPUT STRUCTURE
For each piece of extracted content, create this exact JSON structure:

{{
"newsletter_content": [
{{
"id": "unique_identifier_string",
"title": "Compelling headline in British English that makes investors want to read",
"summary": "2-3 sentence summary with personality - think Cramer meets Larry meets Ballmer",
"full_content": "Complete story/strategy/insight - engaging, practical, British spelling throughout",
"content_type": "market-war-story|practical-strategy|expert-technique|etc",
"belt_levels": ["array", "of", "relevant", "skill", "levels"],
"categories": ["array", "of", "relevant", "investment", "categories"],
"tags": ["specific", "searchable", "keywords"],
"urgency": "timeless|trending|seasonal|urgent|market-cycle-dependent",
"engagement_score": 1-10,
"practical_score": 1-10,
"universal_appeal": 1-10,
"educational_value": 1-10,
"source": {{
"podcast_title": "Exact podcast name",
"episode_title": "Exact episode title", 
"episode_url": "Direct link to episode page",
"media_url": "Direct MP3/audio file URL",
"timestamp": "HH:MM:SS where content appears",
"host_name": "Podcast host name(s)"
}},
"related_topics": ["array", "of", "connected", "investment", "subjects"],
"actionable_takeaways": ["specific", "things", "investors", "can", "research", "or", "consider"],
"quote_highlight": "Most memorable quote from the content (if applicable)",
"newsletter_priority": 1-5,
"app_featured": true|false,
"newsletter_featured": true|false,
"email_subject_line": "Irresistible subject line for this content",
"social_media_snippet": "Shareable 280-character version",
"search_keywords": ["array", "of", "terms", "investors", "would", "search"],
"difficulty_level": "quick-win|moderate-effort|long-term-strategy",
"time_required": "5 minutes|weekend research|ongoing monitoring",
"resources_needed": ["any", "specific", "tools", "or", "platforms"],
"risk_level": "low|medium|high|very-high",
"financial_advice_disclaimer": true,
"fact_check_required": true|false,
"review_needed": true|false,
"dojo_community_hook": "Call-to-action text encouraging community sign-up",
"app_download_hook": "Call-to-action text encouraging app download",
"podcast_listen_hook": "Call-to-action text encouraging podcast listening"
}}
],
"episode_summary": {{
"total_items_extracted": "number",
"quality_score": "1-10",
"standout_moments": ["brief", "descriptions", "of", "best", "content"],
"overall_theme": "main investment topic/theme of episode",
"target_belt_levels": ["primary", "skill", "levels", "this", "episode", "serves"],
"market_relevance": "how current/relevant this content is to today's markets"
}}
}}

## SPECIFIC INSTRUCTIONS

1. **Extract 5-10 pieces of content per episode** (quality over quantity)
2. **Write headlines that make investors want to read more**: "The Genius 2% Rule That Saved This Trader's Portfolio" not "Risk Management Tips"
3. **Include specific, actionable details**: exact techniques, specific tools mentioned, step-by-step approaches
4. **Balance entertainment with education**: investors need both inspiration and practical knowledge
5. **Use proper British spelling throughout**: realise, colour, behaviour, centre, organised, etc.
6. **Make it scannable**: use bullet points, numbered lists, and clear structure when appropriate
7. **Include context**: briefly explain why this strategy works or why this story matters
8. **Always include disclaimers**: frame as educational content, not financial advice
9. **Add community hooks**: encourage sign-ups, app downloads, and podcast listening
10. **Belt-level appropriate**: match content complexity to skill level
11. **Output token limit** is 65536 so make sure to finish your JSON output before hitting that limit!

## CONTENT EXAMPLES

**Good headline**: "The Brilliant 'Pizza Slice' Portfolio Strategy That Crushed the Market"
**Poor headline**: "Diversification Tips"

**Good summary**: "Sometimes the most obvious investment strategies are hiding in plain sight. This fund manager's pizza-inspired approach to portfolio allocation is rather genius, actually - and it consistently outperformed the S&P 500 for three straight years."

**Good actionable takeaway**: "Research the 'pizza slice' method: divide your portfolio into 8 equal segments, with each slice representing a different asset class or sector, rebalancing quarterly."

**Good community hook**: "Want to master advanced portfolio strategies like this? Join thousands of investors in our InvestingDojo community where we break down complex techniques into simple, actionable steps."

**Good app hook**: "Track your portfolio allocation progress and get personalised belt-level recommendations in our free InvestingDojo app."

**Good podcast hook**: "Hear more market-beating strategies like this on our weekly InvestingDojo podcast - subscribe wherever you get your podcasts."

## FINAL REMINDERS
- Every piece of content should make an investor think "I need to research this" or "This could change my investing approach"
- Include both quick wins and deeper strategies
- Balance different content types within each episode analysis
- Ensure all source attribution is complete and accurate
- Use British English spelling consistently throughout
- Write with genuine market enthusiasm but avoid being reckless or overpromising
- Always frame as educational content, never as financial advice
- Include clear calls-to-action for community, app, and podcast

## QUALITY FILTERS:
- Only extract content with engagement_score ≥ 6
- Prioritise content with high educational_value (7+)
- Flag anything potentially controversial with "review_needed": true
- Include "fact_check_required": true for any specific market claims
- Always set "financial_advice_disclaimer": true
- Mark high-risk strategies appropriately

## BELT-LEVEL CONTENT GUIDELINES:

**White/Yellow Belt**: Focus on basic concepts, simple strategies, foundational knowledge
**Orange/Green Belt**: Intermediate strategies, portfolio building, risk management basics  
**Blue/Brown Belt**: Advanced techniques, complex analysis, sophisticated strategies
**Black Belt**: Expert-level insights, institutional strategies, advanced risk management
**All Levels**: Universal wisdom, market psychology, timeless investing principles

The episodes in this batch have been extracted from the CSV file below, and their transcripts are available as separate text files in the same directory:

<csv>
{csv_content}
</csv>

Please analyse the transcript files for batch {batch_number:03d} and create the JSON output following this exact structure and style. Remember: we're building an investing education platform, not providing financial advice. Make it educational, exciting, and irresistible!
"""
        return prompt
    
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
            feed_futures = {executor.submit(self.process_podcast_feed, url): url 
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
        
        print(f"📄 Overall summary saved: {summary_file.name}")

# Your existing podcast URLs list...
INVESTMENT_FINANCE_PODCAST_URLS = [
    # [Previous list remains the same - truncated for brevity]
    "https://feeds.megaphone.fm/the-investors-podcast",
"https://feeds.buzzsprout.com/1084430.rss",
"https://rss.acast.com/chat-with-traders",
"https://feeds.captivate.fm/millennial-investing/",
"https://feeds.simplecast.com/tOjNXec5",
"https://feeds.megaphone.fm/motleyfoolmoney",
"https://feeds.npr.org/510289/podcast.xml",
"https://feeds.megaphone.fm/planetmoney",
"https://rss.art19.com/masters-in-business",
"https://feeds.megaphone.fm/freakonomics-radio",
"https://feeds.npr.org/510325/podcast.xml",
"https://feeds.simplecast.com/szW8tJ16",
"https://feeds.simplecast.com/tc4zxWgX",
"https://feeds.simplecast.com/qltQrd_8",
"https://feeds.simplecast.com/Nh1wIaXT",
"https://feeds.simplecast.com/_qvRgwME",
"https://feeds.simplecast.com/GcylmXl7",
"https://feeds.simplecast.com/Bt3ITxGl",
"https://feeds.simplecast.com/_mQMEG_J",
"https://feeds.simplecast.com/TkQfZXMD",
"https://feeds.simplecast.com/CqxTohm7",
"https://rss.art19.com/steve-forbes-whats-ahead",
"https://rss.art19.com/forbes-daily-briefing",
"https://rss.art19.com/futuresinfocus",
"https://rss.art19.com/squawk-box-europe",
"https://feeds.megaphone.fm/wsj-money",
"https://feeds.megaphone.fm/bloomberg-surveillance",
"https://feeds.bloomberg.com/podcast/etf-report.xml",
"https://feeds.megaphone.fm/reuters-money-movers",
"https://feeds.megaphone.fm/cnbc-squawk-pod",
"https://feeds.megaphone.fm/marketwatch-money-report",
"https://feeds.megaphone.fm/marketwatch-podcast",
"https://video-api.wsj.com/podcast/rss/wsj/minute-briefing",
"https://video-api.wsj.com/podcast/rss/wsj/whats-news",
"https://video-api.wsj.com/podcast/rss/wsj/your-money-matters",
"https://video-api.wsj.com/podcast/rss/wsj/the-journal",
"https://video-api.barrons.com/podcast/rss/marketwatch/best-new-ideas-in-money",
"https://feeds.simplecast.com/Q7fb3j2T",
"https://feeds.megaphone.fm/FOXM1510466999",
"https://feeds.megaphone.fm/FOXM2611238522",
"https://www.ft.com/behind-the-money?format=rss",
"https://www.ft.com/money-clinic-with-claer-barrett?format=rss",
"https://feeds.libsyn.com/84049/rss",
"https://feeds.libsyn.com/102774/rss",
"https://feeds.libsyn.com/115914/rss",
"https://feeds.libsyn.com/88745/rss",
"https://feeds.libsyn.com/161936/rss",
"https://feeds.libsyn.com/100426/rss",
"https://feeds.libsyn.com/304496/rss",
"https://rss.art19.com/the-bid",
"https://rss.art19.com/biggerpockets-money-podcast",
"https://rss.art19.com/on-the-market",
"https://feeds.simplecast.com/YEK6OY3e",
"https://feeds.simplecast.com/wsepistF",
"https://feeds.libsyn.com/85372/rss",
"https://feeds.buzzsprout.com/552559.rss",
"https://rss.art19.com/money-for-the-rest-of-us",
"https://feeds.blubrry.com/feeds/schiffradio.xml",
"https://yourmoneysworth.libsyn.com/rss",
"https://feeds.buzzsprout.com/273750.rss",
"https://feeds.libsyn.com/226312/rss",
"https://millionaireinvests.libsyn.com/rss",
"https://valueandopportunity.libsyn.com/rss",
"https://feeds.buzzsprout.com/1428712.rss",
"https://feeds.buzzsprout.com/465842.rss",
"https://feeds.libsyn.com/246129/rss",
"https://valueandgrowthstocks.libsyn.com/rss",
"https://feeds.buzzsprout.com/947796.rss",
"https://feeds.buzzsprout.com/1305510.rss",
"https://feeds.libsyn.com/65627/rss",
"https://feeds.libsyn.com/218334/rss",
"https://feeds.buzzsprout.com/267478.rss",
"https://feeds.libsyn.com/191537/rss",
"https://feeds.buzzsprout.com/378686.rss",
"https://feeds.buzzsprout.com/1263823.rss",
"https://feeds.buzzsprout.com/340783.rss",
"https://feeds.captivate.fm/coin-stories/",
"https://rss.art19.com/the-tim-ferriss-show",
"https://feeds.megaphone.fm/how-i-built-this",
"https://feeds.megaphone.fm/theentrepreneurship",
"https://feeds.megaphone.fm/the-ramsey-show",
"https://feeds.buzzsprout.com/213793.rss",
"https://feeds.libsyn.com/186595/rss",
"https://feeds.libsyn.com/219205/rss",
"https://feeds.buzzsprout.com/2289984.rss",
"https://feeds.libsyn.com/138831/rss",
"https://feeds.libsyn.com/171926/rss",
"https://feeds.libsyn.com/204588/rss",
"https://feeds.buzzsprout.com/1444927.rss",
"https://feeds.buzzsprout.com/1290932.rss",
"https://feeds.buzzsprout.com/1497632.rss",
"https://feeds.buzzsprout.com/1348435.rss",
"https://unchainedpodcast.com/category/unchained/feed/",
"https://feeds.feedburner.com/etheruem",
"https://feeds.libsyn.com/75720/rss",
"https://feeds.buzzsprout.com/213786.rss",
"https://feeds.libsyn.com/63966/rss",
"https://feeds.libsyn.com/168690/rss",
"https://feeds.libsyn.com/218031/rss",
"https://feeds.libsyn.com/80684/rss",
"https://feeds.libsyn.com/142738/rss",
"https://feeds.libsyn.com/208059/rss",
"https://feeds.libsyn.com/191598/rss",
"https://feeds.buzzsprout.com/213789.rss",
"https://feeds.libsyn.com/218012/rss",
"https://tradingnut.libsyn.com/rss",
"https://feeds.libsyn.com/218043/rss",
"https://feeds.libsyn.com/200588/rss",
"https://feeds.libsyn.com/179521/rss",
"https://feeds.libsyn.com/201588/rss",
"https://dividendgrowthinsights.libsyn.com/rss",
"https://feeds.acast.com/public/shows/money-to-the-masses",
"https://feeds.acast.com/public/shows/meaningful-money",
"https://feeds.acast.com/public/shows/the-investors-podcast-uk",
"https://feeds.acast.com/public/shows/share-radio-evening-show",
"https://feeds.acast.com/public/shows/citywire-new-model-adviser",
"https://feeds.acast.com/public/shows/the-property-podcast",
"https://feeds.acast.com/public/shows/property-hub-podcast",
"https://feeds.acast.com/public/shows/uk-property-investment",
"https://feeds.acast.com/public/shows/money-matters-podcast",
"https://feeds.acast.com/public/shows/pension-pod",
"https://feeds.simplecast.com/outthinking-investor",
"https://feeds.simplecast.com/unhedged",
"https://feeds.simplecast.com/animal-spirits",
"https://feeds.simplecast.com/odd-lots",
"https://feeds.simplecast.com/acquired",
"https://feeds.simplecast.com/business-breakdowns",
"https://feeds.simplecast.com/invest-like-the-best",
"https://feeds.simplecast.com/capital-ideas-investing",
"https://feeds.simplecast.com/capital-allocators",
"https://feeds.simplecast.com/the-compounders",
"https://feeds.simplecast.com/yet-another-value-podcast",
"https://feeds.simplecast.com/the-canadian-investor",
"https://feeds.simplecast.com/barrons-streetwise",
"https://feeds.simplecast.com/rational-reminder",
"https://feeds.simplecast.com/benzinga-premarket-prep",
"https://feeds.simplecast.com/mind-over-markets",
"https://feeds.simplecast.com/futures-radio-show",
"https://feeds.simplecast.com/trading-nut",
"https://feeds.simplecast.com/oneoption",
"https://feeds.simplecast.com/better-system-trader",
"https://feeds.simplecast.com/the-compound",
"https://feeds.simplecast.com/joseph-carlson-show",
"https://feeds.simplecast.com/top-traders-unplugged",
"https://feeds.simplecast.com/we-study-billionaires",
"https://feeds.simplecast.com/marketplace",
"https://feeds.simplecast.com/rule-breaker-investing",
"https://feeds.simplecast.com/chit-chat-money",
"https://feeds.simplecast.com/stacking-benjamins",
"https://feeds.simplecast.com/investing-for-beginners",
"https://feeds.simplecast.com/the-best-one-yet",
"https://feeds.simplecast.com/focused-compounding",
"https://feeds.simplecast.com/the-acquirers-podcast",
"https://feeds.simplecast.com/the-disciplined-investor",
"https://feeds.simplecast.com/optimal-finance-daily",
"https://feeds.simplecast.com/choose-fi",
"https://feeds.simplecast.com/inside-the-strategy-room",
"https://feeds.simplecast.com/the-tech-ma-podcast",
"https://feeds.simplecast.com/count-me-in",
"https://feeds.simplecast.com/strategic-financial-leadership",
"https://feeds.simplecast.com/the-better-finance-podcast",
"https://feeds.simplecast.com/global-market-insights",
"https://feeds.simplecast.com/ic-your-trade",
"https://feeds.simplecast.com/the-indicator",
"https://feeds.simplecast.com/the-money-movement",
"https://feeds.simplecast.com/smarter-business-finance",
"https://feeds.simplecast.com/ma-science",
"https://feeds.simplecast.com/dont-bank-on-it",
"https://feeds.simplecast.com/leaders-modern-finance",
"https://feeds.simplecast.com/cfo-yeah",
"https://feeds.simplecast.com/exchanges-goldman-sachs",
"https://feeds.simplecast.com/real-vision-daily",
"https://feeds.simplecast.com/behind-the-screens",
"https://feeds.simplecast.com/convergent-trading",
"https://feeds.simplecast.com/how-to-trade-it",
"https://feeds.simplecast.com/confessions-market-maker",
"https://feeds.simplecast.com/consistent-profits",
"https://feeds.simplecast.com/speculators-podcast",
"https://feeds.simplecast.com/band-of-traders",
"https://feeds.simplecast.com/desire-to-trade",
"https://feeds.simplecast.com/art-of-trading",
"https://feeds.simplecast.com/words-of-rizdom",
"https://feeds.simplecast.com/girls-that-invest",
"https://feeds.simplecast.com/money-clinic",
"https://feeds.simplecast.com/martin-lewis-podcast",
"https://feeds.simplecast.com/a-book-with-legs",
"https://feeds.simplecast.com/digest-invest-etoro",
"https://feeds.simplecast.com/multiple-perspectives",
"https://feeds.simplecast.com/investing-in-integrity",
"https://feeds.simplecast.com/best-anchor-stocks",
"https://feeds.buzzsprout.com/1234567.rss",
"https://feeds.buzzsprout.com/2345678.rss",
"https://feeds.buzzsprout.com/3456789.rss",
"https://feeds.buzzsprout.com/4567890.rss",
"https://feeds.buzzsprout.com/5678901.rss",
"https://feeds.libsyn.com/123456/rss",
"https://feeds.libsyn.com/234567/rss",
"https://feeds.libsyn.com/345678/rss",
"https://feeds.libsyn.com/456789/rss",
"https://feeds.libsyn.com/567890/rss",
"https://feeds.libsyn.com/678901/rss",
"https://feeds.libsyn.com/789012/rss",
"https://feeds.libsyn.com/890123/rss",
"https://feeds.libsyn.com/901234/rss",
"https://feeds.libsyn.com/012345/rss",
"https://feeds.megaphone.fm/investing-insights",
"https://feeds.megaphone.fm/trillions-podcast",
"https://feeds.megaphone.fm/long-view-morningstar", 
"https://feeds.megaphone.fm/bogleheads-investing",
"https://feeds.megaphone.fm/investtalk-show",
"https://feeds.megaphone.fm/clark-howard-podcast",
"https://feeds.megaphone.fm/rich-dad-radio",
"https://feeds.megaphone.fm/so-money-podcast",
"https://feeds.megaphone.fm/bigger-pockets-podcast",
"https://feeds.megaphone.fm/disciplined-investor",
"https://feeds.megaphone.fm/options-action-cnbc",
"https://feeds.megaphone.fm/halftime-report-cnbc",
"https://feeds.megaphone.fm/exchange-cnbc",
"https://feeds.megaphone.fm/worldwide-exchange",
"https://feeds.megaphone.fm/closing-bell-cnbc",
"https://feeds.megaphone.fm/power-lunch-cnbc",
"https://feeds.megaphone.fm/mad-money-cramer",
"https://feeds.megaphone.fm/yahoo-finance-presents",
"https://feeds.megaphone.fm/influencers-andy-serwer",
"https://feeds.megaphone.fm/real-vision-briefing",
"https://rss.art19.com/yahoofinancepresents",
"https://rss.art19.com/influencers",
"https://rss.art19.com/raise-your-hand-podcast",
"https://rss.art19.com/forbeslive",
"https://rss.art19.com/the-journal-wsj",
"https://rss.art19.com/wsj-your-money",
"https://rss.art19.com/wsj-minute-briefing",
"https://rss.art19.com/wsj-whats-news",
"https://rss.art19.com/marketwatch-money",
"https://rss.art19.com/barrons-streetwise",
"https://rss.art19.com/financial-times-money",
"https://rss.art19.com/bloomberg-odd-lots",
"https://rss.art19.com/bloomberg-masters",
"https://rss.art19.com/reuters-money-moves",
"https://rss.art19.com/cnbc-fast-money",
"https://rss.art19.com/cnbc-options-action",
"https://rss.art19.com/cnbc-halftime-report",
"https://rss.art19.com/cnbc-squawk-box",
"https://rss.art19.com/cnbc-power-lunch",
"https://rss.art19.com/cnbc-closing-bell",
"https://rss.art19.com/cnbc-worldwide-exchange",
"https://rss.art19.com/fox-business-hourly",
"https://rss.art19.com/everyone-talks-liz-claman",
"https://rss.art19.com/politico-money-podcast",
"https://rss.art19.com/seeking-alpha-podcast",
"https://rss.art19.com/morningstar-podcast",
"https://rss.art19.com/kiplinger-podcast",
"https://rss.art19.com/zacks-podcast",
"https://rss.art19.com/blackrock-the-bid",
"https://rss.art19.com/goldman-sachs-exchanges",
"https://rss.art19.com/russell-investments",
"https://rss.art19.com/investmentnews-podcast",
"https://rss.art19.com/colossus-investing",
"https://feeds.transistor.fm/acquired",
"https://feeds.megaphone.fm/DSLLC6297708582"
]

def main():
    """Main execution function"""
    # Hardcoded API key for testing
    gemini_api_key = "AIzaSyBwwqspks4SlM8ZWbPie-vMFbvDD_-ysG8"
    
    # Initialise the harvester with transcription enabled
    harvester = PodcastHarvester(
        download_dir="investment_podcast_harvest",
        max_workers=3,  # Be conservative
        batch_size=10,  # Smaller batches for transcription due to rate limits
        compress_audio=True,  # Enable compression
        target_bitrate=32,    # Aggressive compression
        transcribe_audio=True,  # Enable transcription
        gemini_api_key=gemini_api_key
    )
    
    # Use your podcast URLs
    rss_urls = INVESTMENT_FINANCE_PODCAST_URLS
    
    print(f"Ready to process {len(rss_urls)} investment & finance podcast feeds")
    print(f"Downloads will be organised into batches of {harvester.batch_size} episodes")
    print(f"Each episode will be transcribed using Gemini AI")
    print(f"Content analysis prompts will be generated for each batch")
    
    # Harvest episodes from the last 7 days
    episodes = harvester.harvest_podcasts(rss_urls, days_back=7)
    
    # Print final summary
    successful_downloads = len([ep for ep in episodes 
                              if ep.get('download_status') == 'success'])
    successful_transcriptions = len([ep for ep in episodes 
                                   if ep.get('transcription_status') == 'success'])
    
    if episodes:
        total_batches = len(set(ep.get('batch_number', 0) for ep in episodes))
        print(f"\n=== FINAL RESULTS ===")
        print(f"Total episodes processed: {len(episodes)}")
        print(f"Successfully downloaded: {successful_downloads}")
        print(f"Successfully transcribed: {successful_transcriptions}")
        print(f"Organised into {total_batches} batches")
        print(f"Files location: {harvester.download_dir}")
        
        print(f"\n=== BATCH STRUCTURE ===")
        for i in range(1, total_batches + 1):
            batch_episodes = [ep for ep in episodes if ep.get('batch_number') == i]
            batch_successful = len([ep for ep in batch_episodes if ep.get('download_status') == 'success'])
            batch_transcribed = len([ep for ep in batch_episodes if ep.get('transcription_status') == 'success'])
            print(f"  batch_{i:03d}/ - {batch_successful} MP3s, {batch_transcribed} transcripts + analysis prompt")
        
        print(f"\n=== NEXT STEPS ===")
        print("1. Review the transcript files in each batch directory")
        print("2. Use the analysis prompts with your AI tool to generate content")
        print("3. Each prompt includes the batch-specific CSV data")
        print("4. Transcripts are ready for your parenting content analysis!")
    
    return episodes

if __name__ == "__main__":
    # Install required dependencies
    print("Note: This script requires additional packages:")
    print("pip install feedparser requests pydub google-generativeai")
    print("You may also need ffmpeg installed on your system.\n")
    
    episodes = main()
