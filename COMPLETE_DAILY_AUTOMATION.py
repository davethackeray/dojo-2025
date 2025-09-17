#!/usr/bin/env python3
"""
COMPLETE DAILY AUTOMATION SYSTEM
InvestingDojo.co - End-to-End Content Generation Pipeline

This is the MASTER automation script that orchestrates the complete workflow:
1. RSS Feed Scanning (250+ podcasts)
2. MP3 Download & Compression (<20MB)
3. Gemini AI Transcription (rate-limited)
4. Story Generation using SuperPrompt_Optimized.md with CrewAI integration
5. Database Import (local/production)

USAGE:
python automation/COMPLETE_DAILY_AUTOMATION.py

REQUIREMENTS:
- GEMINI_API_KEY environment variable
- automation/SuperPrompt_Optimized.md file (or SuperPrompt.md as fallback)
- Local database connection
- Internet connection
- Optional: CrewAI integration (CREWAI_ENABLED=true)

RATE LIMITS:
- Gemini API: 10 RPM, 150/day max
- MP3 Processing: No limits (local processing)
- Batch Processing: Configurable batch sizes

Created for task 2: Polish and perfect automation epic in local environment
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import traceback
import mysql.connector
from mysql.connector import Error

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import our automation components
from automation.podcast_harvester import PodcastHarvester
from automation.story_generator import StoryGenerator
from automation.database_importer import DatabaseImporter

# Import CrewAI integration layer
try:
    from automation.crewai_integration import IntegratedStoryGenerator, StoryGeneratorFactory
    CREWAI_INTEGRATION_AVAILABLE = True
except ImportError as e:
    logging.warning(f"CrewAI integration not available: {str(e)}")
    CREWAI_INTEGRATION_AVAILABLE = False
    IntegratedStoryGenerator = None
    StoryGeneratorFactory = None

# Import Editorial Director
try:
    from automation.editorial_director import EditorialDirector
    EDITORIAL_DIRECTOR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Editorial Director not available: {str(e)}")
    EDITORIAL_DIRECTOR_AVAILABLE = False
    EditorialDirector = None

class CompleteDailyAutomation:
    """Master automation orchestrator"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.setup_logging()
        self.config = self.load_configuration()
        self.stats = {
            'start_time': datetime.now(),
            'feeds_processed': 0,
            'episodes_found': 0,
            'episodes_downloaded': 0,
            'episodes_transcribed': 0,
            'stories_generated': 0,
            'stories_imported': 0,
            'stories_updated': 0,
            'production_synced': 0,
            'production_errors': 0,
            'api_calls_made': 0,
            'total_processing_time': 0,
            'errors': [],
            'warnings': [],
            'performance_metrics': {}
        }
        
        # RSS Feed URLs (from existing automation file)
        self.rss_feeds = [
"https://feeds.npr.org/510289/podcast.xml",
"https://feeds.simplecast.com/tOjNXec5",
"https://media.rss.com/confessionsmm/feed.xml",
"https://feeds.npr.org/510325/podcast.xml",
"https://media.rss.com/bankingwithlifepodcast/feed.xml",
"https://media.rss.com/workbench/feed.xml",
"https://feeds.simplecast.com/_qvRgwME",
"https://feeds.simplecast.com/_mQMEG_J",
"https://feeds.simplecast.com/tc4zxWgX",
"https://feeds.simplecast.com/qltQrd_8",
"https://feeds.simplecast.com/CqxTohm7",
"https://feeds.simplecast.com/Bt3ITxGl",
"https://rss.art19.com/forbes-daily-briefing",
"https://feeds.simplecast.com/szW8tJ16",
"https://video-api.wsj.com/podcast/rss/wsj/minute-briefing",
"https://video-api.wsj.com/podcast/rss/wsj/whats-news",
"https://feeds.simplecast.com/Nh1wIaXT",
"https://feeds.simplecast.com/GcylmXl7",
"https://feeds.simplecast.com/TkQfZXMD",
"https://video-api.barrons.com/podcast/rss/marketwatch/best-new-ideas-in-money",
"https://feeds.simplecast.com/Q7fb3j2T",
"https://rss.art19.com/steve-forbes-whats-ahead",
"https://video-api.wsj.com/podcast/rss/wsj/the-journal",
"https://feeds.libsyn.com/115914/rss",
"https://feeds.megaphone.fm/FOXM2611238522",
"https://feeds.libsyn.com/102774/rss",
"https://feeds.libsyn.com/304496/rss",
"https://feeds.libsyn.com/84049/rss",
"https://feeds.libsyn.com/100426/rss",
"https://feeds.libsyn.com/161936/rss",
"https://feeds.libsyn.com/88745/rss",
"https://feeds.buzzsprout.com/552559.rss",
"https://feeds.blubrry.com/feeds/schiffradio.xml",
"https://feeds.simplecast.com/YEK6OY3e",
"https://rss.art19.com/squawk-box-europe",
"https://rss.art19.com/the-bid",
"https://yourmoneysworth.libsyn.com/rss",
"https://rss.art19.com/on-the-market",
"https://feeds.buzzsprout.com/2289984.rss",
"https://rss.art19.com/money-for-the-rest-of-us",
"https://feeds.libsyn.com/75720/rss",
"https://feeds.libsyn.com/85372/rss",
"https://feeds.buzzsprout.com/1348435.rss",
"https://rss.art19.com/biggerpockets-money-podcast",
"https://feeds.libsyn.com/123456/rss",
"https://feeds.libsyn.com/456789/rss",
"https://feeds.libsyn.com/567890/rss",
"https://feeds.transistor.fm/acquired",
"https://feeds.megaphone.fm/DSLLC6297708582"
        ]
        
        self.logger.info(f"Initialized with {len(self.rss_feeds)} RSS feeds")
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"daily_automation_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Daily automation started - Log file: {log_file}")
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from environment and files"""
        config = {
            'gemini_api_key': os.getenv('GEMINI_API_KEY', 'AIzaSyBwwqspks4SlM8ZWbPie-vMFbvDD_-ysG8'),
            'download_dir': Path("temp_processing"),
            'batch_size': 50,  # For MP3 processing
            'ai_batch_size': 3,  # For AI processing (rate limited)
            'days_back': 1,  # Look for episodes from last 24 hours
            'max_file_size_mb': 20,
            'target_bitrate': 32,
            'rate_limits': {
                'requests_per_minute': 10,
                'requests_per_day': 250,
                'max_daily_episodes': 240  # Safety buffer - max episodes to process per day
            },
            'local_database': {
                'host': os.getenv('DB_LOCAL_HOST', 'localhost'),
                'database': os.getenv('DB_LOCAL_DATABASE', 'u219832816_investing_dojo'),
                'user': os.getenv('DB_LOCAL_USER', 'u219832816_davethackeray'),
                'password': os.getenv('DB_LOCAL_PASSWORD', 'ToTheM00n!'),
                'charset': 'utf8mb4',
                'use_unicode': True,
                'autocommit': False
            },
            'production_database': {
                'host': os.getenv('DB_PROD_HOST', 'srv1910.hstgr.io'),
                'database': os.getenv('DB_PROD_DATABASE', 'u219832816_investing_dojo'),
                'user': os.getenv('DB_PROD_USER', 'u219832816_davethackeray'),
                'password': os.getenv('DB_PROD_PASSWORD', 'ToTheM00n!'),
                'charset': 'utf8mb4',
                'use_unicode': True,
                'autocommit': False
            },
            # Enhanced time_required ENUM values to support broader range
            'supported_time_required_values': [
                '5-minutes', '6-minutes', '7-minutes', '8-minutes', '10-minutes', '15-minutes', '30-minutes',
                '1-hour', '2-hours', '3-hours', '4-hours', '6-hours', '8-hours',
                '1-day', '2-days', '3-days', '1-week', '2-weeks', '1-month',
                'ongoing', 'varies', 'immediate', 'quick-read', 'deep-dive'
            ],
            'sync_to_production': True,  # Enable production sync
            'validation_checks': True,   # Enable validation before production sync
            'min_stories_for_sync': 1    # Minimum stories required before syncing to production
        }
        
        # Validate critical configuration
        if not config['gemini_api_key']:
            self.logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY is required")
        
        # Validate database credentials
        self._validate_database_config(config['local_database'], 'local')
        self._validate_database_config(config['production_database'], 'production')
        
        # Check SuperPrompt exists - try SuperPrompt_Optimized.md first, then SuperPrompt.md
        # Handle both cases: running from project root or from automation directory
        automation_dir = Path(__file__).parent
        project_root = automation_dir.parent
        
        # Try different possible locations
        possible_paths = [
            automation_dir / "SuperPrompt_Optimized.md",  # automation/SuperPrompt_Optimized.md (from automation dir)
            project_root / "automation" / "SuperPrompt_Optimized.md",  # automation/SuperPrompt_Optimized.md (from project root)
            automation_dir / "SuperPrompt.md",  # automation/SuperPrompt.md (from automation dir)
            project_root / "automation" / "SuperPrompt.md"  # automation/SuperPrompt.md (from project root)
        ]
        
        config['superprompt_path'] = None
        for path in possible_paths:
            if path.exists():
                config['superprompt_path'] = path
                if "SuperPrompt_Optimized.md" in str(path):
                    self.logger.info(f"[OK] Using SuperPrompt_Optimized.md (enhanced template): {path}")
                else:
                    self.logger.info(f"[OK] Using SuperPrompt.md (fallback template): {path}")
                break
        
        if not config['superprompt_path']:
            self.logger.error("Neither SuperPrompt_Optimized.md nor SuperPrompt.md found in expected locations")
            self.logger.error(f"Searched paths: {[str(p) for p in possible_paths]}")
            raise FileNotFoundError("SuperPrompt_Optimized.md or SuperPrompt.md is required")
        
        # Create directories
        config['download_dir'].mkdir(exist_ok=True)
        
        self.logger.info("Configuration loaded successfully")
        return config
    
    def _validate_database_config(self, db_config: Dict[str, Any], db_type: str):
        """Validate database configuration and provide helpful error messages"""
        required_fields = ['host', 'database', 'user', 'password']
        missing_fields = []
        
        for field in required_fields:
            if not db_config.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            env_vars = {
                'local': {
                    'host': 'DB_LOCAL_HOST',
                    'database': 'DB_LOCAL_DATABASE',
                    'user': 'DB_LOCAL_USER',
                    'password': 'DB_LOCAL_PASSWORD'
                },
                'production': {
                    'host': 'DB_PROD_HOST',
                    'database': 'DB_PROD_DATABASE',
                    'user': 'DB_PROD_USER',
                    'password': 'DB_PROD_PASSWORD'
                }
            }
            
            missing_env_vars = [env_vars[db_type][field] for field in missing_fields]
            
            self.logger.error(f"[ERROR] Missing {db_type} database configuration:")
            for field, env_var in zip(missing_fields, missing_env_vars):
                self.logger.error(f"   - {field}: Set environment variable {env_var}")
            
            self.logger.error(f"\n[TIP] To fix this:")
            self.logger.error(f"   1. Create a .env file based on .env.example")
            self.logger.error(f"   2. Set the missing environment variables:")
            for env_var in missing_env_vars:
                self.logger.error(f"      export {env_var}=your_value")
            self.logger.error(f"   3. Or set them in your system environment")
            
            raise ValueError(f"Missing required {db_type} database configuration: {', '.join(missing_fields)}")
        
        self.logger.info(f"[OK] {db_type.title()} database configuration validated")
    
    def run_complete_automation(self) -> bool:
        """Run the complete daily automation workflow"""
        try:
            self.logger.info("[START] STARTING COMPLETE DAILY AUTOMATION")
            self.logger.info("=" * 60)
            
            # Step 1: Scan RSS feeds and find recent episodes
            self.logger.info("[SATELLITE_ANTENNA] STEP 1: Scanning RSS feeds for recent episodes")
            recent_episodes = self.scan_rss_feeds()
            
            if not recent_episodes:
                self.logger.warning("No recent episodes found. Automation complete.")
                return True
            
            # Step 2: Download and compress MP3 files
            self.logger.info("[DOWNLOAD] STEP 2: Downloading and compressing MP3 files")
            downloaded_episodes = self.download_and_compress_episodes(recent_episodes)
            
            if not downloaded_episodes:
                self.logger.warning("No episodes downloaded successfully.")
                return False
            
            # Step 3: Transcribe audio files (rate limited)
            self.logger.info("[TRANSCRIBE] STEP 3: Transcribing audio files with Gemini AI")
            transcribed_episodes = self.transcribe_episodes(downloaded_episodes)
            
            if not transcribed_episodes:
                self.logger.warning("No episodes transcribed successfully.")
                return False
            
            # Step 4: Editorial Director Analysis and Curation
            self.logger.info("[EDITORIAL] STEP 4: Editorial Director - Content Curation and Strategy")
            editorial_briefs = self.editorial_content_curation(transcribed_episodes)
            
            if not editorial_briefs:
                self.logger.warning("Editorial Director found no suitable content for publication.")
                # Continue with standard workflow as fallback
                editorial_briefs = None
            
            # Step 5: Generate stories using SuperPrompt with Editorial Direction
            self.logger.info("[GENERATE] STEP 5: Generating stories using SuperPrompt with Editorial Direction")
            generated_stories = self.generate_stories(transcribed_episodes, editorial_briefs)
            
            if not generated_stories:
                self.logger.warning("No stories generated successfully.")
                return False
            
            # Step 6: Import stories to local database
            self.logger.info("[IMPORT] STEP 6: Importing stories to local database")
            import_success = self.import_stories_to_database(generated_stories)
            
            if not import_success:
                self.logger.error("[ERROR] Local database import failed")
                return False
            
            # Step 7: Sync to production database (if enabled)
            production_sync_success = True
            if self.config.get('sync_to_production', False):
                self.logger.info("[SYNC] STEP 7: Syncing new stories to production database")
                production_sync_success = self.sync_to_production(generated_stories)
            else:
                self.logger.info("⏭️ STEP 7: Production sync disabled - skipping")
            
            # Step 8: Generate final report with Editorial Analysis
            self.generate_final_report(editorial_briefs)
            
            if import_success and production_sync_success:
                self.logger.info("[SUCCESS] COMPLETE DAILY AUTOMATION FINISHED SUCCESSFULLY!")
                return True
            else:
                self.logger.error("[ERROR] Automation completed with errors")
                return False
                
        except Exception as e:
            self.logger.error(f"[ERROR] AUTOMATION FAILED: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.stats['errors'].append(str(e))
            return False
    
    def scan_rss_feeds(self) -> List[Dict[str, Any]]:
        """Scan all RSS feeds for recent episodes"""
        try:
            start_time = time.time()
            
            harvester = PodcastHarvester(
                download_dir=self.config['download_dir'],
                batch_size=self.config['batch_size']
            )
            
            recent_episodes = harvester.scan_rss_feeds(
                rss_urls=self.rss_feeds,
                days_back=self.config['days_back']
            )
            
            processing_time = time.time() - start_time
            self.stats['performance_metrics']['rss_scanning_time'] = processing_time
            self.stats['feeds_processed'] = len(self.rss_feeds)
            self.stats['episodes_found'] = len(recent_episodes)
            
            self.logger.info(f"Found {len(recent_episodes)} recent episodes in {processing_time:.2f}s")
            
            # Log episode details for debugging
            for i, episode in enumerate(recent_episodes[:5]):  # Show first 5
                title = episode.get('title', 'Unknown')[:60]
                pub_date = episode.get('published_date', 'Unknown')
                self.logger.debug(f"  [RADIO] Episode {i+1}: {title}... ({pub_date})")
            
            return recent_episodes
            
        except Exception as e:
            self.logger.error(f"RSS scanning failed: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.stats['errors'].append(f"RSS scanning: {str(e)}")
            return []
    
    def download_and_compress_episodes(self, episodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Download and compress MP3 files to <20MB"""
        try:
            start_time = time.time()
            
            harvester = PodcastHarvester(
                download_dir=self.config['download_dir'],
                batch_size=self.config['batch_size'],
                target_bitrate=self.config['target_bitrate']
            )
            
            downloaded_episodes = harvester.download_and_compress_episodes(episodes)
            
            processing_time = time.time() - start_time
            self.stats['performance_metrics']['mp3_processing_time'] = processing_time
            self.stats['episodes_downloaded'] = len(downloaded_episodes)
            
            # Validate file sizes and compression
            total_size_mb = 0
            for episode in downloaded_episodes:
                file_path = episode.get('compressed_filepath')
                if file_path and Path(file_path).exists():
                    file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
                    total_size_mb += file_size_mb
                    
                    self.logger.debug(f"  [FILE] {Path(file_path).name}: {file_size_mb:.1f}MB")
                    
                    if file_size_mb > self.config['max_file_size_mb']:
                        warning_msg = f"File exceeds {self.config['max_file_size_mb']}MB: {file_size_mb:.1f}MB"
                        self.stats['warnings'].append(warning_msg)
                        self.logger.warning(warning_msg)
            
            self.logger.info(f"Successfully downloaded {len(downloaded_episodes)} episodes in {processing_time:.2f}s")
            self.logger.info(f"Total size: {total_size_mb:.1f}MB")
            return downloaded_episodes
            
        except Exception as e:
            self.logger.error(f"Download/compression failed: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.stats['errors'].append(f"Download/compression: {str(e)}")
            return []
    
    def transcribe_episodes(self, episodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transcribe audio files using Gemini AI with rate limiting"""
        # This step is combined with story generation for efficiency
        # Gemini can transcribe and generate stories in one API call
        self.logger.info(f"Episodes ready for AI processing: {len(episodes)}")
        
        self.stats['episodes_transcribed'] = len(episodes)
        return episodes
    
    def editorial_content_curation(self, episodes: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """
        ENHANCED Editorial Director step - Curate and strategize content creation
        
        This is where the magic happens - the Editorial Director analyzes all transcripts,
        identifies the most compelling content, and provides strategic direction for
        world-class story generation.
        
        KEY ENHANCEMENT: The Editorial Director now acts as a FILTER - only content that
        meets editorial standards proceeds to the next step. This ensures we publish
        only the most incisive, inspiring, family-focused content.
        """
        try:
            if not EDITORIAL_DIRECTOR_AVAILABLE or not EditorialDirector:
                self.logger.warning("[NOTE] Editorial Director not available - proceeding with standard workflow")
                return None
            
            start_time = time.time()
            
            # Initialize Editorial Director
            editorial_director = EditorialDirector(
                api_key=self.config['gemini_api_key'],
                config=self.config
            )
            
            self.logger.info("[EDITORIAL] Editorial Director analyzing transcripts for world-class content...")
            
            # ENHANCED: Actually transcribe episodes first for proper analysis
            transcribed_episodes = []
            for episode in episodes:
                try:
                    # Use the story generator's transcription capability
                    from automation.story_generator import StoryGenerator
                    temp_generator = StoryGenerator(
                        api_key=self.config['gemini_api_key'],
                        superprompt_path=self.config['superprompt_path']
                    )
                    
                    # Get the compressed file path
                    audio_file = episode.get('compressed_filepath')
                    if audio_file and Path(audio_file).exists():
                        self.logger.info(f"[TRANSCRIBE] Transcribing for editorial analysis: {Path(audio_file).name}")
                        transcript_text = temp_generator._transcribe_audio_file(audio_file)
                        episode['transcript_text'] = transcript_text
                        transcribed_episodes.append(episode)
                        
                        # Rate limiting for transcription
                        time.sleep(3)
                    else:
                        self.logger.warning(f"[WARNING] Audio file not found for editorial analysis: {audio_file}")
                        
                except Exception as e:
                    self.logger.error(f"[ERROR] Transcription failed for editorial analysis: {str(e)}")
                    # Use episode metadata as fallback
                    episode['transcript_text'] = f"Episode: {episode.get('title', 'Unknown')} from {episode.get('source', {}).get('podcast_title', 'Unknown')}"
                    transcribed_episodes.append(episode)
            
            # Prepare transcript data for editorial analysis
            transcript_data = []
            for episode in transcribed_episodes:
                transcript_data.append({
                    'id': episode.get('id', f"episode_{len(transcript_data)}"),
                    'title': episode.get('title', 'Unknown Episode'),
                    'transcript_text': episode.get('transcript_text', ''),
                    'source': episode.get('source', {})
                })
            
            # Editorial Director Analysis
            analyses = editorial_director.analyze_daily_transcripts(transcript_data)
            
            # CRITICAL FILTER: Only proceed with content that meets editorial standards
            high_quality_analyses = [a for a in analyses if a.quality_score >= 7.0]
            family_focused_analyses = [a for a in high_quality_analyses if a.family_engagement_potential >= 7.0]
            
            self.logger.info(f"[STATS] EDITORIAL FILTER: {len(analyses)} → {len(high_quality_analyses)} high-quality → {len(family_focused_analyses)} family-focused")
            
            if not family_focused_analyses:
                self.logger.warning("[WARNING] No content meets Editorial Director standards - using top content with lower threshold")
                family_focused_analyses = analyses[:3] if analyses else []
            
            # Filter episodes to only those that passed editorial review
            approved_episode_ids = [a.transcript_id for a in family_focused_analyses]
            filtered_episodes = [ep for ep in transcribed_episodes if ep.get('id') in approved_episode_ids]
            
            # Update the episodes list to only include approved content
            episodes.clear()
            episodes.extend(filtered_episodes)
            
            self.logger.info(f"[EDITORIAL] EDITORIAL APPROVAL: {len(filtered_episodes)} episodes approved for content generation")
            
            # Identify common threads and themes
            theme_groups = editorial_director.identify_common_threads(family_focused_analyses)
            
            # Make strategic editorial decisions
            editorial_decisions = editorial_director.make_editorial_decisions(family_focused_analyses, theme_groups)
            
            # Orchestrate content creation with editorial briefs
            content_briefs = editorial_director.orchestrate_content_creation(editorial_decisions)
            
            # Generate editorial report
            editorial_report = editorial_director.generate_editorial_report(family_focused_analyses, editorial_decisions)
            
            # Store editorial data for final report
            self.stats['editorial_analysis'] = {
                'transcripts_analyzed': len(analyses),
                'transcripts_approved': len(family_focused_analyses),
                'editorial_decisions': len(editorial_decisions),
                'content_briefs_created': len(content_briefs),
                'average_content_quality': editorial_report['content_quality_overview']['average_quality_score'],
                'high_quality_content_count': editorial_report['content_quality_overview']['high_quality_content_count'],
                'trending_themes': editorial_report['trending_themes'][:5]  # Top 5 themes
            }
            
            processing_time = time.time() - start_time
            self.stats['performance_metrics']['editorial_curation_time'] = processing_time
            
            self.logger.info(f"[SUCCESS] Editorial Director completed analysis in {processing_time:.2f}s")
            self.logger.info(f"[STATS] Quality Overview: {editorial_report['content_quality_overview']['high_quality_content_count']} high-quality pieces identified")
            self.logger.info(f"[EDITORIAL] Strategic Decisions: {len(editorial_decisions)} editorial decisions made")
            self.logger.info(f"[NOTE] Content Briefs: {len(content_briefs)} strategic briefs created for writers")
            
            return content_briefs
            
        except Exception as e:
            self.logger.error(f"[ERROR] Editorial Director failed: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.stats['errors'].append(f"Editorial Director: {str(e)}")
            return None
    
    def generate_stories(self, episodes: List[Dict[str, Any]], editorial_briefs: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Generate stories using SuperPrompt with CrewAI integration and Editorial Direction"""
        try:
            start_time = time.time()
            
            # Apply daily episode limit safety check
            max_daily_episodes = self.config['rate_limits'].get('max_daily_episodes', 140)
            if len(episodes) > max_daily_episodes:
                self.logger.warning(f"[WARNING] Found {len(episodes)} episodes, limiting to {max_daily_episodes} to stay within API limits")
                episodes = episodes[:max_daily_episodes]
                self.stats['warnings'].append(f"Limited processing to {max_daily_episodes} episodes to prevent API limit exceeded")
            
            # Editorial Direction Integration
            if editorial_briefs:
                self.logger.info("[EDITORIAL] Using Editorial Director briefs for strategic content creation")
                self.logger.info(f"[CLIPBOARD] Processing {len(editorial_briefs)} editorial briefs with strategic direction")
                
                # Log editorial priorities
                for brief in editorial_briefs[:3]:  # Show top 3 briefs
                    self.logger.info(f"   [NOTE] {brief['content_strategy']}: {brief['editorial_brief']['story_angle'][:60]}...")
            else:
                self.logger.info("[NOTE] No editorial briefs available - using standard content generation")
            
            # Use CrewAI integration layer if available, otherwise fallback to standard generator
            if CREWAI_INTEGRATION_AVAILABLE and IntegratedStoryGenerator:
                self.logger.info("🤖 Using CrewAI integration layer for story generation")
                story_generator = IntegratedStoryGenerator(
                    api_key=self.config['gemini_api_key'],
                    superprompt_path=self.config['superprompt_path'],
                    config=self.config
                )
                
                # Editorial briefs will be passed through the config system
                if editorial_briefs:
                    self.logger.info(f"[CLIPBOARD] Editorial briefs available for CrewAI integration: {len(editorial_briefs)} briefs")
                    
            else:
                self.logger.info("[NOTE] Using standard StoryGenerator (CrewAI integration not available)")
                story_generator = StoryGenerator(
                    api_key=self.config['gemini_api_key'],
                    superprompt_path=self.config['superprompt_path']
                )
            
            # Process episodes in batches (rate limited)
            generated_stories = story_generator.process_episodes_batch(
                episodes=episodes,
                batch_size=self.config['ai_batch_size']
            )
            
            processing_time = time.time() - start_time
            self.stats['performance_metrics']['ai_generation_time'] = processing_time
            self.stats['stories_generated'] = len(generated_stories)
            self.stats['api_calls_made'] = len(episodes)  # Approximate
            
            # Validate story structure and quality
            for i, story in enumerate(generated_stories):
                title = story.get('title', 'Unknown')[:50]
                content_length = len(str(story.get('full_content', '')))
                belt_levels = story.get('belt_levels', [])
                
                self.logger.debug(f"  [NOTE] Story {i+1}: {title}... ({content_length} chars, {len(belt_levels)} belts)")
                
                # Validate required fields
                required_fields = ['id', 'title', 'summary', 'full_content', 'content_type', 'belt_levels']
                missing_fields = [field for field in required_fields if not story.get(field)]
                
                if missing_fields:
                    warning_msg = f"Story {i+1} missing fields: {missing_fields}"
                    self.stats['warnings'].append(warning_msg)
                    self.logger.warning(warning_msg)
            
            self.logger.info(f"Successfully generated {len(generated_stories)} stories in {processing_time:.2f}s")
            return generated_stories
            
        except Exception as e:
            self.logger.error(f"Story generation failed: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.stats['errors'].append(f"Story generation: {str(e)}")
            return []
    
    def import_stories_to_database(self, stories: List[Dict[str, Any]]) -> bool:
        """Import generated stories to local database"""
        try:
            import mysql.connector
            from mysql.connector import Error
            
            # Connect to database
            connection = mysql.connector.connect(**self.config['local_database'])
            cursor = connection.cursor()
            
            imported_count = 0
            updated_count = 0
            errors = []
            
            for story in stories:
                try:
                    # Start transaction for each story
                    connection.start_transaction()
                    
                    # Extract main story data
                    story_id = story.get('id')
                    if not story_id:
                        self.logger.warning("Story missing ID, skipping")
                        continue
                    
                    # Check if story already exists
                    cursor.execute("SELECT id FROM stories WHERE id = %s", (story_id,))
                    existing = cursor.fetchone()
                    
                    # Prepare main story data
                    story_data = {
                        'id': story_id,
                        'title': story.get('title', '')[:500],
                        'summary': story.get('summary', ''),
                        'full_content': story.get('full_content', ''),
                        'curriculum_alignment': story.get('curriculum_alignment'),
                        'ai_skill_level': story.get('ai_skill_level'),
                        'ai_roi_potential': story.get('ai_roi_potential'),
                        'investment_domain_primary': story.get('investment_domain_primary'),
                        'difficulty_level': story.get('difficulty_level'),
                        'urgency': story.get('urgency'),
                        'concept_hierarchy_level': story.get('concept_hierarchy_level'),
                        'learning_sequence_position': story.get('learning_sequence_position'),
                        'experience_assumptions': story.get('experience_assumptions'),
                        'tech_savviness_required': story.get('tech_savviness_required'),
                        'expert_credentials': json.dumps(story.get('expert_credentials', {})) if story.get('expert_credentials') else None,
                        'track_record_mentions': story.get('track_record_mentions'),
                        'source_bias_assessment': json.dumps(story.get('source_bias_assessment', {})) if story.get('source_bias_assessment') else None,
                        'quote_highlight': story.get('quote_highlight'),
                        'family_security_relevance': json.dumps(story.get('family_security_relevance', {})) if isinstance(story.get('family_security_relevance'), dict) else story.get('family_security_relevance'),
                        'generational_wealth_relevance': json.dumps(story.get('generational_wealth_relevance', {})) if isinstance(story.get('generational_wealth_relevance'), dict) else story.get('generational_wealth_relevance'),
                        'children_education_angle': json.dumps(story.get('children_education_angle', {})) if story.get('children_education_angle') else None,
                        'emergency_fund_consideration': story.get('emergency_fund_consideration'),
                        'risk_level': story.get('risk_level'),
                        'time_required': self._normalize_time_required(story.get('time_required')),
                        'email_subject_line': story.get('email_subject_line', '')[:500],
                        'social_snippet': story.get('social_snippet', '')[:280],
                        'community_hook': story.get('community_hook'),
                        'app_hook': story.get('app_hook'),
                        'podcast_hook': story.get('podcast_hook'),
                        'financial_disclaimer': 1 if story.get('financial_disclaimer', True) else 0,
                        'dinner_table_readiness': story.get('family_engagement_metrics', {}).get('dinner_table_readiness'),
                        'estimated_read_time': story.get('performance_metrics', {}).get('estimated_read_time'),
                        'complexity_rating': story.get('performance_metrics', {}).get('complexity_rating'),
                        'retention_probability': story.get('performance_metrics', {}).get('retention_probability'),
                        'application_difficulty': story.get('performance_metrics', {}).get('application_difficulty'),
                        'confidence_building': story.get('scoring', {}).get('confidence_building'),
                        'family_impact': story.get('scoring', {}).get('family_impact'),
                        'mastery_potential': story.get('scoring', {}).get('mastery_potential'),
                        'viral_potential': story.get('scoring', {}).get('viral_potential')
                    }
                    
                    # Get content type ID
                    content_type = story.get('content_type', 'research-method')
                    cursor.execute("SELECT id FROM content_types WHERE name = %s", (content_type,))
                    content_type_result = cursor.fetchone()
                    
                    if not content_type_result:
                        # Create new content type if it doesn't exist
                        cursor.execute(
                            "INSERT INTO content_types (name, description) VALUES (%s, %s)",
                            (content_type, f"Auto-created content type: {content_type}")
                        )
                        story_data['content_type_id'] = cursor.lastrowid
                    else:
                        story_data['content_type_id'] = content_type_result[0]
                    
                    if existing:
                        # Update existing story
                        update_fields = []
                        update_values = []
                        for key, value in story_data.items():
                            if key != 'id':
                                update_fields.append(f"{key} = %s")
                                update_values.append(value)
                        
                        update_values.append(story_id)
                        update_query = f"UPDATE stories SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = %s"
                        cursor.execute(update_query, update_values)
                        updated_count += 1
                        self.logger.debug(f"Updated story: {story_id}")
                    else:
                        # Insert new story
                        fields = list(story_data.keys())
                        values = list(story_data.values())
                        placeholders = ', '.join(['%s'] * len(fields))
                        insert_query = f"INSERT INTO stories ({', '.join(fields)}, created_at, updated_at) VALUES ({placeholders}, NOW(), NOW())"
                        cursor.execute(insert_query, values)
                        imported_count += 1
                        self.logger.debug(f"Imported story: {story_id}")
                    
                    # Import related data
                    self._import_story_relationships(cursor, story_id, story, existing is not None)
                    
                    # Commit transaction
                    connection.commit()
                    
                except Exception as e:
                    connection.rollback()
                    error_msg = f"Error importing story {story.get('id', 'Unknown')}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
                    self.logger.error(traceback.format_exc())
            
            # Update stats
            self.stats['stories_imported'] = imported_count
            self.stats['stories_updated'] = updated_count
            
            if errors:
                self.stats['errors'].extend(errors)
                self.logger.warning(f"Import completed with {len(errors)} errors")
            
            cursor.close()
            connection.close()
            
            self.logger.info(f"[OK] Successfully imported {imported_count} new stories, updated {updated_count} existing stories")
            return (imported_count + updated_count) > 0
            
        except Exception as e:
            self.logger.error(f"[ERROR] Database import failed: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.stats['errors'].append(f"Database import: {str(e)}")
            return False

    def _normalize_time_required(self, time_value: str) -> str:
        """Normalize time_required values to supported ENUM values"""
        if not time_value:
            return '15-minutes'  # Default value
        
        # Convert to lowercase for comparison
        time_lower = str(time_value).lower().strip()
        
        # Direct matches
        supported_values = self.config.get('supported_time_required_values', [])
        for supported in supported_values:
            if time_lower == supported.lower():
                return supported
        
        # Enhanced fuzzy matching for common variations (including spaces)
        time_mappings = {
            # Exact patterns with spaces
            '5 minutes': '5-minutes',
            '5 mins': '5-minutes',
            '7 minutes': '7-minutes',
            '7 mins': '7-minutes',
            '10 minutes': '10-minutes',
            '10 mins': '10-minutes',
            '15 minutes': '15-minutes',
            '15 mins': '15-minutes',
            '30 minutes': '30-minutes',
            '30 mins': '30-minutes',
            '45 minutes': '30-minutes',  # Round to nearest
            '45 mins': '30-minutes',     # Round to nearest
            '1 hour': '1-hour',
            '2 hours': '2-hours',
            '3 hours': '3-hours',
            '4 hours': '4-hours',
            '6 hours': '6-hours',
            '8 hours': '8-hours',
            '1 day': '1-day',
            '2 days': '2-days',
            '3 days': '3-days',
            '1 week': '1-week',
            '2 weeks': '2-weeks',
            '1 month': '1-month',
            
            # Compact patterns without spaces
            '5min': '5-minutes',
            '7min': '7-minutes',
            '10min': '10-minutes',
            '15min': '15-minutes',
            '30min': '30-minutes',
            '45min': '30-minutes',
            '45mins': '30-minutes',
            '1hr': '1-hour',
            '2hr': '2-hours',
            '3hr': '3-hours',
            '4hr': '4-hours',
            '6hr': '6-hours',
            '8hr': '8-hours',
            
            # Descriptive patterns
            'quick': 'quick-read',
            'fast': '5-minutes',
            'short': '10-minutes',
            'medium': '30-minutes',
            'long': '1-hour',
            'extended': '2-hours',
            'daily': '1-day',
            'weekly': '1-week',
            'monthly': '1-month',
            'weekend': '2-days',
            'practice': '30-minutes',
            'weekend practice': '2-days'
        }
        
        # First try exact matches
        if time_lower in time_mappings:
            return time_mappings[time_lower]
        
        # Then try pattern matching for partial matches
        for pattern, normalized in time_mappings.items():
            if pattern in time_lower:
                return normalized
        
        # Special handling for numeric patterns with regex-like matching
        import re
        
        # Match patterns like "5 min", "30 mins", "1 hr", "2 hours"
        minute_patterns = [
            (r'(\d+)\s*min(?:ute)?s?', lambda m: f"{m.group(1)}-minutes"),
            (r'(\d+)\s*hr?s?', lambda m: f"{m.group(1)}-hour" if m.group(1) == '1' else f"{m.group(1)}-hours"),
            (r'(\d+)\s*hour?s?', lambda m: f"{m.group(1)}-hour" if m.group(1) == '1' else f"{m.group(1)}-hours"),
            (r'(\d+)\s*day?s?', lambda m: f"{m.group(1)}-day" if m.group(1) == '1' else f"{m.group(1)}-days"),
            (r'(\d+)\s*week?s?', lambda m: f"{m.group(1)}-week" if m.group(1) == '1' else f"{m.group(1)}-weeks"),
            (r'(\d+)\s*month?s?', lambda m: f"{m.group(1)}-month" if m.group(1) == '1' else f"{m.group(1)}-months")
        ]
        
        for pattern, formatter in minute_patterns:
            match = re.search(pattern, time_lower)
            if match:
                result = formatter(match)
                # Validate that the result is in our supported values
                if result in supported_values:
                    return result
                # If not exact match, try to find closest supported value
                for supported in supported_values:
                    if result.replace('s', '') == supported or result + 's' == supported:
                        return supported
        
        # If no match found, log warning and return default
        self.logger.warning(f"Unknown time_required value '{time_value}', using default '15-minutes'")
        return '15-minutes'
    
    def _sanitise_database_value(self, value: Any) -> str:
        """Convert any value to database-safe string"""
        if value is None:
            return ""
        elif isinstance(value, (list, dict)):
            import json
            return json.dumps(value) if isinstance(value, dict) else '; '.join(str(item) for item in value)
        else:
            return str(value)

    def _import_story_relationships(self, cursor, story_id: str, story: Dict[str, Any], is_update: bool):
        """Import all related data for a story"""
        
        # If updating, clear existing relationships first
        if is_update:
            tables_to_clear = [
                'story_belt_levels', 'story_tags', 'story_sources', 'story_scores',
                'actionable_practices', 'discussion_prompts', 'learning_outcomes',
                'contrarian_viewpoints', 'risk_warnings', 'search_keywords',
                'family_discussion_points', 'story_teaching_activities',
                'story_age_translations', 'story_seasonal_challenges'
            ]
            
            for table in tables_to_clear:
                cursor.execute(f"DELETE FROM {table} WHERE story_id = %s", (story_id,))
        
        # Import belt levels
        belt_levels = story.get('belt_levels', [])
        for belt_name in belt_levels:
            cursor.execute("SELECT id FROM belt_levels WHERE name = %s", (belt_name,))
            belt_result = cursor.fetchone()
            if belt_result:
                cursor.execute(
                    "INSERT INTO story_belt_levels (story_id, belt_level_id) VALUES (%s, %s)",
                    (story_id, belt_result[0])
                )
        
        # Import tags
        tags_data = story.get('tags', {})
        all_tags = []
        if isinstance(tags_data, dict):
            all_tags.extend(tags_data.get('primary', []))
            all_tags.extend(tags_data.get('secondary', []))
            all_tags.extend(tags_data.get('trending', []))
        
        for tag_name in all_tags:
            # Get or create tag
            cursor.execute("SELECT id FROM tags WHERE name = %s", (tag_name,))
            tag_result = cursor.fetchone()
            
            if not tag_result:
                cursor.execute("INSERT INTO tags (name) VALUES (%s)", (tag_name,))
                tag_id = cursor.lastrowid
            else:
                tag_id = tag_result[0]
            
            cursor.execute(
                "INSERT INTO story_tags (story_id, tag_id) VALUES (%s, %s)",
                (story_id, tag_id)
            )
            
            # Update tag usage count
            cursor.execute("UPDATE tags SET usage_count = usage_count + 1 WHERE id = %s", (tag_id,))
        
        # Import source information
        source_data = story.get('source', {})
        if source_data:
            cursor.execute("""
                INSERT INTO story_sources
                (story_id, podcast_title, episode_title, episode_url, media_url,
                 episode_timestamp, host_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                story_id,
                source_data.get('podcast_title'),
                source_data.get('episode_title'),
                source_data.get('episode_url'),
                source_data.get('media_url'),
                source_data.get('timestamp'),
                source_data.get('host_name')
            ))
        
        # Import scores
        scoring_data = story.get('scoring', {})
        if scoring_data:
            cursor.execute("""
                INSERT INTO story_scores
                (story_id, curriculum_value, engagement_score, practical_score,
                 ai_innovation_score, belt_progression_xp, confidence_building,
                 family_impact, mastery_potential, viral_potential)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                story_id,
                scoring_data.get('curriculum_value'),
                scoring_data.get('engagement_score'),
                scoring_data.get('practical_score'),
                scoring_data.get('ai_innovation_score'),
                story.get('belt_progression_xp', 0),
                scoring_data.get('confidence_building'),
                scoring_data.get('family_impact'),
                scoring_data.get('mastery_potential'),
                scoring_data.get('viral_potential')
            ))
        
        # Import actionable practices
        practices = story.get('actionable_practices', [])
        for i, practice in enumerate(practices):
            if isinstance(practice, dict):
                practice_text = practice.get('practice', '')
            else:
                practice_text = str(practice)
            
            # Ensure practice_text is database-safe
            practice_text = self._sanitise_database_value(practice_text)
            
            cursor.execute("""
                INSERT INTO actionable_practices
                (story_id, practice, display_order)
                VALUES (%s, %s, %s)
            """, (story_id, practice_text, i))
        
        # Import discussion prompts
        prompts = story.get('discussion_prompts', [])
        for i, prompt in enumerate(prompts):
            if isinstance(prompt, dict):
                prompt_text = prompt.get('prompt', '')
            else:
                prompt_text = str(prompt)
            
            # Ensure prompt_text is database-safe
            prompt_text = self._sanitise_database_value(prompt_text)
            
            cursor.execute("""
                INSERT INTO discussion_prompts
                (story_id, prompt, display_order)
                VALUES (%s, %s, %s)
            """, (story_id, prompt_text, i))
        
        # Import learning outcomes
        outcomes = story.get('learning_outcomes', [])
        for i, outcome in enumerate(outcomes):
            if isinstance(outcome, dict):
                outcome_text = outcome.get('outcome', '')
            else:
                outcome_text = str(outcome)
            
            # Ensure outcome_text is database-safe
            outcome_text = self._sanitise_database_value(outcome_text)
            
            cursor.execute("""
                INSERT INTO learning_outcomes
                (story_id, outcome, display_order)
                VALUES (%s, %s, %s)
            """, (story_id, outcome_text, i))
        
        # Import contrarian viewpoints
        viewpoints = story.get('contrarian_viewpoints', [])
        for i, viewpoint in enumerate(viewpoints):
            if isinstance(viewpoint, dict):
                viewpoint_text = viewpoint.get('viewpoint', '')
            else:
                viewpoint_text = str(viewpoint)
            
            # Ensure viewpoint_text is database-safe
            viewpoint_text = self._sanitise_database_value(viewpoint_text)
            
            cursor.execute("""
                INSERT INTO contrarian_viewpoints
                (story_id, viewpoint, display_order)
                VALUES (%s, %s, %s)
            """, (story_id, viewpoint_text, i))
        
        # Import risk warnings
        warnings = story.get('risk_warnings', [])
        for i, warning in enumerate(warnings):
            if isinstance(warning, dict):
                warning_text = warning.get('warning', '')
            else:
                warning_text = str(warning)
            
            # Ensure warning_text is database-safe
            warning_text = self._sanitise_database_value(warning_text)
            
            cursor.execute("""
                INSERT INTO risk_warnings
                (story_id, warning, display_order)
                VALUES (%s, %s, %s)
            """, (story_id, warning_text, i))
        
        # Import search keywords
        keywords = story.get('search_keywords', [])
        for keyword_data in keywords:
            if isinstance(keyword_data, dict):
                keyword = keyword_data.get('keyword', '')
            else:
                keyword = str(keyword_data)
            
            # Ensure keyword is database-safe
            keyword = self._sanitise_database_value(keyword)
            
            cursor.execute("""
                INSERT INTO search_keywords
                (story_id, keyword)
                VALUES (%s, %s)
            """, (story_id, keyword))
        
        # Import family discussion points
        family_points = story.get('family_discussion_points', [])
        for i, point in enumerate(family_points):
            if isinstance(point, dict):
                point_text = point.get('topic', '')
            else:
                point_text = str(point)
            
            # Ensure point_text is database-safe
            point_text = self._sanitise_database_value(point_text)
            
            cursor.execute("""
                INSERT INTO family_discussion_points
                (story_id, point, display_order)
                VALUES (%s, %s, %s)
            """, (story_id, point_text, i))
        
        # Import teaching activities
        education_data = story.get('children_education_angle', {})
        if isinstance(education_data, dict):
            activities = education_data.get('teaching_activities', [])
            for i, activity in enumerate(activities):
                # Ensure activity is database-safe
                activity_text = self._sanitise_database_value(activity)
                
                cursor.execute("""
                    INSERT INTO story_teaching_activities
                    (story_id, activity, age_group, display_order)
                    VALUES (%s, %s, %s, %s)
                """, (story_id, activity_text, 'all', i))
            
            # Import age translations - ENHANCED WITH TYPE SAFETY
            age_concepts = education_data.get('age_appropriate_concepts', {})
            if isinstance(age_concepts, dict):
                for age_group, translation in age_concepts.items():
                    try:
                        # CRITICAL FIX: Handle complex data types
                        if isinstance(translation, list):
                            translation_text = '; '.join(str(item) for item in translation)
                        elif isinstance(translation, dict):
                            import json
                            translation_text = json.dumps(translation)
                        else:
                            translation_text = str(translation)
                        
                        cursor.execute("""
                            INSERT INTO story_age_translations
                            (story_id, age_group, translation, display_order)
                            VALUES (%s, %s, %s, %s)
                        """, (story_id, str(age_group), translation_text, 0))
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to import age translation for {story_id}: {str(e)}")
                        continue
        
        # Import seasonal challenges
        season_relevance = story.get('season_relevance', [])
        if isinstance(season_relevance, list):
            for season_type in season_relevance:
                # Check if season type exists
                cursor.execute("SELECT challenge_type FROM seasonal_challenges WHERE challenge_type = %s", (season_type,))
                if cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO story_seasonal_challenges
                        (story_id, season_type)
                        VALUES (%s, %s)
                    """, (story_id, season_type))
    
    def sync_to_production(self, stories: List[Dict[str, Any]]) -> bool:
        """Sync new stories to production database with validation checks"""
        try:
            # Check if we have minimum stories required for sync
            min_stories = self.config.get('min_stories_for_sync', 1)
            if len(stories) < min_stories:
                self.logger.warning(f"Only {len(stories)} stories generated, minimum {min_stories} required for production sync")
                return True  # Not an error, just skip sync
            
            # Step 1: Validate local database health
            if self.config.get('validation_checks', True):
                self.logger.info("[VALIDATE] Validating local database before production sync...")
                if not self._validate_local_database(stories):
                    self.logger.error("[ERROR] Local database validation failed - aborting production sync")
                    return False
                self.logger.info("[OK] Local database validation passed")
            
            # Step 2: Connect to production database
            self.logger.info("[SYNC] Connecting to production database...")
            import mysql.connector
            
            prod_connection = mysql.connector.connect(**self.config['production_database'])
            prod_cursor = prod_connection.cursor()
            
            self.logger.info("[OK] Connected to production database")
            
            # Step 3: Import stories to production
            imported_count = 0
            errors = []
            
            for story in stories:
                try:
                    # Use the same import logic as local database
                    prod_connection.start_transaction()
                    
                    story_id = story.get('id')
                    if not story_id:
                        continue
                    
                    # Check if story already exists in production
                    prod_cursor.execute("SELECT id FROM stories WHERE id = %s", (story_id,))
                    existing = prod_cursor.fetchone()
                    
                    # Prepare main story data (same as local import)
                    story_data = {
                        'id': story_id,
                        'title': story.get('title', '')[:500],
                        'summary': story.get('summary', ''),
                        'full_content': story.get('full_content', ''),
                        'curriculum_alignment': story.get('curriculum_alignment'),
                        'ai_skill_level': story.get('ai_skill_level'),
                        'ai_roi_potential': story.get('ai_roi_potential'),
                        'investment_domain_primary': story.get('investment_domain_primary'),
                        'difficulty_level': story.get('difficulty_level'),
                        'urgency': story.get('urgency'),
                        'concept_hierarchy_level': story.get('concept_hierarchy_level'),
                        'learning_sequence_position': story.get('learning_sequence_position'),
                        'experience_assumptions': story.get('experience_assumptions'),
                        'tech_savviness_required': story.get('tech_savviness_required'),
                        'expert_credentials': json.dumps(story.get('expert_credentials', {})) if story.get('expert_credentials') else None,
                        'track_record_mentions': story.get('track_record_mentions'),
                        'source_bias_assessment': json.dumps(story.get('source_bias_assessment', {})) if story.get('source_bias_assessment') else None,
                        'quote_highlight': story.get('quote_highlight'),
                        'family_security_relevance': json.dumps(story.get('family_security_relevance', {})) if isinstance(story.get('family_security_relevance'), dict) else story.get('family_security_relevance'),
                        'generational_wealth_relevance': json.dumps(story.get('generational_wealth_relevance', {})) if isinstance(story.get('generational_wealth_relevance'), dict) else story.get('generational_wealth_relevance'),
                        'children_education_angle': json.dumps(story.get('children_education_angle', {})) if story.get('children_education_angle') else None,
                        'emergency_fund_consideration': story.get('emergency_fund_consideration'),
                        'risk_level': story.get('risk_level'),
                        'time_required': self._normalize_time_required(story.get('time_required')),
                        'email_subject_line': story.get('email_subject_line', '')[:500],
                        'social_snippet': story.get('social_snippet', '')[:280],
                        'community_hook': story.get('community_hook'),
                        'app_hook': story.get('app_hook'),
                        'podcast_hook': story.get('podcast_hook'),
                        'financial_disclaimer': 1 if story.get('financial_disclaimer', True) else 0,
                        'dinner_table_readiness': story.get('family_engagement_metrics', {}).get('dinner_table_readiness'),
                        'estimated_read_time': story.get('performance_metrics', {}).get('estimated_read_time'),
                        'complexity_rating': story.get('performance_metrics', {}).get('complexity_rating'),
                        'retention_probability': story.get('performance_metrics', {}).get('retention_probability'),
                        'application_difficulty': story.get('performance_metrics', {}).get('application_difficulty'),
                        'confidence_building': story.get('scoring', {}).get('confidence_building'),
                        'family_impact': story.get('scoring', {}).get('family_impact'),
                        'mastery_potential': story.get('scoring', {}).get('mastery_potential'),
                        'viral_potential': story.get('scoring', {}).get('viral_potential')
                    }
                    
                    # Get content type ID
                    content_type = story.get('content_type', 'research-method')
                    prod_cursor.execute("SELECT id FROM content_types WHERE name = %s", (content_type,))
                    content_type_result = prod_cursor.fetchone()
                    
                    if not content_type_result:
                        # Create new content type if it doesn't exist
                        prod_cursor.execute(
                            "INSERT INTO content_types (name, description) VALUES (%s, %s)",
                            (content_type, f"Auto-created content type: {content_type}")
                        )
                        story_data['content_type_id'] = prod_cursor.lastrowid
                    else:
                        story_data['content_type_id'] = content_type_result[0]
                    
                    if existing:
                        # Update existing story
                        update_fields = []
                        update_values = []
                        for key, value in story_data.items():
                            if key != 'id':
                                update_fields.append(f"{key} = %s")
                                update_values.append(value)
                        
                        update_values.append(story_id)
                        update_query = f"UPDATE stories SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = %s"
                        prod_cursor.execute(update_query, update_values)
                        self.logger.debug(f"[OK] Production update: {story.get('title', 'Unknown')[:50]}...")
                    else:
                        # Insert new story to production
                        fields = list(story_data.keys())
                        values = list(story_data.values())
                        placeholders = ', '.join(['%s'] * len(fields))
                        insert_query = f"INSERT INTO stories ({', '.join(fields)}, created_at, updated_at) VALUES ({placeholders}, NOW(), NOW())"
                        prod_cursor.execute(insert_query, values)
                        imported_count += 1
                        self.logger.debug(f"[OK] Production sync: {story.get('title', 'Unknown')[:50]}...")
                    
                    # Import relationships
                    self._import_story_relationships(prod_cursor, story_id, story, existing is not None)
                    
                    prod_connection.commit()
                    
                except Exception as e:
                    prod_connection.rollback()
                    error_msg = f"Error syncing story {story.get('id', 'Unknown')} to production: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
            
            # Update stats
            self.stats['production_synced'] = imported_count
            self.stats['production_errors'] = len(errors)
            
            if errors:
                self.stats['errors'].extend(errors)
                self.logger.warning(f"Production sync completed with {len(errors)} errors")
            
            prod_cursor.close()
            prod_connection.close()
            
            if imported_count > 0:
                self.logger.info(f"[SUCCESS] Successfully synced {imported_count} stories to production!")
                return True
            else:
                self.logger.error("[ERROR] No stories were synced to production")
                return False
            
        except Exception as e:
            self.logger.error(f"[ERROR] Production sync failed: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.stats['errors'].append(f"Production sync: {str(e)}")
            return False
    
    def _validate_local_database(self, stories: List[Dict[str, Any]]) -> bool:
        """Validate that stories were properly imported to local database"""
        try:
            import mysql.connector
            
            # Connect to local database
            connection = mysql.connector.connect(**self.config['local_database'])
            cursor = connection.cursor()
            
            validation_passed = True
            
            # Check that all stories exist in local database
            for story in stories:
                story_id = story.get('id')
                if not story_id:
                    continue
                
                cursor.execute("SELECT id, title FROM stories WHERE id = %s", (story_id,))
                result = cursor.fetchone()
                
                if not result:
                    self.logger.error(f"[ERROR] Story not found in local database: {story_id}")
                    validation_passed = False
                else:
                    self.logger.debug(f"[OK] Validated local story: {result[1][:50]}...")
                    
                    # Validate relationships were created
                    self._validate_story_relationships(cursor, story_id)
            
            # Check database health
            cursor.execute("SELECT COUNT(*) FROM stories WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)")
            recent_count = cursor.fetchone()[0]
            
            if recent_count == 0:
                self.logger.warning("[WARNING] No stories created in local database in last 24 hours")
            else:
                self.logger.info(f"[OK] Local database health: {recent_count} stories in last 24 hours")
            
            cursor.close()
            connection.close()
            
            return validation_passed
            
        except Exception as e:
            self.logger.error(f"[ERROR] Local database validation error: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False
    
    def _validate_story_relationships(self, cursor, story_id: str):
        """Validate that relationships were properly created for a story"""
        try:
            # Check belt level relationships
            cursor.execute("SELECT COUNT(*) FROM story_belt_levels WHERE story_id = %s", (story_id,))
            belt_count = cursor.fetchone()[0]
            
            # Check tag relationships
            cursor.execute("SELECT COUNT(*) FROM story_tags WHERE story_id = %s", (story_id,))
            tag_count = cursor.fetchone()[0]
            
            # Check scoring data
            cursor.execute("SELECT COUNT(*) FROM story_scores WHERE story_id = %s", (story_id,))
            score_count = cursor.fetchone()[0]
            
            self.logger.debug(f"  [LINK] {story_id}: {belt_count} belts, {tag_count} tags, {score_count} scores")
            
            if belt_count == 0:
                warning_msg = f"Story {story_id} has no belt level relationships"
                self.stats['warnings'].append(warning_msg)
                self.logger.warning(warning_msg)
            
        except Exception as e:
            self.logger.warning(f"[WARNING] Relationship validation failed for {story_id}: {str(e)}")
    
    def _count_stories_in_database(self, db_config: Dict[str, str], stories: List[Dict[str, Any]]) -> int:
        """Count how many stories exist in the specified database"""
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()
            
            found_count = 0
            for story in stories:
                story_id = story.get('id')
                if story_id:
                    cursor.execute("SELECT id FROM stories WHERE id = %s", (story_id,))
                    if cursor.fetchone():
                        found_count += 1
            
            cursor.close()
            connection.close()
            
            return found_count
            
        except Exception as e:
            self.logger.error(f"Error counting stories in database: {str(e)}")
            return 0
    
    def generate_final_report(self, editorial_briefs: Optional[List[Dict[str, Any]]] = None):
        """Generate comprehensive automation report with Editorial Director analysis"""
        end_time = datetime.now()
        duration = end_time - self.stats['start_time']
        
        # Calculate success rates
        download_success_rate = (self.stats['episodes_downloaded'] / max(self.stats['episodes_found'], 1)) * 100
        generation_success_rate = (self.stats['stories_generated'] / max(self.stats['episodes_downloaded'], 1)) * 100
        local_import_success_rate = (self.stats['stories_imported'] / max(self.stats['stories_generated'], 1)) * 100
        production_sync_success_rate = (self.stats['production_synced'] / max(self.stats['stories_generated'], 1)) * 100
        
        report = {
            'automation_run': {
                'start_time': self.stats['start_time'].isoformat(),
                'end_time': end_time.isoformat(),
                'duration_minutes': duration.total_seconds() / 60,
                'success': len(self.stats['errors']) == 0
            },
            'processing_stats': {
                'rss_feeds_scanned': self.stats['feeds_processed'],
                'episodes_found': self.stats['episodes_found'],
                'episodes_downloaded': self.stats['episodes_downloaded'],
                'episodes_transcribed': self.stats['episodes_transcribed'],
                'stories_generated': self.stats['stories_generated'],
                'stories_imported': self.stats['stories_imported'],
                'stories_updated': self.stats['stories_updated'],
                'production_synced': self.stats['production_synced'],
                'production_errors': self.stats['production_errors'],
                'api_calls_made': self.stats['api_calls_made']
            },
            'success_rates': {
                'download_success': download_success_rate,
                'generation_success': generation_success_rate,
                'local_import_success': local_import_success_rate,
                'production_sync_success': production_sync_success_rate
            },
            'performance_metrics': self.stats['performance_metrics'],
            'quality_assessment': {
                'total_errors': len(self.stats['errors']),
                'total_warnings': len(self.stats['warnings']),
                'workflow_integrity': 'PASSED' if len(self.stats['errors']) == 0 else 'FAILED',
                'system_health': 'EXCELLENT' if len(self.stats['errors']) == 0 and all([
                    download_success_rate >= 80,
                    generation_success_rate >= 80,
                    local_import_success_rate >= 80,
                    production_sync_success_rate >= 80
                ]) else 'NEEDS_ATTENTION'
            },
            'errors': self.stats['errors'],
            'warnings': self.stats['warnings'],
            'configuration': {
                'batch_size': self.config['batch_size'],
                'ai_batch_size': self.config['ai_batch_size'],
                'days_back': self.config['days_back'],
                'rate_limits': self.config['rate_limits'],
                'sync_to_production': self.config.get('sync_to_production', False),
                'validation_checks': self.config.get('validation_checks', False)
            }
        }
        
        # Add Editorial Director analysis to report
        if 'editorial_analysis' in self.stats:
            report['editorial_director'] = self.stats['editorial_analysis']
            report['editorial_director']['editorial_briefs_used'] = len(editorial_briefs) if editorial_briefs else 0
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Path("logs") / f"automation_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Log comprehensive summary
        self.logger.info("[STATS] COMPLETE DAILY AUTOMATION REPORT")
        self.logger.info("=" * 60)
        self.logger.info(f"[STOPWATCH]  Duration: {duration.total_seconds()/60:.1f} minutes")
        self.logger.info(f"[SATELLITE_ANTENNA] RSS Feeds: {self.stats['feeds_processed']}")
        self.logger.info(f"[RADIO] Episodes Found: {self.stats['episodes_found']}")
        self.logger.info(f"[DOWNLOAD]  Episodes Downloaded: {self.stats['episodes_downloaded']} ({download_success_rate:.1f}% success)")
        self.logger.info(f"[TRANSCRIBE] Episodes Transcribed: {self.stats['episodes_transcribed']}")
        self.logger.info(f"[GENERATE]  Stories Generated: {self.stats['stories_generated']} ({generation_success_rate:.1f}% success)")
        self.logger.info(f"[IMPORT] Stories Imported: {self.stats['stories_imported']} ({local_import_success_rate:.1f}% success)")
        self.logger.info(f"🔄 Stories Updated: {self.stats['stories_updated']}")
        self.logger.info(f"[SYNC] Production Synced: {self.stats['production_synced']} ({production_sync_success_rate:.1f}% success)")
        self.logger.info(f"[WRENCH] API Calls Made: {self.stats['api_calls_made']}")
        self.logger.info(f"[ERROR] Total Errors: {len(self.stats['errors'])}")
        self.logger.info(f"[WARNING]  Total Warnings: {len(self.stats['warnings'])}")
        
        # Editorial Director Summary
        if 'editorial_analysis' in self.stats:
            editorial = self.stats['editorial_analysis']
            self.logger.info(f"\n[EDITORIAL] EDITORIAL DIRECTOR ANALYSIS:")
            self.logger.info(f"  [STATS] Transcripts Analyzed: {editorial['transcripts_analyzed']}")
            self.logger.info(f"  [EDITORIAL] Editorial Decisions: {editorial['editorial_decisions']}")
            self.logger.info(f"  [NOTE] Content Briefs Created: {editorial['content_briefs_created']}")
            self.logger.info(f"  ⭐ Average Content Quality: {editorial['average_content_quality']:.2f}/10")
            self.logger.info(f"  [GOLD] High-Quality Content: {editorial['high_quality_content_count']} pieces")
            if editorial['trending_themes']:
                themes = [theme['theme'] for theme in editorial['trending_themes'][:3]]
                self.logger.info(f"  [METRICS] Top Themes: {', '.join(themes)}")
        
        # Performance breakdown
        if self.stats['performance_metrics']:
            self.logger.info("\n[METRICS] PERFORMANCE BREAKDOWN:")
            for metric, value in self.stats['performance_metrics'].items():
                self.logger.info(f"  {metric}: {value:.2f}s")
        
        # Quality assessment
        overall_health = report['quality_assessment']['system_health']
        if overall_health == 'EXCELLENT':
            self.logger.info("\n[SUCCESS] QUALITY ASSESSMENT: EXCELLENT")
            self.logger.info("[OK] All workflow components operating optimally")
            self.logger.info("[OK] Enhanced automation system performing perfectly")
        else:
            self.logger.info("\n[WARNING] QUALITY ASSESSMENT: NEEDS ATTENTION")
            self.logger.info("[ERROR] Some issues detected - review errors and warnings")
        
        # Errors and warnings summary
        if self.stats['errors']:
            self.logger.error("\n🚨 CRITICAL ISSUES:")
            for i, error in enumerate(self.stats['errors'][:3], 1):
                self.logger.error(f"  {i}. {error}")
            if len(self.stats['errors']) > 3:
                self.logger.error(f"  ... and {len(self.stats['errors']) - 3} more errors")
        
        if self.stats['warnings']:
            self.logger.warning("\n[WARNING] WARNINGS:")
            for i, warning in enumerate(self.stats['warnings'][:3], 1):
                self.logger.warning(f"  {i}. {warning}")
            if len(self.stats['warnings']) > 3:
                self.logger.warning(f"  ... and {len(self.stats['warnings']) - 3} more warnings")
        
        self.logger.info(f"\n[REPORT] Full report saved: {report_file}")
        
        return report


def main():
    """Main entry point for daily automation"""
    print("COMPLETE DAILY AUTOMATION SYSTEM")
    print("=" * 60)
    print("InvestingDojo.co - End-to-End Content Generation")
    print()
    
    try:
        automation = CompleteDailyAutomation()
        success = automation.run_complete_automation()
        
        if success:
            print("\nAUTOMATION COMPLETED SUCCESSFULLY!")
            return True
        else:
            print("\nAUTOMATION FAILED!")
            return False
            
    except Exception as e:
        print(f"\nCRITICAL ERROR: {str(e)}")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)