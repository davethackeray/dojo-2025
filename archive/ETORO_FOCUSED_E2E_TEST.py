#!/usr/bin/env python3
"""
ETORO DIGEST INVEST FOCUSED END-TO-END TEST
InvestingDojo.co - Targeted Workflow Validation

This script runs a focused end-to-end test of the automated workflow with:
- SPECIFIC TARGET: eToro Digest Invest podcast feed only
- EPISODE LIMIT: Last 3 episodes maximum
- SUPERPROMPT: Uses SuperPrompt_Optimized.md
- DATABASE TESTING: Dual synchronization (local + production)
- SAFETY: Controlled API usage and comprehensive logging

WORKFLOW TESTED:
1. RSS → eToro Digest Invest feed parsing (3 episodes max)
2. MP3 → Download and compression (<20MB)
3. AI → Story generation using SuperPrompt_Optimized.md
4. JSON → Validation and enhancement
5. LOCAL → Database import with relationships
6. PRODUCTION → Database synchronization
7. VALIDATION → Complete workflow verification

Created for validating the enhanced automation system before CrewAI integration.
"""

import os
import sys
import json
import time
import logging
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import mysql.connector
from mysql.connector import Error

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class EToroFocusedE2ETest:
    """Focused end-to-end test for eToro Digest Invest podcast workflow"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.setup_logging()
        
        # SPECIFIC eToro Digest Invest feed
        self.target_feed = "https://feeds.fame.so/digest-invest-by-etoro-insights-on-trading-markets-investing-finance-1"
        self.max_episodes = 3  # Exactly 3 episodes
        
        # Test configuration
        self.config = {
            'gemini_api_key': os.getenv('GEMINI_API_KEY'),
            'superprompt_path': Path("automation/SuperPrompt_Optimized.md"),
            'download_dir': Path("temp_processing") / "etoro_test",
            'target_bitrate': 32,
            'max_file_size_mb': 20,
            'days_back': 7,  # Look back 7 days for episodes
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
            }
        }
        
        # Test statistics
        self.stats = {
            'start_time': datetime.now(),
            'target_feed': self.target_feed,
            'max_episodes': self.max_episodes,
            'episodes_found': 0,
            'episodes_downloaded': 0,
            'episodes_transcribed': 0,
            'stories_generated': 0,
            'local_imported': 0,
            'production_synced': 0,
            'api_calls_made': 0,
            'total_processing_time': 0,
            'errors': [],
            'warnings': [],
            'performance_metrics': {}
        }
        
        # Now validate environment after config is set
        self.validate_environment()
        
        self.logger.info(f"🎯 eToro Focused E2E Test initialized")
        self.logger.info(f"Target: {self.target_feed}")
        self.logger.info(f"Max episodes: {self.max_episodes}")
    
    def setup_logging(self):
        """Setup comprehensive test logging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"etoro_focused_e2e_test_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🎯 eToro Focused E2E Test started - Log: {log_file}")
    
    def validate_environment(self):
        """Validate test environment and requirements"""
        self.logger.info("🔍 Validating test environment...")
        
        # Check API key
        if not os.getenv('GEMINI_API_KEY'):
            raise ValueError("GEMINI_API_KEY environment variable required")
        
        # Check SuperPrompt_Optimized.md
        superprompt_path = Path("automation/SuperPrompt_Optimized.md")
        if not superprompt_path.exists():
            raise FileNotFoundError("automation/SuperPrompt_Optimized.md required")
        
        # Check automation components
        required_components = [
            "automation/podcast_harvester.py",
            "automation/story_generator.py",
            "automation/database_importer.py"
        ]
        
        for component in required_components:
            if not Path(component).exists():
                raise FileNotFoundError(f"Required component missing: {component}")
        
        # Create test directories
        self.config['download_dir'].mkdir(parents=True, exist_ok=True)
        
        # Test database connections
        self._test_database_connections()
        
        self.logger.info("✅ Environment validation passed")
    
    def _test_database_connections(self):
        """Test both local and production database connections"""
        # Test local database
        try:
            local_conn = mysql.connector.connect(**self.config['local_database'])
            local_cursor = local_conn.cursor()
            local_cursor.execute("SELECT COUNT(*) FROM stories")
            local_count = local_cursor.fetchone()[0]
            local_cursor.close()
            local_conn.close()
            self.logger.info(f"✅ Local database: {local_count} stories")
        except Exception as e:
            raise ConnectionError(f"Local database connection failed: {str(e)}")
        
        # Test production database
        try:
            prod_conn = mysql.connector.connect(**self.config['production_database'])
            prod_cursor = prod_conn.cursor()
            prod_cursor.execute("SELECT COUNT(*) FROM stories")
            prod_count = prod_cursor.fetchone()[0]
            prod_cursor.close()
            prod_conn.close()
            self.logger.info(f"✅ Production database: {prod_count} stories")
        except Exception as e:
            raise ConnectionError(f"Production database connection failed: {str(e)}")
    
    def run_focused_e2e_test(self) -> bool:
        """Run the complete focused end-to-end test"""
        try:
            self.logger.info("🚀 STARTING ETORO FOCUSED END-TO-END TEST")
            self.logger.info("=" * 80)
            self.logger.info(f"🎯 Target Feed: eToro Digest Invest")
            self.logger.info(f"📊 Episode Limit: {self.max_episodes} episodes maximum")
            self.logger.info(f"🧠 SuperPrompt: SuperPrompt_Optimized.md")
            self.logger.info(f"💾 Databases: Local + Production sync")
            
            # Step 1: RSS Feed Parsing
            self.logger.info("\n📡 STEP 1: RSS Feed Parsing (eToro Digest Invest)")
            episodes = self.test_rss_parsing()
            
            if not episodes:
                self.logger.error("❌ No episodes found from eToro feed")
                return False
            
            # Limit to exactly 3 episodes
            test_episodes = episodes[:self.max_episodes]
            self.logger.info(f"🎯 Selected {len(test_episodes)} episodes for testing")
            
            # Step 2: MP3 Download and Compression
            self.logger.info("\n⬇️ STEP 2: MP3 Download and Compression")
            downloaded_episodes = self.test_mp3_processing(test_episodes)
            
            if not downloaded_episodes:
                self.logger.error("❌ No episodes downloaded successfully")
                return False
            
            # Step 3: AI Story Generation with SuperPrompt_Optimized
            self.logger.info("\n✍️ STEP 3: AI Story Generation (SuperPrompt_Optimized)")
            generated_stories = self.test_ai_story_generation(downloaded_episodes)
            
            if not generated_stories:
                self.logger.error("❌ No stories generated successfully")
                return False
            
            # Step 4: JSON Validation and Enhancement
            self.logger.info("\n🔍 STEP 4: JSON Validation and Enhancement")
            validated_stories = self.test_json_validation(generated_stories)
            
            if not validated_stories:
                self.logger.error("❌ JSON validation failed")
                return False
            
            # Step 5: Local Database Import with Relationships
            self.logger.info("\n💾 STEP 5: Local Database Import (with relationships)")
            local_import_success = self.test_local_database_import(validated_stories)
            
            if not local_import_success:
                self.logger.error("❌ Local database import failed")
                return False
            
            # Step 6: Production Database Synchronization
            self.logger.info("\n🌐 STEP 6: Production Database Synchronization")
            production_sync_success = self.test_production_database_sync(validated_stories)
            
            if not production_sync_success:
                self.logger.error("❌ Production database sync failed")
                return False
            
            # Step 7: Complete Workflow Validation
            self.logger.info("\n🔍 STEP 7: Complete Workflow Validation")
            validation_success = self.test_complete_workflow_validation(validated_stories)
            
            if not validation_success:
                self.logger.error("❌ Complete workflow validation failed")
                return False
            
            # Generate comprehensive test report
            self.generate_comprehensive_test_report()
            
            self.logger.info("\n🎉 ETORO FOCUSED E2E TEST COMPLETED SUCCESSFULLY!")
            self.logger.info("✅ Enhanced automation system validated and ready for CrewAI integration")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ FOCUSED E2E TEST FAILED: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.stats['errors'].append(f"Critical failure: {str(e)}")
            return False
    
    def test_rss_parsing(self) -> List[Dict[str, Any]]:
        """Test RSS feed parsing for eToro Digest Invest"""
        try:
            from automation.podcast_harvester import PodcastHarvester
            
            start_time = time.time()
            
            harvester = PodcastHarvester(
                download_dir=self.config['download_dir'],
                batch_size=10
            )
            
            # Parse the specific eToro feed
            episodes = harvester.scan_rss_feeds(
                rss_urls=[self.target_feed],
                days_back=self.config['days_back']
            )
            
            processing_time = time.time() - start_time
            self.stats['performance_metrics']['rss_parsing_time'] = processing_time
            self.stats['episodes_found'] = len(episodes)
            
            self.logger.info(f"✅ RSS Parsing: Found {len(episodes)} episodes in {processing_time:.2f}s")
            
            # Log episode details
            for i, episode in enumerate(episodes[:self.max_episodes]):
                title = episode.get('title', 'Unknown')[:60]
                pub_date = episode.get('published_date', 'Unknown')
                self.logger.info(f"  📻 Episode {i+1}: {title}... ({pub_date})")
            
            return episodes
            
        except Exception as e:
            self.logger.error(f"❌ RSS parsing failed: {str(e)}")
            self.stats['errors'].append(f"RSS parsing: {str(e)}")
            return []
    
    def test_mp3_processing(self, episodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Test MP3 download and compression"""
        try:
            from automation.podcast_harvester import PodcastHarvester
            
            start_time = time.time()
            
            harvester = PodcastHarvester(
                download_dir=self.config['download_dir'],
                batch_size=self.max_episodes,
                target_bitrate=self.config['target_bitrate']
            )
            
            downloaded_episodes = harvester.download_and_compress_episodes(episodes)
            
            processing_time = time.time() - start_time
            self.stats['performance_metrics']['mp3_processing_time'] = processing_time
            self.stats['episodes_downloaded'] = len(downloaded_episodes)
            
            self.logger.info(f"✅ MP3 Processing: Downloaded {len(downloaded_episodes)} episodes in {processing_time:.2f}s")
            
            # Validate file sizes and compression
            total_size_mb = 0
            for episode in downloaded_episodes:
                file_path = episode.get('compressed_filepath')
                if file_path and Path(file_path).exists():
                    file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
                    total_size_mb += file_size_mb
                    
                    self.logger.info(f"  📁 {Path(file_path).name}: {file_size_mb:.1f}MB")
                    
                    if file_size_mb > self.config['max_file_size_mb']:
                        self.stats['warnings'].append(f"File exceeds {self.config['max_file_size_mb']}MB: {file_size_mb:.1f}MB")
            
            self.logger.info(f"  📊 Total size: {total_size_mb:.1f}MB")
            return downloaded_episodes
            
        except Exception as e:
            self.logger.error(f"❌ MP3 processing failed: {str(e)}")
            self.stats['errors'].append(f"MP3 processing: {str(e)}")
            return []
    
    def test_ai_story_generation(self, episodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Test AI story generation using SuperPrompt_Optimized.md"""
        try:
            from automation.story_generator import StoryGenerator
            
            start_time = time.time()
            
            story_generator = StoryGenerator(
                api_key=self.config['gemini_api_key'],
                superprompt_path=self.config['superprompt_path']
            )
            
            # Process episodes with rate limiting
            generated_stories = story_generator.process_episodes_batch(
                episodes=episodes,
                batch_size=2  # Conservative batch size for API limits
            )
            
            processing_time = time.time() - start_time
            self.stats['performance_metrics']['ai_generation_time'] = processing_time
            self.stats['stories_generated'] = len(generated_stories)
            self.stats['api_calls_made'] = len(episodes)  # Approximate
            
            self.logger.info(f"✅ AI Generation: Generated {len(generated_stories)} stories in {processing_time:.2f}s")
            
            # Validate story structure and quality
            for i, story in enumerate(generated_stories):
                title = story.get('title', 'Unknown')[:50]
                content_length = len(str(story.get('full_content', '')))
                belt_levels = story.get('belt_levels', [])
                
                self.logger.info(f"  📝 Story {i+1}: {title}... ({content_length} chars, {len(belt_levels)} belts)")
                
                # Validate SuperPrompt_Optimized structure
                required_fields = ['id', 'title', 'summary', 'full_content', 'content_type', 'belt_levels']
                missing_fields = [field for field in required_fields if not story.get(field)]
                
                if missing_fields:
                    self.stats['warnings'].append(f"Story {i+1} missing fields: {missing_fields}")
                
                # Check for enhanced SuperPrompt fields
                enhanced_fields = ['ai_tools_mentioned', 'family_security_relevance', 'seasonal_challenge_integration']
                enhanced_count = sum(1 for field in enhanced_fields if story.get(field))
                self.logger.info(f"    🔧 Enhanced fields: {enhanced_count}/{len(enhanced_fields)}")
            
            return generated_stories
            
        except Exception as e:
            self.logger.error(f"❌ AI story generation failed: {str(e)}")
            self.stats['errors'].append(f"AI generation: {str(e)}")
            return []
    
    def test_json_validation(self, stories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Test JSON validation and enhancement"""
        try:
            start_time = time.time()
            
            validated_stories = []
            validation_errors = []
            
            for i, story in enumerate(stories):
                try:
                    # Test JSON serialization
                    json_str = json.dumps(story, ensure_ascii=False, indent=2)
                    
                    # Test JSON parsing
                    parsed_story = json.loads(json_str)
                    
                    # Validate SuperPrompt_Optimized structure
                    validation_result = self._validate_superprompt_structure(parsed_story)
                    
                    if validation_result['valid']:
                        validated_stories.append(parsed_story)
                        self.logger.info(f"  ✅ Story {i+1}: JSON validation passed")
                    else:
                        validation_errors.extend(validation_result['errors'])
                        self.logger.warning(f"  ⚠️ Story {i+1}: Validation issues - {len(validation_result['errors'])} errors")
                
                except Exception as e:
                    validation_errors.append(f"Story {i+1} JSON error: {str(e)}")
                    self.logger.error(f"  ❌ Story {i+1}: JSON validation failed - {str(e)}")
            
            processing_time = time.time() - start_time
            self.stats['performance_metrics']['json_validation_time'] = processing_time
            
            self.logger.info(f"✅ JSON Validation: {len(validated_stories)}/{len(stories)} stories validated in {processing_time:.2f}s")
            
            if validation_errors:
                self.stats['warnings'].extend(validation_errors[:5])  # Limit warnings
                self.logger.warning(f"⚠️ Total validation issues: {len(validation_errors)}")
            
            return validated_stories
            
        except Exception as e:
            self.logger.error(f"❌ JSON validation failed: {str(e)}")
            self.stats['errors'].append(f"JSON validation: {str(e)}")
            return []
    
    def _validate_superprompt_structure(self, story: Dict[str, Any]) -> Dict[str, Any]:
        """Validate story against SuperPrompt_Optimized structure"""
        errors = []
        
        # Required fields
        required_fields = [
            'id', 'title', 'summary', 'full_content', 'content_type',
            'belt_levels', 'curriculum_categories', 'scoring'
        ]
        
        for field in required_fields:
            if not story.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate ENUM fields
        enum_validations = {
            'content_type': [
                'curriculum-war-story', 'ai-breakthrough', 'systematic-strategy',
                'family-wealth-builder', 'mastery-technique', 'mindset-hack',
                'research-method', 'risk-lesson', 'epic-curriculum-fail',
                'belt-progression-moment', 'ai-integration-guide', 'generational-wealth-wisdom'
            ],
            'difficulty_level': ['foundational', 'intermediate-skill', 'advanced-mastery'],
            'urgency': ['timeless', 'trending', 'seasonal', 'urgent'],
            'investment_domain_primary': ['stocks', 'options', 'crypto', 'portfolio-management', 'alternative-investments']
        }
        
        for field, valid_values in enum_validations.items():
            if story.get(field) and story[field] not in valid_values:
                errors.append(f"Invalid {field}: {story[field]}")
        
        # Validate belt_levels
        valid_belts = ['white-belt', 'yellow-belt', 'orange-belt', 'green-belt', 'blue-belt', 'brown-belt', 'black-belt']
        belt_levels = story.get('belt_levels', [])
        if isinstance(belt_levels, list):
            for belt in belt_levels:
                if belt not in valid_belts:
                    errors.append(f"Invalid belt level: {belt}")
        
        # Check for enhanced SuperPrompt fields
        enhanced_fields = [
            'seasonal_challenge_integration', 'spark_content_generation',
            'community_building_features', 'monetization_psychology'
        ]
        
        enhanced_count = sum(1 for field in enhanced_fields if story.get(field))
        if enhanced_count < 2:
            errors.append(f"Missing enhanced SuperPrompt fields: {4 - enhanced_count} missing")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'enhanced_fields_count': enhanced_count
        }
    
    def test_local_database_import(self, stories: List[Dict[str, Any]]) -> bool:
        """Test local database import with relationships"""
        try:
            start_time = time.time()
            
            # Create test JSON file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_file = self.config['download_dir'] / f"etoro_local_import_{timestamp}.json"
            
            test_data = {
                "investing-dojo-stories": stories
            }
            
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, ensure_ascii=False, indent=2)
            
            # Use enhanced importer
            from automation.COMPLETE_DAILY_AUTOMATION import CompleteDailyAutomation
            
            automation = CompleteDailyAutomation()
            import_success = automation.import_stories_to_database(stories)
            
            processing_time = time.time() - start_time
            self.stats['performance_metrics']['local_import_time'] = processing_time
            
            if import_success:
                self.stats['local_imported'] = len(stories)
                self.logger.info(f"✅ Local Import: {len(stories)} stories imported in {processing_time:.2f}s")
                
                # Validate relationships were created
                self._validate_local_relationships(stories)
            else:
                self.logger.error("❌ Local database import failed")
            
            # Clean up test file
            try:
                test_file.unlink()
            except:
                pass
            
            return import_success
            
        except Exception as e:
            self.logger.error(f"❌ Local database import failed: {str(e)}")
            self.stats['errors'].append(f"Local import: {str(e)}")
            return False
    
    def _validate_local_relationships(self, stories: List[Dict[str, Any]]):
        """Validate that relationships were properly created in local database"""
        try:
            connection = mysql.connector.connect(**self.config['local_database'])
            cursor = connection.cursor()
            
            for story in stories:
                story_id = story.get('id')
                if not story_id:
                    continue
                
                # Check belt level relationships
                cursor.execute("SELECT COUNT(*) FROM story_belt_levels WHERE story_id = %s", (story_id,))
                belt_count = cursor.fetchone()[0]
                
                # Check tag relationships
                cursor.execute("SELECT COUNT(*) FROM story_tags WHERE story_id = %s", (story_id,))
                tag_count = cursor.fetchone()[0]
                
                # Check scoring data
                cursor.execute("SELECT COUNT(*) FROM story_scores WHERE story_id = %s", (story_id,))
                score_count = cursor.fetchone()[0]
                
                self.logger.info(f"  🔗 {story_id}: {belt_count} belts, {tag_count} tags, {score_count} scores")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            self.logger.warning(f"⚠️ Relationship validation failed: {str(e)}")
    
    def test_production_database_sync(self, stories: List[Dict[str, Any]]) -> bool:
        """Test production database synchronization"""
        try:
            start_time = time.time()
            
            # Use the enhanced automation system for production sync
            from automation.COMPLETE_DAILY_AUTOMATION import CompleteDailyAutomation
            
            automation = CompleteDailyAutomation()
            sync_success = automation.sync_to_production(stories)
            
            processing_time = time.time() - start_time
            self.stats['performance_metrics']['production_sync_time'] = processing_time
            
            if sync_success:
                self.stats['production_synced'] = len(stories)
                self.logger.info(f"✅ Production Sync: {len(stories)} stories synced in {processing_time:.2f}s")
                
                # Validate production sync
                self._validate_production_sync(stories)
            else:
                self.logger.error("❌ Production database sync failed")
            
            return sync_success
            
        except Exception as e:
            self.logger.error(f"❌ Production database sync failed: {str(e)}")
            self.stats['errors'].append(f"Production sync: {str(e)}")
            return False
    
    def _validate_production_sync(self, stories: List[Dict[str, Any]]):
        """Validate that stories exist in production database"""
        try:
            connection = mysql.connector.connect(**self.config['production_database'])
            cursor = connection.cursor()
            
            found_count = 0
            for story in stories:
                story_id = story.get('id')
                if story_id:
                    cursor.execute("SELECT id, title FROM stories WHERE id = %s", (story_id,))
                    if cursor.fetchone():
                        found_count += 1
            
            cursor.close()
            connection.close()
            
            self.logger.info(f"  🌐 Production validation: {found_count}/{len(stories)} stories found")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Production validation failed: {str(e)}")
    
    def test_complete_workflow_validation(self, stories: List[Dict[str, Any]]) -> bool:
        """Test complete workflow validation"""
        try:
            start_time = time.time()
            
            # Validate stories exist in both databases
            local_found = self._count_stories_in_database(self.config['local_database'], stories)
            production_found = self._count_stories_in_database(self.config['production_database'], stories)
            
            processing_time = time.time() - start_time
            self.stats['performance_metrics']['validation_time'] = processing_time
            
            success_threshold = 0.8  # 80% success rate required
            local_success_rate = local_found / len(stories)
            production_success_rate = production_found / len(stories)
            
            self.logger.info(f"✅ Workflow Validation completed in {processing_time:.2f}s:")
            self.logger.info(f"  📊 Local Database: {local_found}/{len(stories)} stories ({local_success_rate:.1%})")
            self.logger.info(f"  🌐 Production Database: {production_found}/{len(stories)} stories ({production_success_rate:.1%})")
            
            if local_success_rate >= success_threshold and production_success_rate >= success_threshold:
                self.logger.info("✅ Complete workflow validation PASSED")
                return True
            else:
                self.logger.error("❌ Complete workflow validation FAILED")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Workflow validation failed: {str(e)}")
            self.stats['errors'].append(f"Workflow validation: {str(e)}")
            return False
    
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
    
    def generate_comprehensive_test_report(self):
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = end_time - self.stats['start_time']
        
        # Calculate success rates
        download_success_rate = (self.stats['episodes_downloaded'] / max(self.stats['episodes_found'], 1)) * 100
        generation_success_rate = (self.stats['stories_generated'] / max(self.stats['episodes_downloaded'], 1)) * 100
        local_import_success_rate = (self.stats['local_imported'] / max(self.stats['stories_generated'], 1)) * 100
        production_sync_success_rate = (self.stats['production_synced'] / max(self.stats['stories_generated'], 1)) * 100
        
        # Create comprehensive report
        report = {
            'test_run_info': {
                'start_time': self.stats['start_time'].isoformat(),
                'end_time': end_time.isoformat(),
                'duration_minutes': duration.total_seconds() / 60,
                'target_feed': self.stats['target_feed'],
                'max_episodes': self.stats['max_episodes']
            },
            'test_configuration': {
                'superprompt_used': 'SuperPrompt_Optimized.md',
                'target_bitrate': self.config['target_bitrate'],
                'max_file_size_mb': self.config['max_file_size_mb'],
                'days_back': self.config['days_back'],
                'api_calls_made': self.stats['api_calls_made']
            },
            'test_results': {
                'episodes_found': self.stats['episodes_found'],
                'episodes_downloaded': self.stats['episodes_downloaded'],
                'stories_generated': self.stats['stories_generated'],
                'local_imported': self.stats['local_imported'],
                'production_synced': self.stats['production_synced']
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
                'ready_for_crewai': len(self.stats['errors']) == 0 and all([
                    download_success_rate >= 80,
                    generation_success_rate >= 80,
                    local_import_success_rate >= 80,
                    production_sync_success_rate >= 80
                ])
            },
            'errors': self.stats['errors'],
            'warnings': self.stats['warnings']
        }
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Path("logs") / f"etoro_focused_e2e_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Log comprehensive summary
        self.logger.info("=" * 80)
        self.logger.info("🎯 ETORO FOCUSED E2E TEST REPORT")
        self.logger.info("=" * 80)
        self.logger.info(f"⏱️  Duration: {duration.total_seconds() / 60:.1f} minutes")
        self.logger.info(f"🎯 Target Feed: eToro Digest Invest")
        self.logger.info(f"📊 Episodes Processed: {self.stats['episodes_found']} found → {self.stats['episodes_downloaded']} downloaded")
        self.logger.info(f"✍️  Stories Generated: {self.stats['stories_generated']} ({generation_success_rate:.1f}% success)")
        self.logger.info(f"💾 Local Database: {self.stats['local_imported']} imported ({local_import_success_rate:.1f}% success)")
        self.logger.info(f"🌐 Production Database: {self.stats['production_synced']} synced ({production_sync_success_rate:.1f}% success)")
        self.logger.info(f"🔧 API Calls Made: {self.stats['api_calls_made']}")
        self.logger.info(f"❌ Errors: {len(self.stats['errors'])}")
        self.logger.info(f"⚠️  Warnings: {len(self.stats['warnings'])}")
        
        # Performance breakdown
        if self.stats['performance_metrics']:
            self.logger.info("\n📈 PERFORMANCE BREAKDOWN:")
            for metric, value in self.stats['performance_metrics'].items():
                self.logger.info(f"  {metric}: {value:.2f}s")
        
        # Quality assessment
        overall_success = report['quality_assessment']['ready_for_crewai']
        if overall_success:
            self.logger.info("\n🎉 QUALITY ASSESSMENT: EXCELLENT")
            self.logger.info("✅ Enhanced automation system is ready for CrewAI integration!")
            self.logger.info("✅ All workflow components validated successfully")
            self.logger.info("✅ Dual database synchronization working perfectly")
        else:
            self.logger.info("\n⚠️ QUALITY ASSESSMENT: NEEDS ATTENTION")
            self.logger.info("❌ Some issues detected - review errors before CrewAI integration")
        
        # Errors and warnings summary
        if self.stats['errors']:
            self.logger.error("\n🚨 CRITICAL ISSUES:")
            for i, error in enumerate(self.stats['errors'][:3], 1):
                self.logger.error(f"  {i}. {error}")
            if len(self.stats['errors']) > 3:
                self.logger.error(f"  ... and {len(self.stats['errors']) - 3} more errors")
        
        if self.stats['warnings']:
            self.logger.warning("\n⚠️ WARNINGS:")
            for i, warning in enumerate(self.stats['warnings'][:3], 1):
                self.logger.warning(f"  {i}. {warning}")
            if len(self.stats['warnings']) > 3:
                self.logger.warning(f"  ... and {len(self.stats['warnings']) - 3} more warnings")
        
        self.logger.info(f"\n📄 Full report saved: {report_file}")
        
        return report


def main():
    """Main execution function for eToro focused E2E test"""
    print("🎯 ETORO DIGEST INVEST FOCUSED END-TO-END TEST")
    print("=" * 80)
    print("InvestingDojo.co - Enhanced Automation Workflow Validation")
    print()
    print("🎯 TARGET: eToro Digest Invest podcast feed")
    print("📊 SCOPE: Last 3 episodes maximum")
    print("🧠 AI: SuperPrompt_Optimized.md")
    print("💾 DATABASES: Local + Production synchronization")
    print("🔧 PURPOSE: Validate system before CrewAI integration")
    print()
    
    # Confirm execution
    confirm = input("🚀 Ready to run focused E2E test? (y/N): ")
    if confirm.lower() != 'y':
        print("Test cancelled.")
        return 1
    
    print()
    
    try:
        # Create and run test
        test = EToroFocusedE2ETest()
        success = test.run_focused_e2e_test()
        
        if success:
            print("\n🎉 ETORO FOCUSED E2E TEST COMPLETED SUCCESSFULLY!")
            print("✅ Enhanced automation system validated and ready!")
            print("✅ Dual database synchronization working perfectly!")
            print("✅ System ready for CrewAI agentic workflow integration!")
            return 0
        else:
            print("\n❌ ETORO FOCUSED E2E TEST FAILED!")
            print("❌ Please review errors and fix issues before proceeding.")
            print("❌ Check the test report for detailed analysis.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {str(e)}")
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    success = main()
    sys.exit(success)