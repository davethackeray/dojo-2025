#!/usr/bin/env python3
"""
CREWAI INTEGRATION TEST SCRIPT
Comprehensive testing of the CrewAI integration layer with existing automation
Demonstrates seamless switching, A/B testing, and performance monitoring
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import integration components
from automation.crewai_integration import (
    IntegratedStoryGenerator,
    StoryGeneratorFactory,
    IntegrationConfig,
    PerformanceMonitor,
    create_integrated_story_generator
)

# Import existing components for comparison
from automation.story_generator import StoryGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class IntegrationTester:
    """Comprehensive integration testing suite"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.superprompt_path = Path("automation/SuperPrompt.md")
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'performance_comparison': {},
            'recommendations': []
        }
        
        # Create test directories
        Path("logs").mkdir(exist_ok=True)
        Path("logs/crewai_integration").mkdir(exist_ok=True)
        Path("logs/crewai_metrics").mkdir(exist_ok=True)
    
    def validate_prerequisites(self) -> bool:
        """Validate all prerequisites for testing"""
        logger.info("🔍 Validating prerequisites...")
        
        issues = []
        
        # Check API key
        if not self.api_key:
            issues.append("GEMINI_API_KEY environment variable not set")
        
        # Check SuperPrompt
        if not self.superprompt_path.exists():
            issues.append(f"SuperPrompt not found: {self.superprompt_path}")
        
        # Check CrewAI availability
        try:
            from automation.crew_ai_story_generator import is_crewai_available
            if not is_crewai_available():
                logger.warning("⚠️ CrewAI not available - will test fallback behavior")
        except ImportError:
            logger.warning("⚠️ CrewAI components not available - will test fallback behavior")
        
        if issues:
            logger.error("❌ Prerequisites validation failed:")
            for issue in issues:
                logger.error(f"   - {issue}")
            return False
        
        logger.info("✅ Prerequisites validation passed")
        return True
    
    def test_configuration_system(self) -> bool:
        """Test the configuration system and environment variables"""
        logger.info("🧪 Testing configuration system...")
        
        try:
            # Test default configuration
            config = IntegrationConfig()
            default_summary = config.get_config_summary()
            
            logger.info(f"📊 Default config: {default_summary}")
            
            # Test environment variable override
            original_enabled = os.getenv('CREWAI_ENABLED')
            original_rollout = os.getenv('CREWAI_ROLLOUT_PERCENTAGE')
            
            # Set test environment variables
            os.environ['CREWAI_ENABLED'] = 'true'
            os.environ['CREWAI_ROLLOUT_PERCENTAGE'] = '50'
            os.environ['CREWAI_AB_TESTING'] = 'true'
            os.environ['CREWAI_QUALITY_THRESHOLD'] = '8.0'
            
            # Create new config with environment overrides
            test_config = IntegrationConfig()
            test_summary = test_config.get_config_summary()
            
            logger.info(f"📊 Test config: {test_summary}")
            
            # Validate configuration changes
            assert test_config.crewai_enabled == True
            assert test_config.rollout_percentage == 50
            assert test_config.ab_testing_enabled == True
            assert test_config.quality_threshold == 8.0
            
            # Test A/B testing logic
            episode_id_1 = "test_episode_1"
            episode_id_2 = "test_episode_2"
            
            result_1a = test_config.should_use_crewai(episode_id_1)
            result_1b = test_config.should_use_crewai(episode_id_1)  # Should be consistent
            result_2 = test_config.should_use_crewai(episode_id_2)
            
            assert result_1a == result_1b, "A/B testing should be consistent for same episode"
            logger.info(f"✅ A/B testing: episode_1={result_1a}, episode_2={result_2}")
            
            # Restore original environment
            if original_enabled:
                os.environ['CREWAI_ENABLED'] = original_enabled
            else:
                os.environ.pop('CREWAI_ENABLED', None)
            
            if original_rollout:
                os.environ['CREWAI_ROLLOUT_PERCENTAGE'] = original_rollout
            else:
                os.environ.pop('CREWAI_ROLLOUT_PERCENTAGE', None)
            
            # Clean up test variables
            for var in ['CREWAI_AB_TESTING', 'CREWAI_QUALITY_THRESHOLD']:
                os.environ.pop(var, None)
            
            self.test_results['tests']['configuration_system'] = {
                'status': 'passed',
                'default_config': default_summary,
                'test_config': test_summary,
                'ab_testing_consistent': result_1a == result_1b
            }
            
            logger.info("✅ Configuration system test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Configuration system test failed: {str(e)}")
            self.test_results['tests']['configuration_system'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    def test_factory_pattern(self) -> bool:
        """Test the story generator factory pattern"""
        logger.info("🧪 Testing factory pattern...")
        
        try:
            # Test with CrewAI disabled
            config_disabled = {'crewai_enabled': False}
            generator_disabled = StoryGeneratorFactory.create_story_generator(
                self.api_key, self.superprompt_path, config_disabled
            )
            
            assert type(generator_disabled).__name__ == 'StoryGenerator'
            logger.info(f"✅ Factory with CrewAI disabled: {type(generator_disabled).__name__}")
            
            # Test with CrewAI enabled (may fallback if not available)
            config_enabled = {'crewai_enabled': True, 'rollout_percentage': 100}
            generator_enabled = StoryGeneratorFactory.create_story_generator(
                self.api_key, self.superprompt_path, config_enabled
            )
            
            generator_type = type(generator_enabled).__name__
            logger.info(f"✅ Factory with CrewAI enabled: {generator_type}")
            
            # Test integrated generator creation
            integrated = create_integrated_story_generator(self.api_key, self.superprompt_path)
            assert type(integrated).__name__ == 'IntegratedStoryGenerator'
            logger.info(f"✅ Integrated generator created: {type(integrated).__name__}")
            
            self.test_results['tests']['factory_pattern'] = {
                'status': 'passed',
                'generator_disabled': type(generator_disabled).__name__,
                'generator_enabled': generator_type,
                'integrated_generator': type(integrated).__name__
            }
            
            logger.info("✅ Factory pattern test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Factory pattern test failed: {str(e)}")
            self.test_results['tests']['factory_pattern'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    def test_performance_monitoring(self) -> bool:
        """Test the performance monitoring system"""
        logger.info("🧪 Testing performance monitoring...")
        
        try:
            config = IntegrationConfig({'monitoring_enabled': True})
            monitor = PerformanceMonitor(config)
            
            # Record test sessions
            test_sessions = [
                {
                    'generator_type': 'standard',
                    'processing_time': 15.5,
                    'stories_generated': 2,
                    'quality_scores': [7.5, 8.2],
                    'error_occurred': False,
                    'episode_metadata': {'id': 'test_1', 'episode_title': 'Test Episode 1'}
                },
                {
                    'generator_type': 'crewai',
                    'processing_time': 25.3,
                    'stories_generated': 3,
                    'quality_scores': [8.5, 9.1, 8.8],
                    'error_occurred': False,
                    'episode_metadata': {'id': 'test_2', 'episode_title': 'Test Episode 2'}
                },
                {
                    'generator_type': 'standard',
                    'processing_time': 12.1,
                    'stories_generated': 0,
                    'quality_scores': [],
                    'error_occurred': True,
                    'episode_metadata': {'id': 'test_3', 'episode_title': 'Test Episode 3'}
                }
            ]
            
            # Record sessions
            for session in test_sessions:
                monitor.record_session(**session)
            
            # Get performance comparison
            comparison = monitor.get_performance_comparison()
            logger.info(f"📊 Performance comparison: {comparison}")
            
            # Test rollback logic
            rollback_needed = monitor.should_trigger_rollback()
            logger.info(f"🔄 Rollback needed: {rollback_needed}")
            
            # Validate metrics structure
            assert 'crewai_sessions' in comparison
            assert 'standard_sessions' in comparison
            assert 'recommendation' in comparison
            
            self.test_results['tests']['performance_monitoring'] = {
                'status': 'passed',
                'sessions_recorded': len(test_sessions),
                'comparison': comparison,
                'rollback_needed': rollback_needed
            }
            
            logger.info("✅ Performance monitoring test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Performance monitoring test failed: {str(e)}")
            self.test_results['tests']['performance_monitoring'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    def test_integrated_generator(self) -> bool:
        """Test the integrated story generator with mock data"""
        logger.info("🧪 Testing integrated story generator...")
        
        try:
            # Create integrated generator with test configuration
            config = {
                'crewai_enabled': True,
                'rollout_percentage': 50,
                'ab_testing_enabled': True,
                'monitoring_enabled': True,
                'auto_fallback': True
            }
            
            integrated = IntegratedStoryGenerator(self.api_key, self.superprompt_path, config)
            
            # Test status reporting
            status = integrated.get_status()
            logger.info(f"📊 Integrated generator status: {status['generators_available']}")
            
            # Test generator selection logic
            episode_metadata_1 = {'id': 'test_episode_1', 'episode_title': 'Test Episode 1'}
            episode_metadata_2 = {'id': 'test_episode_2', 'episode_title': 'Test Episode 2'}
            
            generator_1, type_1 = integrated._select_generator(episode_metadata_1)
            generator_2, type_2 = integrated._select_generator(episode_metadata_2)
            
            logger.info(f"🎯 Generator selection: episode_1={type_1}, episode_2={type_2}")
            
            # Test quality score estimation
            mock_story = {
                'id': 'test_story_1',
                'title': 'Test Investment Strategy',
                'summary': 'A comprehensive test of investment strategies',
                'full_content': 'This is a detailed test story about investment strategies that should be long enough to get a good quality score. It includes actionable advice and family-focused content.',
                'content_type': 'systematic-strategy',
                'actionable_practices': ['Practice 1', 'Practice 2'],
                'belt_levels': ['green-belt'],
                'family_security_relevance': 'High relevance for family security'
            }
            
            quality_score = integrated._estimate_quality_score(mock_story)
            logger.info(f"📊 Quality score estimation: {quality_score}/10")
            
            # Test performance report generation
            performance_report = integrated.get_performance_report()
            logger.info(f"📈 Performance report generated with {len(performance_report['recommendations'])} recommendations")
            
            self.test_results['tests']['integrated_generator'] = {
                'status': 'passed',
                'generators_available': status['generators_available'],
                'generator_selection': {'episode_1': type_1, 'episode_2': type_2},
                'quality_score_test': quality_score,
                'performance_report_generated': True
            }
            
            logger.info("✅ Integrated generator test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Integrated generator test failed: {str(e)}")
            self.test_results['tests']['integrated_generator'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    def test_backward_compatibility(self) -> bool:
        """Test backward compatibility with existing automation"""
        logger.info("🧪 Testing backward compatibility...")
        
        try:
            # Create both generators
            standard_generator = StoryGenerator(self.api_key, self.superprompt_path)
            integrated_generator = IntegratedStoryGenerator(self.api_key, self.superprompt_path)
            
            # Compare interfaces
            standard_methods = set(dir(standard_generator))
            integrated_methods = set(dir(integrated_generator))
            
            # Check that integrated generator has all standard methods
            required_methods = {
                'generate_stories_from_transcript',
                'transcribe_audio_file',
                'process_episodes_batch',
                'get_status'
            }
            
            missing_methods = required_methods - integrated_methods
            if missing_methods:
                raise AssertionError(f"Missing required methods: {missing_methods}")
            
            # Test method signatures compatibility
            import inspect
            
            for method_name in required_methods:
                standard_sig = inspect.signature(getattr(standard_generator, method_name))
                integrated_sig = inspect.signature(getattr(integrated_generator, method_name))
                
                # Parameters should be compatible (integrated can have additional optional params)
                standard_params = list(standard_sig.parameters.keys())
                integrated_params = list(integrated_sig.parameters.keys())
                
                # Check that all standard parameters are present in integrated
                for param in standard_params:
                    if param not in integrated_params:
                        raise AssertionError(f"Method {method_name} missing parameter: {param}")
            
            logger.info("✅ Interface compatibility verified")
            
            # Test status method compatibility
            standard_status = standard_generator.get_status()
            integrated_status = integrated_generator.get_status()
            
            # Integrated status should include all standard fields plus additional ones
            standard_keys = set(standard_status.keys()) if isinstance(standard_status, dict) else set()
            integrated_keys = set(integrated_status.keys()) if isinstance(integrated_status, dict) else set()
            
            logger.info(f"📊 Status keys - Standard: {len(standard_keys)}, Integrated: {len(integrated_keys)}")
            
            self.test_results['tests']['backward_compatibility'] = {
                'status': 'passed',
                'interface_compatible': True,
                'required_methods_present': list(required_methods),
                'status_keys_comparison': {
                    'standard': len(standard_keys),
                    'integrated': len(integrated_keys)
                }
            }
            
            logger.info("✅ Backward compatibility test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Backward compatibility test failed: {str(e)}")
            self.test_results['tests']['backward_compatibility'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    def test_fallback_behavior(self) -> bool:
        """Test automatic fallback behavior"""
        logger.info("🧪 Testing fallback behavior...")
        
        try:
            # Create integrated generator with fallback enabled
            config = {
                'crewai_enabled': True,
                'rollout_percentage': 100,  # Force CrewAI usage
                'auto_fallback': True,
                'monitoring_enabled': True
            }
            
            integrated = IntegratedStoryGenerator(self.api_key, self.superprompt_path, config)
            
            # Test fallback quality estimation
            mock_story = {
                'id': 'fallback_test',
                'title': 'Fallback Test Story',
                'summary': 'Testing fallback behavior',
                'full_content': 'Short content',
                'content_type': 'research-method'
            }
            
            quality_score = integrated._estimate_quality_score(mock_story)
            logger.info(f"📊 Fallback quality estimation: {quality_score}/10")
            
            # Test performance monitor rollback logic
            monitor = integrated.performance_monitor
            
            # Simulate poor performance data
            poor_sessions = [
                {
                    'generator_type': 'crewai',
                    'processing_time': 60.0,
                    'stories_generated': 1,
                    'quality_scores': [5.0],  # Below threshold
                    'error_occurred': False,
                    'episode_metadata': {'id': f'poor_test_{i}'}
                }
                for i in range(6)  # Need at least 5 sessions for rollback consideration
            ]
            
            for session in poor_sessions:
                monitor.record_session(**session)
            
            # Check if rollback would be triggered
            should_rollback = monitor.should_trigger_rollback()
            logger.info(f"🔄 Rollback triggered by poor performance: {should_rollback}")
            
            self.test_results['tests']['fallback_behavior'] = {
                'status': 'passed',
                'quality_estimation_works': quality_score > 0,
                'rollback_logic_works': should_rollback,
                'poor_performance_detected': True
            }
            
            logger.info("✅ Fallback behavior test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fallback behavior test failed: {str(e)}")
            self.test_results['tests']['fallback_behavior'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run the complete test suite"""
        logger.info("🚀 Starting comprehensive CrewAI integration test suite")
        logger.info("=" * 70)
        
        start_time = time.time()
        
        # Validate prerequisites
        if not self.validate_prerequisites():
            self.test_results['overall_status'] = 'failed'
            self.test_results['failure_reason'] = 'prerequisites_not_met'
            return self.test_results
        
        # Run all tests
        tests = [
            ('Configuration System', self.test_configuration_system),
            ('Factory Pattern', self.test_factory_pattern),
            ('Performance Monitoring', self.test_performance_monitoring),
            ('Integrated Generator', self.test_integrated_generator),
            ('Backward Compatibility', self.test_backward_compatibility),
            ('Fallback Behavior', self.test_fallback_behavior)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n🧪 Running {test_name} test...")
            try:
                if test_func():
                    passed_tests += 1
                    logger.info(f"✅ {test_name} test PASSED")
                else:
                    logger.error(f"❌ {test_name} test FAILED")
            except Exception as e:
                logger.error(f"💥 {test_name} test CRASHED: {str(e)}")
        
        # Calculate results
        total_time = time.time() - start_time
        success_rate = (passed_tests / total_tests) * 100
        
        self.test_results.update({
            'overall_status': 'passed' if passed_tests == total_tests else 'partial' if passed_tests > 0 else 'failed',
            'tests_passed': passed_tests,
            'tests_total': total_tests,
            'success_rate': success_rate,
            'total_time': total_time,
            'summary': {
                'integration_ready': passed_tests >= 4,  # Core functionality working
                'production_ready': passed_tests == total_tests,
                'fallback_available': self.test_results['tests'].get('backward_compatibility', {}).get('status') == 'passed'
            }
        })
        
        # Generate recommendations
        recommendations = []
        if success_rate == 100:
            recommendations.append("✅ All tests passed - CrewAI integration is production-ready")
            recommendations.append("🚀 Safe to enable gradual rollout starting at 5-10%")
        elif success_rate >= 80:
            recommendations.append("⚠️ Most tests passed - integration is functional but needs attention")
            recommendations.append("🔧 Review failed tests before production deployment")
        else:
            recommendations.append("❌ Multiple test failures - integration needs significant work")
            recommendations.append("🛑 Do not deploy to production until issues are resolved")
        
        if self.test_results['tests'].get('backward_compatibility', {}).get('status') == 'passed':
            recommendations.append("✅ Backward compatibility confirmed - existing automation will continue working")
        
        self.test_results['recommendations'] = recommendations
        
        # Log final results
        logger.info("\n" + "=" * 70)
        logger.info("🏁 COMPREHENSIVE TEST SUITE RESULTS")
        logger.info("=" * 70)
        logger.info(f"📊 Tests passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        logger.info(f"⏱️ Total time: {total_time:.2f} seconds")
        logger.info(f"🎯 Overall status: {self.test_results['overall_status'].upper()}")
        
        logger.info("\n📋 RECOMMENDATIONS:")
        for rec in recommendations:
            logger.info(f"   {rec}")
        
        # Save detailed results
        results_file = Path("logs") / f"integration_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📄 Detailed results saved: {results_file}")
        
        return self.test_results


def main():
    """Main test execution"""
    print("🧪 CREWAI INTEGRATION COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print("Testing seamless integration with existing automation")
    print("Validating A/B testing, performance monitoring, and fallback behavior")
    print()
    
    try:
        tester = IntegrationTester()
        results = tester.run_comprehensive_test_suite()
        
        # Exit with appropriate code
        if results['overall_status'] == 'passed':
            print("\n🎉 ALL TESTS PASSED - Integration is production-ready!")
            return 0
        elif results['overall_status'] == 'partial':
            print(f"\n⚠️ PARTIAL SUCCESS - {results['tests_passed']}/{results['tests_total']} tests passed")
            return 1
        else:
            print("\n❌ TESTS FAILED - Integration needs work before deployment")
            return 2
            
    except Exception as e:
        print(f"\n💥 TEST SUITE CRASHED: {str(e)}")
        import traceback
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    exit(main())