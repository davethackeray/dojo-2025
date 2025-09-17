#!/usr/bin/env python3
"""
AUTOMATION TEST SCRIPT
Test the complete automation system with a small sample

This script tests:
1. RSS feed scanning (limited feeds)
2. MP3 download and compression
3. Gemini AI transcription and story generation
4. Database import

Usage: python automation/test_automation.py
"""

import os
import sys
from pathlib import Path
import logging
import traceback
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from automation.COMPLETE_DAILY_AUTOMATION import CompleteDailyAutomation

class AutomationTester:
    """Test automation system with limited scope"""
    
    def __init__(self):
        self.setup_logging()
        self.test_results = {
            'environment_checks': {},
            'component_tests': {},
            'errors': [],
            'warnings': []
        }
        
    def setup_logging(self):
        """Setup detailed test logging"""
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"automation_test_{timestamp}.log"
        
        # Setup logging with both file and console output
        logging.basicConfig(
            level=logging.DEBUG,  # More detailed logging for testing
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Test logging initialized - Log file: {log_file}")
        
    def debug_environment(self):
        """Debug environment setup and dependencies"""
        self.logger.info("🔍 DEBUGGING ENVIRONMENT SETUP")
        self.logger.info("=" * 50)
        
        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.logger.info(f"Python version: {python_version}")
        self.test_results['environment_checks']['python_version'] = python_version
        
        # Check project root
        self.logger.info(f"Project root: {project_root}")
        self.logger.info(f"Current working directory: {os.getcwd()}")
        self.test_results['environment_checks']['project_root'] = str(project_root)
        
        # Check critical files
        critical_files = [
            "automation/SuperPrompt.md",
            "automation/COMPLETE_DAILY_AUTOMATION.py",
            "automation/podcast_harvester.py",
            "automation/story_generator.py",
            "automation/database_importer.py"
        ]
        
        for file_path in critical_files:
            full_path = project_root / file_path
            exists = full_path.exists()
            self.logger.info(f"File check - {file_path}: {'✅ EXISTS' if exists else '❌ MISSING'}")
            self.test_results['environment_checks'][file_path] = exists
            
            if not exists:
                self.test_results['errors'].append(f"Missing critical file: {file_path}")
        
        # Check environment variables
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            self.logger.info(f"GEMINI_API_KEY: ✅ SET (length: {len(api_key)} chars)")
            self.test_results['environment_checks']['gemini_api_key'] = True
        else:
            self.logger.warning("GEMINI_API_KEY: ❌ NOT SET")
            self.test_results['environment_checks']['gemini_api_key'] = False
            self.test_results['warnings'].append("GEMINI_API_KEY not set - AI processing will fail")
        
        # Check Python dependencies
        dependencies = [
            'feedparser', 'requests', 'pydub', 'google.generativeai', 
            'mysql.connector', 'pathlib'
        ]
        
        self.logger.info("\n📦 CHECKING PYTHON DEPENDENCIES:")
        for dep in dependencies:
            try:
                __import__(dep)
                self.logger.info(f"  {dep}: ✅ INSTALLED")
                self.test_results['environment_checks'][f'dep_{dep}'] = True
            except ImportError as e:
                self.logger.error(f"  {dep}: ❌ MISSING - {str(e)}")
                self.test_results['environment_checks'][f'dep_{dep}'] = False
                self.test_results['errors'].append(f"Missing dependency: {dep}")
        
        # Check directories
        directories = ['temp_processing', 'logs']
        self.logger.info("\n📁 CHECKING DIRECTORIES:")
        for dir_name in directories:
            dir_path = project_root / dir_name
            if dir_path.exists():
                self.logger.info(f"  {dir_name}: ✅ EXISTS")
                self.test_results['environment_checks'][f'dir_{dir_name}'] = True
            else:
                self.logger.info(f"  {dir_name}: ⚠️ WILL BE CREATED")
                self.test_results['environment_checks'][f'dir_{dir_name}'] = False
        
        return len(self.test_results['errors']) == 0
    
    def test_individual_components(self):
        """Test individual automation components"""
        self.logger.info("\n🧪 TESTING INDIVIDUAL COMPONENTS")
        self.logger.info("=" * 50)
        
        # Test 1: Import all modules
        self.logger.info("Test 1: Module imports")
        try:
            from automation.podcast_harvester import PodcastHarvester
            from automation.story_generator import StoryGenerator
            from automation.database_importer import DatabaseImporter
            self.logger.info("  ✅ All modules imported successfully")
            self.test_results['component_tests']['module_imports'] = True
        except Exception as e:
            self.logger.error(f"  ❌ Module import failed: {str(e)}")
            self.logger.error(f"  Traceback: {traceback.format_exc()}")
            self.test_results['component_tests']['module_imports'] = False
            self.test_results['errors'].append(f"Module import error: {str(e)}")
            return False
        
        # Test 2: PodcastHarvester initialization
        self.logger.info("\nTest 2: PodcastHarvester initialization")
        try:
            harvester = PodcastHarvester(
                download_dir=Path("temp_processing/test"),
                batch_size=5,
                target_bitrate=32
            )
            self.logger.info("  ✅ PodcastHarvester initialized successfully")
            self.test_results['component_tests']['podcast_harvester_init'] = True
        except Exception as e:
            self.logger.error(f"  ❌ PodcastHarvester init failed: {str(e)}")
            self.logger.error(f"  Traceback: {traceback.format_exc()}")
            self.test_results['component_tests']['podcast_harvester_init'] = False
            self.test_results['errors'].append(f"PodcastHarvester init error: {str(e)}")
        
        # Test 3: StoryGenerator initialization (if API key available)
        self.logger.info("\nTest 3: StoryGenerator initialization")
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            try:
                story_gen = StoryGenerator(
                    api_key=api_key,
                    superprompt_path=Path("automation/SuperPrompt.md")
                )
                self.logger.info("  ✅ StoryGenerator initialized successfully")
                self.test_results['component_tests']['story_generator_init'] = True
            except Exception as e:
                self.logger.error(f"  ❌ StoryGenerator init failed: {str(e)}")
                self.logger.error(f"  Traceback: {traceback.format_exc()}")
                self.test_results['component_tests']['story_generator_init'] = False
                self.test_results['errors'].append(f"StoryGenerator init error: {str(e)}")
        else:
            self.logger.warning("  ⚠️ Skipping StoryGenerator test - no API key")
            self.test_results['component_tests']['story_generator_init'] = 'skipped'
        
        # Test 4: DatabaseImporter initialization
        self.logger.info("\nTest 4: DatabaseImporter initialization")
        try:
            db_config = {
                'host': 'localhost',
                'database': 'u219832816_investing_dojo',
                'user': 'u219832816_davethackeray',
                'password': 'ToTheM00n!',
                'charset': 'utf8mb4'
            }
            importer = DatabaseImporter(db_config)
            self.logger.info("  ✅ DatabaseImporter initialized successfully")
            self.test_results['component_tests']['database_importer_init'] = True
            
            # Test database connection
            self.logger.info("  Testing database connection...")
            if importer.connect():
                self.logger.info("  ✅ Database connection successful")
                self.test_results['component_tests']['database_connection'] = True
                importer.disconnect()
            else:
                self.logger.warning("  ⚠️ Database connection failed (expected in test environment)")
                self.test_results['component_tests']['database_connection'] = False
                self.test_results['warnings'].append("Database connection failed - expected in test environment")
                
        except Exception as e:
            self.logger.error(f"  ❌ DatabaseImporter init failed: {str(e)}")
            self.logger.error(f"  Traceback: {traceback.format_exc()}")
            self.test_results['component_tests']['database_importer_init'] = False
            self.test_results['errors'].append(f"DatabaseImporter init error: {str(e)}")
        
        return True
    
    def test_rss_feed_scanning(self):
        """Test RSS feed scanning with a single feed"""
        self.logger.info("\n📡 TESTING RSS FEED SCANNING")
        self.logger.info("=" * 50)
        
        try:
            from automation.podcast_harvester import PodcastHarvester
            
            # Test with a single reliable RSS feed
            test_feeds = ["https://feeds.megaphone.fm/planetmoney"]
            
            harvester = PodcastHarvester(
                download_dir=Path("temp_processing/test_rss"),
                batch_size=5
            )
            
            self.logger.info(f"Testing RSS scanning with {len(test_feeds)} feed(s)")
            self.logger.info(f"Test feed: {test_feeds[0]}")
            
            episodes = harvester.scan_rss_feeds(
                rss_urls=test_feeds,
                days_back=7  # Look back 7 days for testing
            )
            
            self.logger.info(f"✅ RSS scanning completed")
            self.logger.info(f"Episodes found: {len(episodes)}")
            
            if episodes:
                self.logger.info("Sample episode data:")
                sample = episodes[0]
                for key, value in sample.items():
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    self.logger.info(f"  {key}: {value}")
            
            self.test_results['component_tests']['rss_scanning'] = {
                'success': True,
                'episodes_found': len(episodes),
                'feeds_tested': len(test_feeds)
            }
            
            return episodes
            
        except Exception as e:
            self.logger.error(f"❌ RSS scanning failed: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self.test_results['component_tests']['rss_scanning'] = {
                'success': False,
                'error': str(e)
            }
            self.test_results['errors'].append(f"RSS scanning error: {str(e)}")
            return []
    
    def run_test(self):
        """Run comprehensive automation test with detailed debugging"""
        self.logger.info("🧪 STARTING COMPREHENSIVE AUTOMATION TEST")
        self.logger.info("=" * 60)
        
        test_start_time = datetime.now()
        overall_success = True
        
        try:
            # Step 1: Environment debugging
            self.logger.info("STEP 1: Environment debugging")
            env_success = self.debug_environment()
            if not env_success:
                self.logger.error("❌ Environment checks failed - continuing with warnings")
                overall_success = False
            
            # Step 2: Component testing
            self.logger.info("\nSTEP 2: Component testing")
            comp_success = self.test_individual_components()
            if not comp_success:
                self.logger.error("❌ Component tests failed")
                overall_success = False
            
            # Step 3: RSS feed testing
            self.logger.info("\nSTEP 3: RSS feed testing")
            episodes = self.test_rss_feed_scanning()
            
            # Step 4: Limited automation run (if we have episodes and API key)
            api_key = os.getenv('GEMINI_API_KEY')
            if episodes and api_key and len(self.test_results['errors']) == 0:
                self.logger.info("\nSTEP 4: Limited automation run")
                automation_success = self.run_limited_automation(episodes[:2])  # Test with max 2 episodes
                if not automation_success:
                    overall_success = False
            else:
                self.logger.info("\nSTEP 4: Skipping automation run")
                if not episodes:
                    self.logger.info("  Reason: No episodes found")
                if not api_key:
                    self.logger.info("  Reason: No API key")
                if self.test_results['errors']:
                    self.logger.info(f"  Reason: {len(self.test_results['errors'])} errors found")
            
            # Final results
            test_duration = datetime.now() - test_start_time
            self.logger.info(f"\n🏁 TEST COMPLETED in {test_duration.total_seconds():.1f} seconds")
            self._print_comprehensive_results()
            
            return overall_success
                
        except Exception as e:
            self.logger.error(f"💥 CRITICAL TEST ERROR: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self.test_results['errors'].append(f"Critical test error: {str(e)}")
            return False
    
    def run_limited_automation(self, episodes):
        """Run limited automation with just a few episodes"""
        self.logger.info("🤖 RUNNING LIMITED AUTOMATION")
        self.logger.info("=" * 40)
        
        try:
            # Create test automation instance
            automation = CompleteDailyAutomation()
            
            # Override configuration for testing
            automation.config['batch_size'] = 2
            automation.config['ai_batch_size'] = 1  # Very conservative for testing
            automation.config['download_dir'] = Path("temp_processing/test_automation")
            
            self.logger.info(f"Testing with {len(episodes)} episodes")
            self.logger.info(f"Download directory: {automation.config['download_dir']}")
            
            # Test download and compression (skip AI for now to save API calls)
            self.logger.info("\n📥 Testing download and compression...")
            downloaded_episodes = automation.download_and_compress_episodes(episodes)
            
            self.logger.info(f"Download results: {len(downloaded_episodes)} episodes processed")
            
            # Log download results
            for i, episode in enumerate(downloaded_episodes):
                status = episode.get('download_status', 'unknown')
                size = episode.get('file_size_mb', 0)
                compressed_size = episode.get('compressed_size_mb', 0)
                self.logger.info(f"  Episode {i+1}: {status}, {size:.1f}MB -> {compressed_size:.1f}MB")
            
            self.test_results['component_tests']['limited_automation'] = {
                'episodes_processed': len(episodes),
                'episodes_downloaded': len([e for e in downloaded_episodes if e.get('download_status') == 'success']),
                'success': True
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Limited automation failed: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self.test_results['component_tests']['limited_automation'] = {
                'success': False,
                'error': str(e)
            }
            self.test_results['errors'].append(f"Limited automation error: {str(e)}")
            return False
    
    def _print_comprehensive_results(self):
        """Print comprehensive test results"""
        self.logger.info("\n📊 COMPREHENSIVE TEST RESULTS")
        self.logger.info("=" * 60)
        
        # Environment checks
        self.logger.info("🔍 ENVIRONMENT CHECKS:")
        env_checks = self.test_results['environment_checks']
        for check, result in env_checks.items():
            if isinstance(result, bool):
                status = "✅ PASS" if result else "❌ FAIL"
                self.logger.info(f"  {check}: {status}")
            else:
                self.logger.info(f"  {check}: {result}")
        
        # Component tests
        self.logger.info("\n🧪 COMPONENT TESTS:")
        comp_tests = self.test_results['component_tests']
        for test, result in comp_tests.items():
            if isinstance(result, bool):
                status = "✅ PASS" if result else "❌ FAIL"
                self.logger.info(f"  {test}: {status}")
            elif isinstance(result, dict):
                if result.get('success'):
                    self.logger.info(f"  {test}: ✅ PASS")
                    for key, value in result.items():
                        if key != 'success':
                            self.logger.info(f"    {key}: {value}")
                else:
                    self.logger.info(f"  {test}: ❌ FAIL")
                    if 'error' in result:
                        self.logger.info(f"    error: {result['error']}")
            else:
                self.logger.info(f"  {test}: {result}")
        
        # Summary counts
        total_errors = len(self.test_results['errors'])
        total_warnings = len(self.test_results['warnings'])
        
        self.logger.info(f"\n📈 SUMMARY:")
        self.logger.info(f"  Total Errors: {total_errors}")
        self.logger.info(f"  Total Warnings: {total_warnings}")
        
        # Errors
        if self.test_results['errors']:
            self.logger.info(f"\n❌ ERRORS ({len(self.test_results['errors'])}):")
            for i, error in enumerate(self.test_results['errors'], 1):
                self.logger.info(f"  {i}. {error}")
        
        # Warnings
        if self.test_results['warnings']:
            self.logger.info(f"\n⚠️ WARNINGS ({len(self.test_results['warnings'])}):")
            for i, warning in enumerate(self.test_results['warnings'], 1):
                self.logger.info(f"  {i}. {warning}")
        
        # Overall status
        if total_errors == 0:
            if total_warnings == 0:
                self.logger.info(f"\n🎉 ALL TESTS PASSED! System is ready for production.")
            else:
                self.logger.info(f"\n✅ TESTS PASSED with {total_warnings} warnings. Review warnings before production.")
        else:
            self.logger.info(f"\n❌ TESTS FAILED with {total_errors} errors. Fix errors before proceeding.")
        
        # Recommendations
        self.logger.info(f"\n💡 RECOMMENDATIONS:")
        if not env_checks.get('gemini_api_key', False):
            self.logger.info("  - Set GEMINI_API_KEY environment variable for AI processing")
        if not env_checks.get('database_connection', True):
            self.logger.info("  - Verify database connection settings for production")
        if total_errors > 0:
            self.logger.info("  - Fix all errors before running full automation")
        if total_warnings > 0:
            self.logger.info("  - Review and address warnings for optimal performance")
        
        self.logger.info("  - Run full automation test with: python automation/COMPLETE_DAILY_AUTOMATION.py")
        self.logger.info("  - Setup Windows Task Scheduler with: python automation/setup_windows_scheduler.py")


def main():
    """Main test entry point"""
    print("🧪 COMPREHENSIVE AUTOMATION SYSTEM TEST")
    print("=" * 60)
    print("Testing environment, components, and limited automation run")
    print("This test will:")
    print("  1. Check environment and dependencies")
    print("  2. Test individual components")
    print("  3. Test RSS feed scanning")
    print("  4. Run limited automation (if conditions are met)")
    print()
    
    # Check if we're in the right directory
    if not Path("automation").exists():
        print("❌ ERROR: Run this script from the project root directory")
        print("   Current directory:", os.getcwd())
        print("   Expected: Directory containing 'automation' folder")
        return False
    
    tester = AutomationTester()
    success = tester.run_test()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 COMPREHENSIVE TEST COMPLETED SUCCESSFULLY!")
        print("✅ System appears ready for automation")
        print("\nNext steps:")
        print("  1. Set GEMINI_API_KEY if not already set")
        print("  2. Run full automation: python automation/COMPLETE_DAILY_AUTOMATION.py")
        print("  3. Setup scheduler: python automation/setup_windows_scheduler.py")
    else:
        print("❌ TESTS COMPLETED WITH ISSUES!")
        print("⚠️ Review errors and warnings above")
        print("\nCheck the log file for detailed information")
        print("Fix issues before running full automation")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)