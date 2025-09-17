#!/usr/bin/env python3
"""
LIMITED TEST AUTOMATION
Test the fixed automation with just a few RSS feeds

This is a test version of COMPLETE_DAILY_AUTOMATION.py with:
- Only 3 RSS feeds for faster testing
- Enhanced logging for debugging
- Same workflow as production version
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

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import our automation components
from automation.podcast_harvester import PodcastHarvester
from automation.story_generator import StoryGenerator
from automation.database_importer import DatabaseImporter

class LimitedTestAutomation:
    """Limited test version of the automation system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.logger = None
        self.stats = {
            'start_time': datetime.now(),
            'feeds_processed': 0,
            'episodes_found': 0,
            'episodes_downloaded': 0,
            'stories_generated': 0,
            'stories_imported': 0,
            'errors': []
        }
        
        # Configuration
        self.config = {
            'days_back': 2,  # Look back 2 days for more episodes
            'max_episodes': 5,  # Limit to 5 episodes for testing
            'batch_size': 2,  # Process 2 episodes at a time
            'database': {
                'host': 'localhost',
                'database': 'u219832816_investing_dojo',
                'user': 'u219832816_davethackeray',
                'password': 'ToTheM00n!',
                'charset': 'utf8mb4'
            }
        }
        
        # LIMITED RSS Feed URLs for testing (only 3 reliable feeds)
        self.rss_feeds = [
            "https://feeds.npr.org/510325/podcast.xml",  # Planet Money
            "https://video-api.wsj.com/podcast/rss/wsj/whats-news",  # WSJ What's News
            "https://rss.art19.com/forbes-daily-briefing"  # Forbes Daily Briefing
        ]
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"test_automation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🧪 TEST: Logging initialized - Log file: {log_file}")
    
    def run_complete_automation(self) -> bool:
        """Run the complete automation workflow with limited feeds"""
        try:
            self.logger.info("🧪 TEST: STARTING LIMITED AUTOMATION TEST")
            self.logger.info("=" * 60)
            
            # Step 1: Scan RSS feeds and find recent episodes
            self.logger.info("📡 STEP 1: Scanning RSS feeds for recent episodes")
            recent_episodes = self.scan_rss_feeds()
            
            if not recent_episodes:
                self.logger.warning("No recent episodes found - ending automation")
                return False
            
            # Limit episodes for testing
            if len(recent_episodes) > self.config['max_episodes']:
                recent_episodes = recent_episodes[:self.config['max_episodes']]
                self.logger.info(f"🧪 TEST: Limited to {len(recent_episodes)} episodes for testing")
            
            self.logger.info(f"Found {len(recent_episodes)} recent episodes")
            
            # Step 2: Download and compress MP3 files
            self.logger.info("⬇️ STEP 2: Downloading and compressing MP3 files")
            downloaded_episodes = self.download_and_compress_episodes(recent_episodes)
            
            if not downloaded_episodes:
                self.logger.error("No episodes downloaded successfully")
                return False
            
            self.logger.info(f"Successfully downloaded {len(downloaded_episodes)} episodes")
            
            # Step 3: Generate stories using AI
            self.logger.info("✍️ STEP 3: Generating stories using SuperPrompt")
            generated_stories = self.generate_stories_from_episodes(downloaded_episodes)
            
            if not generated_stories:
                self.logger.error("No stories generated successfully")
                return False
            
            self.logger.info(f"Successfully generated {len(generated_stories)} stories")
            
            # Step 4: Import stories to database
            self.logger.info("💾 STEP 4: Importing stories to database")
            import_success = self.import_stories_to_database(generated_stories)
            
            if not import_success:
                self.logger.error("Database import failed")
                return False
            
            # Step 5: Generate summary report
            self.generate_summary_report()
            
            self.logger.info("🎉 TEST: AUTOMATION COMPLETED SUCCESSFULLY!")
            return True
            
        except Exception as e:
            self.logger.error(f"💥 TEST: Automation failed with error: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.stats['errors'].append(f"Automation error: {str(e)}")
            return False
    
    def scan_rss_feeds(self) -> List[Dict[str, Any]]:
        """Scan RSS feeds for recent episodes"""
        try:
            harvester = PodcastHarvester(
                download_dir=self.project_root / "temp_processing"
            )
            
            recent_episodes = harvester.scan_rss_feeds(
                rss_urls=self.rss_feeds,
                days_back=self.config['days_back']
            )
            
            self.stats['feeds_processed'] = len(self.rss_feeds)
            self.stats['episodes_found'] = len(recent_episodes)
            
            return recent_episodes
            
        except Exception as e:
            self.logger.error(f"RSS scanning failed: {str(e)}")
            self.stats['errors'].append(f"RSS scanning: {str(e)}")
            return []
    
    def download_and_compress_episodes(self, episodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Download and compress episode MP3 files"""
        try:
            harvester = PodcastHarvester(
                download_dir=self.project_root / "temp_processing"
            )
            
            downloaded_episodes = harvester.download_and_compress_episodes(episodes)
            
            self.stats['episodes_downloaded'] = len(downloaded_episodes)
            
            return downloaded_episodes
            
        except Exception as e:
            self.logger.error(f"Download/compression failed: {str(e)}")
            self.stats['errors'].append(f"Download/compression: {str(e)}")
            return []
    
    def generate_stories_from_episodes(self, episodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate stories from episodes using AI"""
        try:
            # Check for API key
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                self.logger.error("GEMINI_API_KEY not found in environment variables")
                return []
            
            # Initialize story generator
            superprompt_path = self.project_root / "automation" / "SuperPrompt.md"
            generator = StoryGenerator(api_key, superprompt_path)
            
            # Generate stories in batches
            all_stories = generator.process_episodes_batch(
                episodes, 
                batch_size=self.config['batch_size']
            )
            
            self.stats['stories_generated'] = len(all_stories)
            
            return all_stories
            
        except Exception as e:
            self.logger.error(f"Story generation failed: {str(e)}")
            self.stats['errors'].append(f"Story generation: {str(e)}")
            return []
    
    def import_stories_to_database(self, stories: List[Dict[str, Any]]) -> bool:
        """Import generated stories to database using enhanced importer"""
        try:
            # Import the enhanced importer using importlib (file has hyphens in name)
            import importlib.util
            import_file = self.project_root / "automation" / "import-to-devEnvironment.py"
            spec = importlib.util.spec_from_file_location("import_to_devEnvironment", import_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            EnhancedContentImporter = module.EnhancedContentImporter
            
            # Create temporary JSON file with stories
            temp_file = Path("temp_processing") / f"test_stories_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            temp_file.parent.mkdir(exist_ok=True)
            
            # Format data for enhanced importer
            temp_data = {
                "investing-dojo-stories": stories
            }
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(temp_data, f, ensure_ascii=False, indent=2)
            
            # Use enhanced importer
            importer = EnhancedContentImporter(str(temp_file), dry_run=False)
            
            # Load and validate JSON
            if not importer.load_json():
                self.logger.error("Failed to load JSON data for import")
                return False
            
            # Connect to database
            if not importer.connect_to_database():
                self.logger.error("Failed to connect to database for import")
                return False
            
            # Import stories
            imported_count = 0
            errors = []
            
            for story in stories:
                try:
                    if importer.import_story(story):
                        imported_count += 1
                        self.logger.info(f"✅ Imported: {story.get('title', 'Unknown')[:50]}...")
                    else:
                        error_msg = f"Failed to import story: {story.get('title', 'Unknown')}"
                        errors.append(error_msg)
                        self.logger.warning(error_msg)
                except Exception as e:
                    error_msg = f"Error importing story {story.get('id', 'Unknown')}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
            
            # Update stats
            self.stats['stories_imported'] = imported_count
            
            if errors:
                self.stats['errors'].extend(errors)
                self.logger.warning(f"Import completed with {len(errors)} errors")
            
            # Clean up temp file
            try:
                temp_file.unlink()
            except:
                pass
            
            self.logger.info(f"✅ Successfully imported {imported_count} stories using enhanced importer")
            return imported_count > 0
            
        except Exception as e:
            self.logger.error(f"❌ Enhanced database import failed: {str(e)}")
            self.stats['errors'].append(f"Database import: {str(e)}")
            return False
    
    def generate_summary_report(self):
        """Generate and log summary report"""
        end_time = datetime.now()
        duration = end_time - self.stats['start_time']
        
        self.logger.info("=" * 60)
        self.logger.info("🧪 TEST AUTOMATION SUMMARY REPORT")
        self.logger.info("=" * 60)
        self.logger.info(f"⏱️  Duration: {duration}")
        self.logger.info(f"📡 RSS Feeds Processed: {self.stats['feeds_processed']}")
        self.logger.info(f"🎧 Episodes Found: {self.stats['episodes_found']}")
        self.logger.info(f"⬇️  Episodes Downloaded: {self.stats['episodes_downloaded']}")
        self.logger.info(f"✍️  Stories Generated: {self.stats['stories_generated']}")
        self.logger.info(f"💾 Stories Imported: {self.stats['stories_imported']}")
        self.logger.info(f"❌ Errors: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            self.logger.info("\n🚨 ERRORS ENCOUNTERED:")
            for i, error in enumerate(self.stats['errors'], 1):
                self.logger.info(f"  {i}. {error}")
        
        self.logger.info("=" * 60)

def main():
    """Main execution function"""
    print("🧪 LIMITED TEST AUTOMATION")
    print("=" * 60)
    print("Testing automation with limited RSS feeds")
    print()
    
    # Initialize automation
    automation = LimitedTestAutomation()
    automation.setup_logging()
    
    # Log initialization after logger is set up
    automation.logger.info(f"🧪 TEST: Initialized with {len(automation.rss_feeds)} RSS feeds (limited for testing)")
    
    # Run automation
    success = automation.run_complete_automation()
    
    if success:
        print("\n🎉 TEST COMPLETED SUCCESSFULLY!")
        print("Check the logs for detailed results.")
        return 0
    else:
        print("\n❌ TEST FAILED!")
        print("Check the logs for error details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())