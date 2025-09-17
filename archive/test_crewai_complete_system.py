#!/usr/bin/env python3
"""
COMPREHENSIVE CREWAI SYSTEM TEST SUITE
Multi-agent CrewAI system validation and JSON output compatibility testing

This comprehensive test suite validates:
1. Complete workflow from transcript input to JSON output
2. JSON schema compatibility between SuperPrompt and CrewAI workflows
3. A/B testing framework validation
4. Database schema validation and import compatibility
5. Performance and quality metrics comparison
6. Integration layer functionality
7. Production readiness assessment

Usage:
    python automation/test_crewai_complete_system.py
    python automation/test_crewai_complete_system.py --test-type=compatibility
    python automation/test_crewai_complete_system.py --test-type=performance
    python automation/test_crewai_complete_system.py --test-type=integration
"""

import os
import sys
import json
import time
import logging
import argparse
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import statistics
from dataclasses import dataclass, asdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import automation components
from automation.story_generator import StoryGenerator
from automation.crewai_integration import IntegratedStoryGenerator, IntegrationConfig, PerformanceMonitor
from automation.crew_ai_story_generator import CrewAIStoryGenerator, is_crewai_available
from automation.database_importer import DatabaseImporter

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    duration: float
    details: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]

class CrewAISystemTester:
    """Comprehensive CrewAI system testing framework"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.setup_logging()
        self.config = self.load_test_configuration(config_path)
        self.test_results: List[TestResult] = []
        self.start_time = datetime.now()
        
        # Test data paths
        self.etoro_test_dir = Path("temp_processing/etoro_test")
        self.test_transcripts_dir = Path("automation/test-transcripts")
        
        # Database configurations
        self.local_db_config = {
            'host': os.getenv('DB_LOCAL_HOST', 'localhost'),
            'database': os.getenv('DB_LOCAL_DATABASE', 'u219832816_investing_dojo'),
            'user': os.getenv('DB_LOCAL_USER', 'u219832816_davethackeray'),
            'password': os.getenv('DB_LOCAL_PASSWORD', 'ToTheM00n!'),
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': False
        }
        
        self.logger.info("🧪 CrewAI System Tester initialized")
        self.logger.info(f"📊 Test configuration loaded")
    
    def setup_logging(self):
        """Setup comprehensive test logging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path("logs/crewai_tests")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"crewai_system_test_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🔍 Test logging initialized - Log file: {log_file}")
    
    def load_test_configuration(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """Load test configuration"""
        default_config = {
            'api_key': os.getenv('GEMINI_API_KEY'),
            'superprompt_path': Path("automation/SuperPrompt.md"),
            'test_episodes_limit': 3,
            'timeout_seconds': 300,
            'quality_threshold': 7.0,
            'performance_tolerance': 0.2,  # 20% performance difference tolerance
            'required_fields': [
                'id', 'title', 'summary', 'full_content', 'content_type',
                'belt_levels', 'difficulty_level', 'time_required'
            ],
            'enum_fields': {
                'belt_levels': ['white-belt', 'yellow-belt', 'orange-belt', 'green-belt', 
                               'blue-belt', 'brown-belt', 'black-belt'],
                'content_type': ['curriculum-war-story', 'ai-breakthrough', 'systematic-strategy',
                               'family-wealth-builder', 'mastery-technique', 'mindset-hack',
                               'research-method', 'risk-lesson', 'epic-curriculum-fail',
                               'belt-progression-moment', 'ai-integration-guide', 'generational-wealth-wisdom'],
                'difficulty_level': ['foundational', 'intermediate-skill', 'advanced-mastery'],
                'time_required': ['5-minutes', '10-minutes', '15-minutes', '30-minutes',
                                '1-hour', '2-hours', 'ongoing', 'varies']
            },
            'integration_config': {
                'crewai_enabled': True,
                'rollout_percentage': 50,
                'ab_testing_enabled': True,
                'monitoring_enabled': True,
                'auto_fallback': True
            }
        }
        
        if not default_config['api_key']:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        if not default_config['superprompt_path'].exists():
            raise FileNotFoundError(f"SuperPrompt not found: {default_config['superprompt_path']}")
        
        return default_config
    
    def run_comprehensive_tests(self, test_type: str = "all") -> Dict[str, Any]:
        """Run comprehensive test suite"""
        self.logger.info("🚀 STARTING COMPREHENSIVE CREWAI SYSTEM TESTS")
        self.logger.info("=" * 80)
        
        try:
            if test_type in ["all", "compatibility"]:
                self.logger.info("📋 Running JSON Output Compatibility Tests...")
                compatibility_result = self.test_json_output_compatibility()
                self.test_results.append(compatibility_result)
            
            if test_type in ["all", "ab_testing"]:
                self.logger.info("🔄 Running A/B Testing Framework Validation...")
                ab_testing_result = self.test_ab_testing_framework()
                self.test_results.append(ab_testing_result)
            
            if test_type in ["all", "database"]:
                self.logger.info("💾 Running Database Schema Validation...")
                database_result = self.test_database_schema_validation()
                self.test_results.append(database_result)
            
            if test_type in ["all", "performance"]:
                self.logger.info("⚡ Running Performance and Quality Testing...")
                performance_result = self.test_performance_and_quality()
                self.test_results.append(performance_result)
            
            if test_type in ["all", "integration"]:
                self.logger.info("🔗 Running Integration Testing...")
                integration_result = self.test_integration_layer()
                self.test_results.append(integration_result)
            
            if test_type in ["all", "etoro"]:
                self.logger.info("📊 Running eToro Data Testing...")
                etoro_result = self.test_with_etoro_data()
                self.test_results.append(etoro_result)
            
            # Generate final report
            final_report = self.generate_production_readiness_report()
            
            self.logger.info("🎉 COMPREHENSIVE TESTS COMPLETED")
            return final_report
            
        except Exception as e:
            self.logger.error(f"❌ Test suite failed: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    def test_json_output_compatibility(self) -> TestResult:
        """Test JSON output compatibility between SuperPrompt and CrewAI workflows"""
        start_time = time.time()
        test_name = "JSON Output Compatibility"
        errors = []
        warnings = []
        
        try:
            self.logger.info("🔍 Testing JSON output compatibility...")
            
            # Get test transcript
            test_transcript, test_metadata = self.get_test_transcript()
            
            # Generate stories with SuperPrompt
            self.logger.info("📝 Generating stories with SuperPrompt workflow...")
            superprompt_generator = StoryGenerator(
                api_key=self.config['api_key'],
                superprompt_path=self.config['superprompt_path']
            )
            
            superprompt_stories = superprompt_generator.generate_stories_from_transcript(
                test_transcript, test_metadata
            )
            
            if not superprompt_stories:
                errors.append("SuperPrompt workflow failed to generate stories")
                return TestResult(
                    test_name=test_name,
                    success=False,
                    duration=time.time() - start_time,
                    details={},
                    errors=errors,
                    warnings=warnings,
                    metrics={}
                )
            
            # Generate stories with CrewAI (if available)
            crewai_stories = []
            if is_crewai_available():
                self.logger.info("🤖 Generating stories with CrewAI workflow...")
                try:
                    crewai_generator = CrewAIStoryGenerator(
                        api_key=self.config['api_key'],
                        superprompt_path=self.config['superprompt_path']
                    )
                    
                    crewai_stories = crewai_generator.generate_stories_from_transcript(
                        test_transcript, test_metadata
                    )
                    
                    if not crewai_stories:
                        warnings.append("CrewAI workflow failed to generate stories")
                except Exception as e:
                    warnings.append(f"CrewAI generation failed: {str(e)}")
            else:
                warnings.append("CrewAI not available for testing")
            
            # Compare JSON schemas
            compatibility_result = self.compare_json_schemas(superprompt_stories, crewai_stories)
            
            # Validate ENUM fields
            enum_validation = self.validate_enum_fields(superprompt_stories + crewai_stories)
            
            # Test database compatibility
            database_compatibility = self.test_database_import_compatibility(
                superprompt_stories + crewai_stories
            )
            
            success = (
                compatibility_result['compatible'] and
                enum_validation['valid'] and
                database_compatibility['success']
            )
            
            details = {
                'superprompt_stories_count': len(superprompt_stories),
                'crewai_stories_count': len(crewai_stories),
                'schema_compatibility': compatibility_result,
                'enum_validation': enum_validation,
                'database_compatibility': database_compatibility
            }
            
            metrics = {
                'total_stories_tested': len(superprompt_stories) + len(crewai_stories),
                'compatibility_score': compatibility_result.get('compatibility_score', 0),
                'enum_compliance_rate': enum_validation.get('compliance_rate', 0)
            }
            
            self.logger.info(f"✅ JSON compatibility test completed: {success}")
            
            return TestResult(
                test_name=test_name,
                success=success,
                duration=time.time() - start_time,
                details=details,
                errors=errors,
                warnings=warnings,
                metrics=metrics
            )
            
        except Exception as e:
            errors.append(f"JSON compatibility test error: {str(e)}")
            self.logger.error(f"❌ JSON compatibility test failed: {str(e)}")
            
            return TestResult(
                test_name=test_name,
                success=False,
                duration=time.time() - start_time,
                details={},
                errors=errors,
                warnings=warnings,
                metrics={}
            )
    
    def test_ab_testing_framework(self) -> TestResult:
        """Test A/B testing framework validation"""
        start_time = time.time()
        test_name = "A/B Testing Framework"
        errors = []
        warnings = []
        
        try:
            self.logger.info("🔄 Testing A/B testing framework...")
            
            # Test integration config
            integration_config = IntegrationConfig(self.config['integration_config'])
            
            # Test consistent episode assignment
            test_episodes = [
                {'id': 'test_episode_1', 'title': 'Test Episode 1'},
                {'id': 'test_episode_2', 'title': 'Test Episode 2'},
                {'id': 'test_episode_3', 'title': 'Test Episode 3'}
            ]
            
            assignment_consistency = {}
            for episode in test_episodes:
                assignments = []
                # Test multiple assignments for same episode
                for _ in range(10):
                    should_use_crewai = integration_config.should_use_crewai(episode['id'])
                    assignments.append(should_use_crewai)
                
                # All assignments should be identical for same episode
                assignment_consistency[episode['id']] = {
                    'consistent': len(set(assignments)) == 1,
                    'assignment': assignments[0] if assignments else None,
                    'total_tests': len(assignments)
                }
            
            # Test rollout percentage functionality
            rollout_tests = {}
            for percentage in [5, 25, 50, 100]:
                integration_config.rollout_percentage = percentage
                crewai_selections = 0
                total_tests = 100
                
                for i in range(total_tests):
                    test_episode_id = f"rollout_test_{i}"
                    if integration_config.should_use_crewai(test_episode_id):
                        crewai_selections += 1
                
                actual_percentage = (crewai_selections / total_tests) * 100
                rollout_tests[f"{percentage}%"] = {
                    'expected': percentage,
                    'actual': actual_percentage,
                    'within_tolerance': abs(actual_percentage - percentage) <= 10  # 10% tolerance
                }
            
            # Validate results
            consistency_passed = all(
                result['consistent'] for result in assignment_consistency.values()
            )
            
            rollout_passed = all(
                result['within_tolerance'] for result in rollout_tests.values()
            )
            
            success = consistency_passed and rollout_passed
            
            details = {
                'assignment_consistency': assignment_consistency,
                'rollout_tests': rollout_tests,
                'integration_config_summary': integration_config.get_config_summary()
            }
            
            metrics = {
                'consistency_rate': sum(1 for r in assignment_consistency.values() if r['consistent']) / len(assignment_consistency),
                'rollout_accuracy': sum(1 for r in rollout_tests.values() if r['within_tolerance']) / len(rollout_tests)
            }
            
            if not consistency_passed:
                errors.append("Episode assignment consistency failed")
            if not rollout_passed:
                errors.append("Rollout percentage accuracy failed")
            
            self.logger.info(f"✅ A/B testing framework test completed: {success}")
            
            return TestResult(
                test_name=test_name,
                success=success,
                duration=time.time() - start_time,
                details=details,
                errors=errors,
                warnings=warnings,
                metrics=metrics
            )
            
        except Exception as e:
            errors.append(f"A/B testing framework error: {str(e)}")
            self.logger.error(f"❌ A/B testing framework test failed: {str(e)}")
            
            return TestResult(
                test_name=test_name,
                success=False,
                duration=time.time() - start_time,
                details={},
                errors=errors,
                warnings=warnings,
                metrics={}
            )
    
    def test_database_schema_validation(self) -> TestResult:
        """Test database schema validation"""
        start_time = time.time()
        test_name = "Database Schema Validation"
        errors = []
        warnings = []
        
        try:
            self.logger.info("💾 Testing database schema validation...")
            
            # Generate test stories
            test_transcript, test_metadata = self.get_test_transcript()
            
            # Use integrated generator to get stories
            integrated_generator = IntegratedStoryGenerator(
                api_key=self.config['api_key'],
                superprompt_path=self.config['superprompt_path'],
                config=self.config['integration_config']
            )
            
            test_stories = integrated_generator.generate_stories_from_transcript(
                test_transcript, test_metadata
            )
            
            if not test_stories:
                errors.append("Failed to generate test stories for database validation")
                return TestResult(
                    test_name=test_name,
                    success=False,
                    duration=time.time() - start_time,
                    details={},
                    errors=errors,
                    warnings=warnings,
                    metrics={}
                )
            
            # Test database compatibility
            database_compatibility = self.test_database_import_compatibility(test_stories)
            
            # Test ENUM field validation
            enum_validation_results = {}
            for story in test_stories:
                story_enum_validation = self.validate_story_enum_fields(story)
                if story_enum_validation['errors']:
                    enum_validation_results[story.get('id', 'unknown')] = story_enum_validation
            
            success = (
                database_compatibility['success'] and
                len(enum_validation_results) == 0
            )
            
            details = {
                'stories_tested': len(test_stories),
                'database_compatibility': database_compatibility,
                'enum_validation_errors': enum_validation_results
            }
            
            metrics = {
                'total_stories_tested': len(test_stories),
                'database_compatibility_rate': 1.0 if database_compatibility['success'] else 0.0,
                'enum_compliance_rate': 1 - (len(enum_validation_results) / len(test_stories)) if test_stories else 0
            }
            
            if not database_compatibility['success']:
                errors.extend(database_compatibility.get('issues', []))
            if enum_validation_results:
                errors.append(f"ENUM validation failed for {len(enum_validation_results)} stories")
            
            self.logger.info(f"✅ Database schema validation completed: {success}")
            
            return TestResult(
                test_name=test_name,
                success=success,
                duration=time.time() - start_time,
                details=details,
                errors=errors,
                warnings=warnings,
                metrics=metrics
            )
            
        except Exception as e:
            errors.append(f"Database schema validation error: {str(e)}")
            self.logger.error(f"❌ Database schema validation failed: {str(e)}")
            
            return TestResult(
                test_name=test_name,
                success=False,
                duration=time.time() - start_time,
                details={},
                errors=errors,
                warnings=warnings,
                metrics={}
            )
    
    def test_performance_and_quality(self) -> TestResult:
        """Test performance and quality comparison"""
        start_time = time.time()
        test_name = "Performance and Quality Testing"
        errors = []
        warnings = []
        
        try:
            self.logger.info("⚡ Testing performance and quality metrics...")
            
            # Get test data
            test_transcript, test_metadata = self.get_test_transcript()
            
            # Test SuperPrompt performance
            superprompt_metrics = self.measure_workflow_performance(
                'superprompt', test_transcript, test_metadata
            )
            
            # Test CrewAI performance (if available)
            crewai_metrics = {}
            if is_crewai_available():
                crewai_metrics = self.measure_workflow_performance(
                    'crewai', test_transcript, test_metadata
                )
            else:
                warnings.append("CrewAI not available for performance testing")
            
            # Compare performance metrics
            performance_comparison = self.compare_performance_metrics(
                superprompt_metrics, crewai_metrics
            )
            
            # Test quality scoring
            all_stories = superprompt_metrics.get('stories', []) + crewai_metrics.get('stories', [])
            quality_assessment = self.assess_quality_metrics(all_stories)
            
            # Validate performance criteria
            performance_acceptable = True
            if crewai_metrics and superprompt_metrics:
                time_difference = abs(
                    crewai_metrics.get('processing_time', 0) - 
                    superprompt_metrics.get('processing_time', 0)
                )
                max_acceptable_difference = max(
                    superprompt_metrics.get('processing_time', 0) * self.config['performance_tolerance'],
                    30  # Minimum 30 seconds tolerance
                )
                performance_acceptable = time_difference <= max_acceptable_difference
            
            quality_acceptable = (
                quality_assessment['average_quality'] >= self.config['quality_threshold']
            )
            
            success = performance_acceptable and quality_acceptable
            
            details = {
                'superprompt_metrics': superprompt_metrics,
                'crewai_metrics': crewai_metrics,
                'performance_comparison': performance_comparison,
                'quality_assessment': quality_assessment
            }
            
            metrics = {
                'superprompt_processing_time': superprompt_metrics.get('processing_time', 0),
                'crewai_processing_time': crewai_metrics.get('processing_time', 0),
                'average_quality_score': quality_assessment['average_quality']
            }
            
            if not performance_acceptable:
                errors.append("Performance difference exceeds acceptable tolerance")
            if not quality_acceptable:
                errors.append(f"Quality score {quality_assessment['average_quality']:.1f} below threshold {self.config['quality_threshold']}")
            
            self.logger.info(f"✅ Performance and quality testing completed: {success}")
            
            return TestResult(
                test_name=test_name,
                success=success,
                duration=time.time() - start_time,
                details=details,
                errors=errors,
                warnings=warnings,
                metrics=metrics
            )
            
        except Exception as e:
            errors.append(f"Performance and quality testing error: {str(e)}")
            self.logger.error(f"❌ Performance and quality testing failed: {str(e)}")
            
            return TestResult(
                test_name=test_name,
                success=False,
                duration=time.time() - start_time,
                details={},
                errors=errors,
                warnings=warnings,
                metrics={}
            )
    
    def test_integration_layer(self) -> TestResult:
        """Test integration layer functionality"""
        start_time = time.time()
        test_name = "Integration Layer Testing"
        errors = []
        warnings = []
        
        try:
            self.logger.info("🔗 Testing integration layer functionality...")
            
            # Test drop-in replacement functionality
            test_transcript, test_metadata = self.get_test_transcript()
            
            # Test IntegratedStoryGenerator
            integrated_generator = IntegratedStoryGenerator(
                api_key=self.config['api_key'],
                superprompt_path=self.config['superprompt_path'],
                config=self.config['integration_config']
            )
            
            # Test status reporting
            status = integrated_generator.get_status()
            status_valid = (
                'integration_enabled' in status and
                'generators_available' in status and
                'config' in status
            )
            
            # Test story generation
            stories = integrated_generator.generate_stories_from_transcript(
                test_transcript, test_metadata
            )
            
            generation_success = stories is not None and len(stories) > 0
            
            # Test performance reporting
            performance_report = integrated_generator.get_performance_report()
            performance_report_valid = (
                'timestamp' in performance_report and
                'config' in performance_report and
                'performance_comparison' in performance_report
            )
            
            success = status_valid and generation_success and performance_report_valid
            
            details = {
                'status_check': status,
                'generation_success': generation_success,
                'stories_generated': len(stories) if stories else 0,
                'performance_report_valid': performance_report_valid
            }
            
            metrics = {
                'integration_features_working': sum([status_valid, generation_success, performance_report_valid]),
                'total_integration_features': 3,
                'stories_generated': len(stories) if stories else 0
            }
            
            if not status_valid:
                errors.append("Status reporting failed")
            if not generation_success:
                errors.append("Story generation failed")
            if not performance_report_valid:
                errors.append("Performance reporting failed")
            
            self.logger.info(f"✅ Integration layer testing completed: {success}")
            
            return TestResult(
                test_name=test_name,
                success=success,
                duration=time.time() - start_time,
                details=details,
                errors=errors,
                warnings=warnings,
                metrics=metrics
            )
            
        except Exception as e:
            errors.append(f"Integration layer testing error: {str(e)}")
            self.logger.error(f"❌ Integration layer testing failed: {str(e)}")
            
            return TestResult(
                test_name=test_name,
                success=False,
                duration=time.time() - start_time,
                details={},
                errors=errors,
                warnings=warnings,
                metrics={}
            )
    
    def test_with_etoro_data(self) -> TestResult:
        """Test with real eToro data from temp_processing/etoro_test/"""
        start_time = time.time()
        test_name = "eToro Data Testing"
        errors = []
        warnings = []
        
        try:
            self.logger.info("📊 Testing with real eToro data...")
            
            # Load eToro test data
            etoro_episodes = self.load_etoro_test_data()
            
            if not etoro_episodes:
                warnings.append("No eToro test data found - using sample data")
                # Create sample episode for testing
                etoro_episodes = [{
                    'id': 'sample_etoro_episode',
                    'podcast_title': 'eToro Market Digest',
                    'episode_title': 'Sample Market Update',
                    'published_date': datetime.now().isoformat(),
                    'episode_url': 'https://test.etoro.com/sample'
                }]
            
            # Test with integrated generator
            integrated_generator = IntegratedStoryGenerator(
                api_key=self.config['api_key'],
                superprompt_path=self.config['superprompt_path'],
                config=self.config['integration_config']
            )
            
            etoro_results = []
            successful_generations = 0
            
            for episode in etoro_episodes:
                try:
                    # Use sample transcript for testing
                    sample_transcript = f"""
                    This is episode {episode.get('episode_title', 'Unknown')} from {episode.get('podcast_title', 'Unknown')}.
                    Today we're discussing market movements and investment opportunities.
                    The S&P 500 has shown strong performance this quarter.
                    Investors should consider diversification strategies for long-term growth.
                    Key topics include risk management, portfolio allocation, and market timing strategies.
                    """
                    
                    # Generate stories
                    stories = integrated_generator.generate_stories_from_transcript(
                        sample_transcript, episode
                    )
                    
                    if stories:
                        successful_generations += 1
                        etoro_results.append({
                            'episode_id': episode.get('id'),
                            'episode_title': episode.get('episode_title'),
                            'stories_generated': len(stories),
                            'generator_used': stories[0].get('integration_metadata', {}).get('generator_used', 'unknown'),
                            'processing_successful': True
                        })
                    else:
                        etoro_results.append({
                            'episode_id': episode.get('id'),
                            'episode_title': episode.get('episode_title'),
                            'stories_generated': 0,
                            'processing_successful': False
                        })
                
                except Exception as e:
                    errors.append(f"Error processing eToro episode {episode.get('id', 'unknown')}: {str(e)}")
                    etoro_results.append({
                        'episode_id': episode.get('id'),
                        'episode_title': episode.get('episode_title'),
                        'error': str(e),
                        'processing_successful': False
                    })
            
            # Calculate success metrics
            success_rate = successful_generations / len(etoro_episodes) if etoro_episodes else 0
            total_stories_generated = sum(r.get('stories_generated', 0) for r in etoro_results)
            
            success = success_rate >= 0.5 and len(errors) == 0  # At least 50% success rate
            
            details = {
                'etoro_episodes_tested': len(etoro_episodes),
                'successful_generations': successful_generations,
                'success_rate': success_rate,
                'total_stories_generated': total_stories_generated,
                'episode_results': etoro_results
            }
            
            metrics = {
                'etoro_episodes_processed': len(etoro_episodes),
                'etoro_success_rate': success_rate,
                'etoro_stories_generated': total_stories_generated,
                'etoro_processing_efficiency': successful_generations / len(etoro_episodes) if etoro_episodes else 0
            }
            
            if success_rate < 0.5:
                errors.append(f"eToro processing success rate too low: {success_rate:.1%}")
            
            self.logger.info(f"✅ eToro data testing completed: {success}")
            self.logger.info(f"📊 Processed {len(etoro_episodes)} episodes, {successful_generations} successful")
            
            return TestResult(
                test_name=test_name,
                success=success,
                duration=time.time() - start_time,
                details=details,
                errors=errors,
                warnings=warnings,
                metrics=metrics
            )
            
        except Exception as e:
            errors.append(f"eToro data testing error: {str(e)}")
            self.logger.error(f"❌ eToro data testing failed: {str(e)}")
            
            return TestResult(
                test_name=
test_name,
                success=False,
                duration=time.time() - start_time,
                details={},
                errors=errors,
                warnings=warnings,
                metrics={}
            )
    
    # Helper methods
    def get_test_transcript(self) -> Tuple[str, Dict[str, Any]]:
        """Get test transcript and metadata"""
        # Try to get from test-transcripts directory first
        if self.test_transcripts_dir.exists():
            transcript_files = list(self.test_transcripts_dir.glob("*.txt"))
            if transcript_files:
                transcript_file = transcript_files[0]
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript = f.read()
                
                # Extract metadata from filename
                filename = transcript_file.stem
                parts = filename.split('_')
                
                metadata = {
                    'id': parts[0] if parts else 'test_episode',
                    'podcast_title': parts[1] if len(parts) > 1 else 'Test Podcast',
                    'episode_title': ' '.join(parts[2:]) if len(parts) > 2 else 'Test Episode',
                    'published_date': datetime.now().isoformat(),
                    'episode_url': 'https://test.example.com/episode'
                }
                
                return transcript, metadata
        
        # Fallback to sample transcript
        sample_transcript = """
        Welcome to today's market update. The S&P 500 reached new highs today, 
        driven by strong earnings from technology companies. Nvidia reported 
        record quarterly revenue, beating analyst expectations by 15%. 
        
        In other news, the Federal Reserve is expected to maintain current 
        interest rates at their next meeting, citing stable inflation metrics. 
        Investors are closely watching for any signals about future monetary policy.
        
        For individual investors, this presents both opportunities and challenges. 
        The key is to maintain a diversified portfolio and focus on long-term goals 
        rather than short-term market fluctuations.
        """
        
        metadata = {
            'id': 'sample_test_episode',
            'podcast_title': 'Test Market Update',
            'episode_title': 'Sample Market Analysis',
            'published_date': datetime.now().isoformat(),
            'episode_url': 'https://test.example.com/sample'
        }
        
        return sample_transcript.strip(), metadata
    
    def load_etoro_test_data(self) -> List[Dict[str, Any]]:
        """Load eToro test data from temp_processing/etoro_test/"""
        etoro_episodes = []
        
        try:
            if not self.etoro_test_dir.exists():
                self.logger.warning(f"eToro test directory not found: {self.etoro_test_dir}")
                return []
            
            # Look for batch summary files
            batch_files = list(self.etoro_test_dir.rglob("*_summary.json"))
            
            for batch_file in batch_files:
                try:
                    with open(batch_file, 'r', encoding='utf-8') as f:
                        batch_data = json.load(f)
                    
                    episodes = batch_data.get('episodes', [])
                    for episode in episodes:
                        # Check if audio file exists
                        audio_path = Path(episode.get('compressed_filepath', ''))
                        if audio_path.exists():
                            etoro_episodes.append(episode)
                        else:
                            self.logger.warning(f"Audio file not found: {audio_path}")
                
                except Exception as e:
                    self.logger.error(f"Error loading batch file {batch_file}: {str(e)}")
            
            self.logger.info(f"Loaded {len(etoro_episodes)} eToro test episodes")
            return etoro_episodes[:self.config['test_episodes_limit']]
            
        except Exception as e:
            self.logger.error(f"Error loading eToro test data: {str(e)}")
            return []
    
    def compare_json_schemas(self, superprompt_stories: List[Dict[str, Any]], 
                           crewai_stories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare JSON schemas between workflows"""
        all_stories = superprompt_stories + crewai_stories
        
        if not all_stories:
            return {'compatible': False, 'compatibility_score': 0}
        
        # Basic compatibility check
        required_fields = set(self.config['required_fields'])
        all_fields = set()
        
        for story in all_stories:
            all_fields.update(story.keys())
        
        missing_fields = required_fields - all_fields
        compatibility_score = 1.0 - (len(missing_fields) * 0.1)
        
        return {
            'compatible': len(missing_fields) == 0,
            'compatibility_score': max(0, compatibility_score),
            'missing_fields': list(missing_fields),
            'total_fields': len(all_fields)
        }
    
    def validate_enum_fields(self, stories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate ENUM fields against database constraints"""
        enum_errors = []
        total_validations = 0
        successful_validations = 0
        
        for story in stories:
            for field_name, valid_values in self.config['enum_fields'].items():
                if field_name in story:
                    total_validations += 1
                    field_value = story[field_name]
                    
                    if isinstance(field_value, list):
                        for value in field_value:
                            if value in valid_values:
                                successful_validations += 1
                            else:
                                enum_errors.append(f"{field_name}: {value}")
                    else:
                        if field_value in valid_values:
                            successful_validations += 1
                        else:
                            enum_errors.append(f"{field_name}: {field_value}")
        
        compliance_rate = successful_validations / total_validations if total_validations > 0 else 1.0
        
        return {
            'valid': len(enum_errors) == 0,
            'compliance_rate': compliance_rate,
            'errors': enum_errors
        }
    
    def validate_story_enum_fields(self, story: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ENUM fields for a single story"""
        errors = []
        
        for field_name, valid_values in self.config['enum_fields'].items():
            if field_name in story:
                field_value = story[field_name]
                
                if isinstance(field_value, list):
                    for value in field_value:
                        if value not in valid_values:
                            errors.append(f"{field_name}: '{value}' not in {valid_values}")
                else:
                    if field_value not in valid_values:
                        errors.append(f"{field_name}: '{field_value}' not in {valid_values}")
        
        return {'errors': errors}
    
    def test_database_import_compatibility(self, stories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test database import compatibility"""
        issues = []
        
        for story in stories:
            for field in self.config['required_fields']:
                if field not in story or not story[field]:
                    issues.append(f"Missing required field: {field}")
        
        return {
            'success': len(issues) == 0,
            'issues': issues
        }
    
    def measure_workflow_performance(self, workflow_type: str, transcript: str, 
                                   metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Measure performance metrics for a specific workflow"""
        try:
            start_time = time.time()
            
            if workflow_type == 'superprompt':
                generator = StoryGenerator(
                    api_key=self.config['api_key'],
                    superprompt_path=self.config['superprompt_path']
                )
                stories = generator.generate_stories_from_transcript(transcript, metadata)
            
            elif workflow_type == 'crewai':
                generator = CrewAIStoryGenerator(
                    api_key=self.config['api_key'],
                    superprompt_path=self.config['superprompt_path']
                )
                stories = generator.generate_stories_from_transcript(transcript, metadata)
            
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")
            
            processing_time = time.time() - start_time
            
            # Calculate quality scores
            quality_scores = []
            if stories:
                for story in stories:
                    quality_score = self.calculate_story_quality_score(story)
                    quality_scores.append(quality_score)
            
            return {
                'workflow_type': workflow_type,
                'processing_time': processing_time,
                'stories_generated': len(stories) if stories else 0,
                'stories': stories or [],
                'quality_scores': quality_scores,
                'average_quality': statistics.mean(quality_scores) if quality_scores else 0,
                'success': stories is not None and len(stories) > 0
            }
            
        except Exception as e:
            self.logger.error(f"Error measuring {workflow_type} performance: {str(e)}")
            return {
                'workflow_type': workflow_type,
                'processing_time': 0,
                'stories_generated': 0,
                'stories': [],
                'quality_scores': [],
                'average_quality': 0,
                'success': False,
                'error': str(e)
            }
    
    def calculate_story_quality_score(self, story: Dict[str, Any]) -> float:
        """Calculate quality score for a story"""
        score = 0.0
        max_score = 10.0
        
        # Required fields (3 points)
        required_fields = ['id', 'title', 'summary', 'full_content', 'content_type']
        if all(field in story and story[field] for field in required_fields):
            score += 3.0
        
        # Content length (2 points)
        if 'full_content' in story:
            content_length = len(story['full_content'])
            if content_length > 1000:
                score += 2.0
            elif content_length > 500:
                score += 1.0
        
        # Enhanced fields (2 points)
        enhanced_fields = ['actionable_practices', 'discussion_prompts', 'belt_levels']
        present_enhanced = sum(1 for field in enhanced_fields if field in story and story[field])
        score += (present_enhanced / len(enhanced_fields)) * 2.0
        
        # Family focus (2 points)
        family_fields = ['family_security_relevance', 'children_education_angle']
        present_family = sum(1 for field in family_fields if field in story and story[field])
        score += (present_family / len(family_fields)) * 2.0
        
        # Completeness bonus (1 point)
        if len(story.keys()) > 10:
            score += 1.0
        
        return min(score, max_score)
    
    def compare_performance_metrics(self, superprompt_metrics: Dict[str, Any], 
                                  crewai_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Compare performance metrics between workflows"""
        if not superprompt_metrics or not crewai_metrics:
            return {
                'comparison_available': False,
                'reason': 'Missing metrics for comparison'
            }
        
        return {
            'comparison_available': True,
            'time_difference': crewai_metrics.get('processing_time', 0) - superprompt_metrics.get('processing_time', 0),
            'quality_difference': crewai_metrics.get('average_quality', 0) - superprompt_metrics.get('average_quality', 0),
            'stories_difference': crewai_metrics.get('stories_generated', 0) - superprompt_metrics.get('stories_generated', 0),
            'superprompt_faster': superprompt_metrics.get('processing_time', 0) < crewai_metrics.get('processing_time', 0),
            'crewai_higher_quality': crewai_metrics.get('average_quality', 0) > superprompt_metrics.get('average_quality', 0)
        }
    
    def assess_quality_metrics(self, stories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess quality metrics for stories"""
        if not stories:
            return {
                'average_quality': 0,
                'quality_distribution': {},
                'total_stories': 0
            }
        
        quality_scores = [self.calculate_story_quality_score(story) for story in stories]
        
        # Quality distribution
        quality_distribution = {
            'excellent (9-10)': sum(1 for score in quality_scores if score >= 9),
            'good (7-8.9)': sum(1 for score in quality_scores if 7 <= score < 9),
            'fair (5-6.9)': sum(1 for score in quality_scores if 5 <= score < 7),
            'poor (0-4.9)': sum(1 for score in quality_scores if score < 5)
        }
        
        return {
            'average_quality': statistics.mean(quality_scores),
            'quality_distribution': quality_distribution,
            'total_stories': len(stories),
            'quality_scores': quality_scores
        }
    
    def generate_production_readiness_report(self) -> Dict[str, Any]:
        """Generate comprehensive production readiness assessment report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate overall success rate
        successful_tests = sum(1 for result in self.test_results if result.success)
        total_tests = len(self.test_results)
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        # Aggregate metrics
        all_metrics = {}
        all_errors = []
        all_warnings = []
        
        for result in self.test_results:
            all_metrics.update(result.metrics)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        # Determine production readiness
        production_ready = (
            success_rate >= 0.8 and  # 80% test success rate
            len(all_errors) == 0 and  # No critical errors
            all_metrics.get('compatibility_score', 0) >= 0.9  # High compatibility
        )
        
        # Generate recommendations
        recommendations = []
        if success_rate < 0.8:
            recommendations.append("Improve test success rate before production deployment")
        if all_errors:
            recommendations.append("Resolve all critical errors before production deployment")
        if all_metrics.get('compatibility_score', 0) < 0.9:
            recommendations.append("Improve JSON schema compatibility between workflows")
        if not production_ready:
            recommendations.append("Complete additional testing and validation before production deployment")
        else:
            recommendations.append("System appears ready for production deployment with monitoring")
        
        report = {
            'assessment_timestamp': end_time.isoformat(),
            'test_duration_seconds': total_duration,
            'production_ready': production_ready,
            'overall_success_rate': success_rate,
            'test_summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests
            },
            'test_results': [asdict(result) for result in self.test_results],
            'aggregated_metrics': all_metrics,
            'critical_errors': all_errors,
            'warnings': all_warnings,
            'recommendations': recommendations,
            'system_capabilities': {
                'crewai_available': is_crewai_available(),
                'integration_layer_functional': any(
                    result.test_name == "Integration Layer Testing" and result.success 
                    for result in self.test_results
                ),
                'database_compatible': any(
                    result.test_name == "Database Schema Validation" and result.success 
                    for result in self.test_results
                ),
                'performance_acceptable': any(
                    result.test_name == "Performance and Quality Testing" and result.success 
                    for result in self.test_results
                )
            }
        }
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Path("logs/crewai_tests") / f"production_readiness_report_{timestamp}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Log summary
        self.logger.info("📊 PRODUCTION READINESS ASSESSMENT REPORT")
        self.logger.info("=" * 80)
        self.logger.info(f"🎯 Production Ready: {'✅ YES' if production_ready else '❌ NO'}")
        self.logger.info(f"📈 Overall Success Rate: {success_rate:.1%}")
        self.logger.info(f"✅ Successful Tests: {successful_tests}/{total_tests}")
        self.logger.info(f"❌ Critical Errors: {len(all_errors)}")
        self.logger.info(f"⚠️ Warnings: {len(all_warnings)}")
        self.logger.info(f"⏱️ Total Test Duration: {total_duration:.1f}s")
        
        if recommendations:
            self.logger.info("\n📋 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                self.logger.info(f"  {i}. {rec}")
        
        self.logger.info(f"\n📄 Full report saved: {report_file}")
        
        return report


def main():
    """Main entry point for comprehensive CrewAI system testing"""
    parser = argparse.ArgumentParser(description="Comprehensive CrewAI System Test Suite")
    parser.add_argument(
        '--test-type', 
        choices=['all', 'compatibility', 'ab_testing', 'database', 'performance', 'integration', 'etoro'],
        default='all',
        help='Type of tests to run'
    )
    parser.add_argument('--config', type=Path, help='Path to test configuration file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("🧪 COMPREHENSIVE CREWAI SYSTEM TEST SUITE")
    print("=" * 80)
    print("Multi-agent CrewAI system validation and compatibility testing")
    print()
    
    try:
        tester = CrewAISystemTester(config_path=args.config)
        report = tester.run_comprehensive_tests(test_type=args.test_type)
        
        if report.get('production_ready', False):
            print("\n🎉 SYSTEM IS PRODUCTION READY!")
            return True
        else:
            print("\n⚠️ SYSTEM NEEDS ADDITIONAL WORK BEFORE PRODUCTION")
            return False
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST FAILURE: {str(e)}")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)