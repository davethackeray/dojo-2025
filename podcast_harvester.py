#!/usr/bin/env python3
"""
PODCAST HARVESTER MODULE
Handles RSS feed scanning, MP3 downloading, and compression

This module is responsible for:
1. Scanning RSS feeds for recent episodes
2. Downloading MP3 files
3. Compressing audio to <20MB for Gemini API
4. Managing batch processing

Based on the existing 1_ingest-compress-transcript.py but optimized for daily automation
"""

import feedparser
import requests
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import hashlib
import math
from pydub import AudioSegment
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PodcastHarvester:
    """Handles RSS feed scanning and MP3 processing"""
    
    def __init__(self, download_dir: Path, max_workers: int = 5, 
                 batch_size: int = 50, target_bitrate: int = 32):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.target_bitrate = target_bitrate
        
        # Setup HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        logger.info(f"PodcastHarvester initialized - Download dir: {download_dir}")
    
    def scan_rss_feeds(self, rss_urls: List[str], days_back: int = 1) -> List[Dict[str, Any]]:
        """Scan RSS feeds for recent episodes"""
        logger.info(f"Scanning {len(rss_urls)} RSS feeds for episodes from last {days_back} days")
        
        all_episodes = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all RSS feed processing tasks
            future_to_url = {
                executor.submit(self._process_single_feed, url, cutoff_date): url 
                for url in rss_urls
            }
            
            # Collect results
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    episodes = future.result()
                    all_episodes.extend(episodes)
                    if episodes:
                        logger.info(f"✅ {url}: Found {len(episodes)} recent episodes")
                    else:
                        logger.debug(f"⚪ {url}: No recent episodes")
                except Exception as e:
                    logger.warning(f"❌ {url}: Error - {str(e)}")
        
        logger.info(f"Total episodes found: {len(all_episodes)}")
        return all_episodes
    
    def _process_single_feed(self, rss_url: str, cutoff_date: datetime) -> List[Dict[str, Any]]:
        """Process a single RSS feed"""
        episodes = []
        
        try:
            # Parse RSS feed
            feed = feedparser.parse(rss_url)
            
            if not hasattr(feed, 'entries') or not feed.entries:
                return episodes
            
            # Process each entry
            for entry in feed.entries:
                # Check if episode is recent
                if not self._is_recent_episode(entry.get('published_parsed'), cutoff_date):
                    continue
                
                # Extract audio URL
                audio_url = self._extract_audio_url(entry)
                if not audio_url:
                    continue
                
                # Create episode metadata
                episode_data = {
                    'id': self._generate_episode_id(
                        feed.feed.get('title', 'Unknown'),
                        entry.get('title', 'Untitled'),
                        entry.get('published', '')
                    ),
                    'podcast_title': feed.feed.get('title', 'Unknown Podcast'),
                    'episode_title': entry.get('title', 'Untitled'),
                    'episode_url': entry.get('link', ''),
                    'media_url': audio_url,
                    'published_date': entry.get('published', ''),
                    'published_parsed': entry.get('published_parsed'),
                    'description': entry.get('description', ''),
                    'rss_url': rss_url,
                    'download_status': 'pending',
                    'compression_status': 'pending',
                    'local_filepath': None,
                    'compressed_filepath': None,
                    'file_size_mb': None
                }
                
                episodes.append(episode_data)
                
        except Exception as e:
            logger.error(f"Error processing RSS feed {rss_url}: {str(e)}")
        
        return episodes
    
    def _is_recent_episode(self, published_parsed, cutoff_date: datetime) -> bool:
        """Check if episode was published after cutoff date"""
        if not published_parsed:
            return False
        
        try:
            episode_date = datetime(*published_parsed[:6])
            return episode_date >= cutoff_date
        except (TypeError, ValueError):
            return False
    
    def _extract_audio_url(self, entry) -> Optional[str]:
        """Extract MP3 or audio URL from RSS entry"""
        # Check enclosures first (most common)
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if 'audio' in enclosure.get('type', '').lower():
                    return enclosure.get('url') or enclosure.get('href')
        
        # Check links
        if hasattr(entry, 'links'):
            for link in entry.links:
                if link.get('type', '').startswith('audio'):
                    return link.get('href')
        
        # Check media content
        if hasattr(entry, 'media_content'):
            for media in entry.media_content:
                if 'audio' in media.get('type', '').lower():
                    return media.get('url')
        
        return None
    
    def _generate_episode_id(self, podcast_title: str, episode_title: str, published_date: str) -> str:
        """Generate unique ID for episode"""
        content = f"{podcast_title}_{episode_title}_{published_date}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]
    
    def download_and_compress_episodes(self, episodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Download and compress episodes in batches"""
        logger.info(f"Processing {len(episodes)} episodes for download and compression")
        
        # Create batches
        batches = self._create_batches(episodes)
        processed_episodes = []
        
        for batch_num, batch_episodes in enumerate(batches, 1):
            logger.info(f"Processing batch {batch_num}/{len(batches)} ({len(batch_episodes)} episodes)")
            
            # Create batch directory
            batch_dir = self.download_dir / f"batch_{batch_num:03d}"
            batch_dir.mkdir(exist_ok=True)
            
            # Process episodes in this batch
            batch_results = self._process_batch(batch_episodes, batch_dir, batch_num)
            processed_episodes.extend(batch_results)
            
            # Save batch summary
            self._save_batch_summary(batch_dir, batch_num, batch_results)
        
        successful_episodes = [ep for ep in processed_episodes if ep.get('download_status') == 'success']
        logger.info(f"Successfully processed {len(successful_episodes)}/{len(episodes)} episodes")
        
        return successful_episodes
    
    def _create_batches(self, episodes: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Split episodes into batches"""
        batches = []
        for i in range(0, len(episodes), self.batch_size):
            batch = episodes[i:i + self.batch_size]
            batches.append(batch)
        return batches
    
    def _process_batch(self, episodes: List[Dict[str, Any]], batch_dir: Path, batch_num: int) -> List[Dict[str, Any]]:
        """Process a single batch of episodes"""
        processed_episodes = []
        
        for episode in episodes:
            try:
                # Download episode
                success = self._download_episode(episode, batch_dir)
                
                if success:
                    # Compress episode
                    self._compress_episode(episode, batch_dir)
                    
                processed_episodes.append(episode)
                
            except Exception as e:
                logger.error(f"Error processing episode {episode['id']}: {str(e)}")
                episode['download_status'] = 'error'
                episode['error_message'] = str(e)
                processed_episodes.append(episode)
        
        return processed_episodes
    
    def _download_episode(self, episode: Dict[str, Any], batch_dir: Path) -> bool:
        """Download a single episode"""
        try:
            # Create safe filename
            safe_podcast = self._sanitize_filename(episode['podcast_title'])
            safe_episode = self._sanitize_filename(episode['episode_title'])
            filename = f"{episode['id']}_{safe_podcast}_{safe_episode}.mp3"
            filepath = batch_dir / filename
            
            # Download file
            logger.debug(f"Downloading: {filename}")
            response = self.session.get(episode['media_url'], stream=True, timeout=30)
            response.raise_for_status()
            
            # Save file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Update episode data
            episode['local_filepath'] = str(filepath)
            episode['download_status'] = 'success'
            episode['file_size_mb'] = filepath.stat().st_size / (1024 * 1024)
            
            logger.debug(f"✅ Downloaded: {filename} ({episode['file_size_mb']:.1f}MB)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Download failed for {episode['id']}: {str(e)}")
            episode['download_status'] = 'failed'
            episode['error_message'] = str(e)
            return False
    
    def _compress_episode(self, episode: Dict[str, Any], batch_dir: Path):
        """Compress episode to <20MB for Gemini API"""
        if episode['download_status'] != 'success':
            return
        
        try:
            original_path = Path(episode['local_filepath'])
            compressed_filename = f"compressed_{original_path.name}"
            compressed_path = batch_dir / compressed_filename
            
            # Check if compression is needed
            if episode['file_size_mb'] <= 20:
                logger.debug(f"File already under 20MB: {original_path.name}")
                episode['compressed_filepath'] = episode['local_filepath']
                episode['compression_status'] = 'not_needed'
                return
            
            logger.debug(f"Compressing: {original_path.name} ({episode['file_size_mb']:.1f}MB)")
            
            # Load and compress audio
            audio = AudioSegment.from_file(str(original_path))
            
            # Apply compression settings
            if audio.channels > 1:
                audio = audio.set_channels(1)  # Convert to mono
            
            audio = audio.set_frame_rate(22050)  # Reduce sample rate
            audio = audio.normalize()  # Normalize volume
            
            # Export with low bitrate
            audio.export(
                str(compressed_path),
                format="mp3",
                bitrate=f"{self.target_bitrate}k",
                parameters=[
                    "-ac", "1",  # Force mono
                    "-ar", "22050",  # Sample rate
                    "-q:a", "9",  # Lowest quality
                ]
            )
            
            # Update episode data
            compressed_size_mb = compressed_path.stat().st_size / (1024 * 1024)
            episode['compressed_filepath'] = str(compressed_path)
            episode['compression_status'] = 'success'
            episode['compressed_size_mb'] = compressed_size_mb
            
            compression_ratio = (1 - compressed_size_mb / episode['file_size_mb']) * 100
            logger.debug(f"✅ Compressed: {original_path.name} -> {compressed_size_mb:.1f}MB ({compression_ratio:.1f}% reduction)")
            
            # Remove original if compression successful
            original_path.unlink()
            
        except Exception as e:
            logger.error(f"❌ Compression failed for {episode['id']}: {str(e)}")
            episode['compression_status'] = 'failed'
            episode['compression_error'] = str(e)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Clean filename for safe saving with Windows compatibility"""
        # Remove/replace problematic characters
        invalid_chars = '<>:"/\\|?*&'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Replace spaces and special characters for Windows
        filename = filename.replace(' ', '_')
        filename = filename.replace('&', 'and')
        filename = filename.replace('_', '')  # Remove underscores to shorten
        filename = filename.replace('-', '')  # Remove dashes to shorten
        
        # Much shorter limit for Windows compatibility
        return filename[:30]  # Very short limit
    
    def _save_batch_summary(self, batch_dir: Path, batch_num: int, episodes: List[Dict[str, Any]]):
        """Save batch processing summary"""
        successful_downloads = len([ep for ep in episodes if ep.get('download_status') == 'success'])
        successful_compressions = len([ep for ep in episodes if ep.get('compression_status') in ['success', 'not_needed']])
        
        summary = {
            'batch_number': batch_num,
            'timestamp': datetime.now().isoformat(),
            'total_episodes': len(episodes),
            'successful_downloads': successful_downloads,
            'successful_compressions': successful_compressions,
            'episodes': episodes
        }
        
        summary_file = batch_dir / f"batch_{batch_num:03d}_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Batch {batch_num} summary: {successful_downloads}/{len(episodes)} downloaded, {successful_compressions}/{len(episodes)} compressed")