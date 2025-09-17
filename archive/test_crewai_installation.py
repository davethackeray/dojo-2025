#!/usr/bin/env python3
"""
CREWAI INSTALLATION TEST SCRIPT
Comprehensive testing of CrewAI framework integration with InvestingDojo automation
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def setup_test_logging():
    """Setup logging for test script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/crewai_test.log', mode='w')
        ]
    )
    return logging.getLogger(__name__)

def test_environment_setup() -> Dict[str, Any]:
    """Test environment setup and requirements"""
    logger = logging.getLogger(__name__)
    results = {
        'environment': {
            'python_version': sys.version,
            'working_directory': str(Path.cwd()),
            'project_root': str(project_root)
        },
        'tests': {},
        'errors': [],
        'warnings': []
    }
    
    logger.info("🧪 TESTING ENVIRONMENT SETUP")
    logger.info("=" * 50)
    
    # Test 1: Check Python version
    try:
        python_version = sys.version_info
        if python_version >= (3, 8):
            results['tests']['python_version'] = 'PASS'
            logger.info(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            results['tests']['python_version'] = 'FAIL'
            results['errors'].append(f"Python {python_version.major}.{python_version.minor} too old, need 3.8+")
            logger.error(f"❌ Python version too old: {python_version}")
    except Exception as e:
        results['tests']['python_version'] = 'ERROR'
        results['errors'].append(f"Python version check failed: {str(e)}")
    
    # Test 2: Check environment variables
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            results['tests']['gemini_api_key'] = 'PASS'
            logger.info("✅ GEMINI_API_KEY found")
        else:
            results['tests']['gemini_api_key'] = 'FAIL'
            results['errors'].append("GEMINI_API_KEY not found in environment")
            logger.error("❌ GEMINI_API_KEY not found")
        
        crewai_enabled = os.getenv('CREWAI_ENABLED', 'false').lower()
        results['environment']['crewai_enabled'] = crewai_enabled
        logger.info(f"📊 CREWAI_ENABLED: {crewai_enabled}")
        
    except Exception as e:
        results['tests']['environment_vars'] = 'ERROR'
        results['errors'].append(f"Environment variable check failed: {str(e)}")
    
    # Test 3: Check required files
    try:
        required_files = [
            'automation/SuperPrompt.md',
            'automation/requirements.txt',
            'automation/crewai_config.py',
            'automation/crew_ai_story_generator.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if not missing_files:
            results['tests']['required_files'] = 'PASS'
            logger.info(f"✅ All required files present ({len(required_files)} files)")
        else:
            results['tests']['required_files'] = 'FAIL'
            results['errors'].append(f"Missing files: {missing_files}")
            logger.error(f"❌ Missing files: {missing_files}")
            
    except Exception as e:
        results['tests']['required_files'] = 'ERROR'
        results['errors'].append(f"File check failed: {str(e)}")
    
    return results

def test_dependency_imports() -> Dict[str, Any]:
    """Test importing all required dependencies"""
    logger = logging.getLogger(__name__)
    results = {'tests': {}, 'errors': [], 'warnings': []}
    
    logger.info("\n🔧 TESTING DEPENDENCY IMPORTS")
    logger.info("=" * 50)
    
    # Core dependencies
    dependencies = [
        ('google.generativeai', 'Google Gemini AI'),
        ('mysql.connector', 'MySQL Connector'),
        ('feedparser', 'RSS Feed Parser'),
        ('requests', 'HTTP Requests'),
        ('pydub', 'Audio Processing')
    ]
    
    # CrewAI dependencies
    crewai_dependencies = [
        ('crewai', 'CrewAI Framework'),
        ('crewai_tools', 'CrewAI Tools'),
        ('pydantic', 'Pydantic'),
        ('langchain', 'LangChain'),
        ('langchain_community', 'LangChain Community'),
        ('langchain_core', 'LangChain Core')
    ]
    
    # Test core dependencies
    for module, name in dependencies:
        try:
            __import__(module)
            results['tests'][f'import_{module}'] = 'PASS'
            logger.info(f"✅ {name}: imported successfully")
        except ImportError as e:
            results['tests'][f'import_{module}'] = 'FAIL'
            results['errors'].append(f"Failed to import {name}: {str(e)}")
            logger.error(f"❌ {name}: import failed - {str(e)}")
        except Exception as e:
            results['tests'][f'import_{module}'] = 'ERROR'
            results['errors'].append(f"Error importing {name}: {str(e)}")
            logger.error(f"💥 {name}: unexpected error - {str(e)}")
    
    # Test CrewAI dependencies
    logger.info("\n🤖 Testing CrewAI Dependencies:")
    for module, name in crewai_dependencies:
        try:
            __import__(module)
            results['tests'][f'import_{module}'] = 'PASS'
            logger.info(f"✅ {name}: imported successfully")
        except ImportError as e:
            results['tests'][f'import_{module}'] = 'FAIL'
            results['warnings'].append(f"CrewAI dependency missing: {name} - {str(e)}")
            logger.warning(f"⚠️ {name}: import failed - {str(e)}")
        except Exception as e:
            results['tests'][f'import_{module}'] = 'ERROR'
            results['errors'].append(f"Error importing {name}: {str(e)}")
            logger.error(f"💥 {name}: unexpected error - {str(e)}")
    
    return results

def test_crewai_configuration() -> Dict[str, Any]:
    """Test CrewAI configuration and setup"""
    logger = logging.getLogger(__name__)
    results = {'tests': {}, 'errors': [], 'warnings': []}
    
    logger.info("\n⚙️ TESTING CREWAI CONFIGURATION")
    logger.info("=" * 50)
    
    try:
        # Test CrewAI availability check
        from automation.crewai_config import is_crewai_available, create_crewai_config
        
        available = is_crewai_available()
        results['tests']['crewai_available'] = 'PASS' if available else 'FAIL'
        
        if available:
            logger.info("✅ CrewAI is available and enabled")
        else:
            logger.warning("⚠️ CrewAI is not available or disabled")
            results['warnings'].append("CrewAI not available - will use fallback")
        
        # Test configuration creation
        try:
            config = create_crewai_config()
            results['tests']['config_creation'] = 'PASS'
            logger.info("✅ CrewAI configuration created successfully")
            
            # Test configuration methods
            env_info = config.get_environment_info()
            logger.info(f"📊 Environment info: {env_info}")
            
            # Test LLM configuration
            if config.is_enabled():
                llm = config.get_llm()
                results['tests']['llm_config'] = 'PASS'
                logger.info("✅ LLM configuration successful")
            else:
                results['tests']['llm_config'] = 'SKIP'
                logger.info("⏭️ LLM configuration skipped (CrewAI disabled)")
            
        except Exception as e:
            results['tests']['config_creation'] = 'FAIL'
            results['errors'].append(f"Configuration creation failed: {str(e)}")
            logger.error(f"❌ Configuration creation failed: {str(e)}")
        
    except ImportError as e:
        results['tests']['crewai_import'] = 'FAIL'
        results['errors'].append(f"Failed to import CrewAI config: {str(e)}")
        logger.error(f"❌ CrewAI config import failed: {str(e)}")
    except Exception as e:
        results['tests']['crewai_config'] = 'ERROR'
        results['errors'].append(f"CrewAI configuration test error: {str(e)}")
        logger.error(f"💥 CrewAI configuration test error: {str(e)}")
    
    return results

def test_story_generator_creation() -> Dict[str, Any]:
    """Test story generator creation and basic functionality"""
    logger = logging.getLogger(__name__)
    results = {'tests': {}, 'errors': [], 'warnings': []}
    
    logger.info("\n📝 TESTING STORY GENERATOR CREATION")
    logger.info("=" * 50)
    
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        superprompt_path = Path('automation/SuperPrompt.md')
        
        if not api_key:
            results['tests']['story_generator'] = 'SKIP'
            results['warnings'].append("Skipping story generator test - no API key")
            logger.warning("⏭️ Skipping story generator test - no API key")
            return results
        
        if not superprompt_path.exists():
            results['tests']['story_generator'] = 'FAIL'
            results['errors'].append("SuperPrompt.md not found")
            logger.error("❌ SuperPrompt.md not found")
            return results
        
        # Test CrewAI story generator
        try:
            from automation.crew_ai_story_generator import CrewAIStoryGenerator, create_story_generator
            
            # Test factory function
            generator = create_story_generator(api_key, superprompt_path, use_crewai=True)
            results['tests']['generator_creation'] = 'PASS'
            logger.info("✅ Story generator created successfully")
            
            # Test status method
            status = generator.get_status()
            logger.info(f"📊 Generator status: {status}")
            
            if status.get('crewai_enabled'):
                results['tests']['crewai_generator'] = 'PASS'
                logger.info("✅ CrewAI generator is enabled and ready")
            else:
                results['tests']['crewai_generator'] = 'FALLBACK'
                results['warnings'].append("Using fallback generator instead of CrewAI")
                logger.warning("⚠️ Using fallback generator instead of CrewAI")
            
        except Exception as e:
            results['tests']['generator_creation'] = 'FAIL'
            results['errors'].append(f"Story generator creation failed: {str(e)}")
            logger.error(f"❌ Story generator creation failed: {str(e)}")
        
    except ImportError as e:
        results['tests']['story_generator_import'] = 'FAIL'
        results['errors'].append(f"Failed to import story generator: {str(e)}")
        logger.error(f"❌ Story generator import failed: {str(e)}")
    except Exception as e:
        results['tests']['story_generator'] = 'ERROR'
        results['errors'].append(f"Story generator test error: {str(e)}")
        logger.error(f"💥 Story generator test error: {str(e)}")
    
    return results

def test_integration_with_existing_system() -> Dict[str, Any]:
    """Test integration with existing automation system"""
    logger = logging.getLogger(__name__)
    results = {'tests': {}, 'errors': [], 'warnings': []}
    
    logger.info("\n🔗 TESTING INTEGRATION WITH EXISTING SYSTEM")
    logger.info("=" * 50)
    
    try:
        # Test importing existing components
        from automation.story_generator import StoryGenerator
        from automation.podcast_harvester import PodcastHarvester
        
        results['tests']['existing_imports'] = 'PASS'
        logger.info("✅ Existing automation components imported successfully")
        
        # Test that CrewAI doesn't break existing functionality
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            superprompt_path = Path('automation/SuperPrompt.md')
            if superprompt_path.exists():
                # Test original StoryGenerator still works
                original_generator = StoryGenerator(api_key, superprompt_path)
                results['tests']['original_generator'] = 'PASS'
                logger.info("✅ Original StoryGenerator still functional")
                
                # Test factory function fallback
                from automation.crew_ai_story_generator import create_story_generator
                fallback_generator = create_story_generator(api_key, superprompt_path, use_crewai=False)
                results['tests']['fallback_generator'] = 'PASS'
                logger.info("✅ Fallback generator creation works")
            else:
                results['warnings'].append("SuperPrompt.md not found for integration test")
        else:
            results['warnings'].append("No API key for integration test")
        
    except ImportError as e:
        results['tests']['existing_imports'] = 'FAIL'
        results['errors'].append(f"Failed to import existing components: {str(e)}")
        logger.error(f"❌ Existing component import failed: {str(e)}")
    except Exception as e:
        results['tests']['integration'] = 'ERROR'
        results['errors'].append(f"Integration test error: {str(e)}")
        logger.error(f"💥 Integration test error: {str(e)}")
    
    return results

def generate_test_report(all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate comprehensive test report"""
    logger = logging.getLogger(__name__)
    
    # Combine all results
    combined_results = {
        'test_run': {
            'timestamp': datetime.now().isoformat(),
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'error_tests': 0,
            'skipped_tests': 0
        },
        'test_categories': {},
        'all_errors': [],
        'all_warnings': [],
        'recommendations': []
    }
    
    # Process each test category
    for i, result in enumerate(all_results):
        category_name = ['environment', 'dependencies', 'configuration', 'generator', 'integration'][i]
        combined_results['test_categories'][category_name] = result
        
        # Count test results
        for test_name, test_result in result.get('tests', {}).items():
            combined_results['test_run']['total_tests'] += 1
            
            if test_result == 'PASS':
                combined_results['test_run']['passed_tests'] += 1
            elif test_result == 'FAIL':
                combined_results['test_run']['failed_tests'] += 1
            elif test_result == 'ERROR':
                combined_results['test_run']['error_tests'] += 1
            elif test_result in ['SKIP', 'FALLBACK']:
                combined_results['test_run']['skipped_tests'] += 1
        
        # Collect errors and warnings
        combined_results['all_errors'].extend(result.get('errors', []))
        combined_results['all_warnings'].extend(result.get('warnings', []))
    
    # Generate recommendations
    if combined_results['test_run']['failed_tests'] > 0:
        combined_results['recommendations'].append("Install missing dependencies with: pip install -r automation/requirements.txt")
    
    if combined_results['test_run']['error_tests'] > 0:
        combined_results['recommendations'].append("Check error logs and fix configuration issues")
    
    if len(combined_results['all_warnings']) > 0:
        combined_results['recommendations'].append("Review warnings for potential issues")
    
    if not os.getenv('GEMINI_API_KEY'):
        combined_results['recommendations'].append("Set GEMINI_API_KEY environment variable")
    
    if os.getenv('CREWAI_ENABLED', 'false').lower() != 'true':
        combined_results['recommendations'].append("Set CREWAI_ENABLED=true to enable CrewAI functionality")
    
    # Calculate success rate
    total_tests = combined_results['test_run']['total_tests']
    passed_tests = combined_results['test_run']['passed_tests']
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    combined_results['test_run']['success_rate'] = success_rate
    
    # Determine overall status
    if success_rate >= 90:
        combined_results['test_run']['status'] = 'EXCELLENT'
    elif success_rate >= 75:
        combined_results['test_run']['status'] = 'GOOD'
    elif success_rate >= 50:
        combined_results['test_run']['status'] = 'NEEDS_ATTENTION'
    else:
        combined_results['test_run']['status'] = 'CRITICAL'
    
    return combined_results

def main():
    """Main test execution"""
    print("🚀 CREWAI INSTALLATION TEST SUITE")
    print("=" * 60)
    print("InvestingDojo.co - CrewAI Framework Integration Test")
    print()
    
    # Setup logging
    Path('logs').mkdir(exist_ok=True)
    logger = setup_test_logging()
    
    try:
        # Run all test categories
        test_results = []
        
        logger.info("Starting comprehensive CrewAI installation test...")
        
        # Test 1: Environment Setup
        test_results.append(test_environment_setup())
        
        # Test 2: Dependency Imports
        test_results.append(test_dependency_imports())
        
        # Test 3: CrewAI Configuration
        test_results.append(test_crewai_configuration())
        
        # Test 4: Story Generator Creation
        test_results.append(test_story_generator_creation())
        
        # Test 5: Integration Testing
        test_results.append(test_integration_with_existing_system())
        
        # Generate comprehensive report
        final_report = generate_test_report(test_results)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Path(f"logs/crewai_test_report_{timestamp}.json")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        # Print summary
        logger.info("\n📊 FINAL TEST REPORT")
        logger.info("=" * 50)
        logger.info(f"🎯 Overall Status: {final_report['test_run']['status']}")
        logger.info(f"✅ Tests Passed: {final_report['test_run']['passed_tests']}/{final_report['test_run']['total_tests']}")
        logger.info(f"📈 Success Rate: {final_report['test_run']['success_rate']:.1f}%")
        logger.info(f"❌ Errors: {len(final_report['all_errors'])}")
        logger.info(f"⚠️ Warnings: {len(final_report['all_warnings'])}")
        
        if final_report['recommendations']:
            logger.info("\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(final_report['recommendations'], 1):
                logger.info(f"  {i}. {rec}")
        
        logger.info(f"\n📄 Full report saved: {report_file}")
        
        # Return success/failure
        return final_report['test_run']['status'] in ['EXCELLENT', 'GOOD']
        
    except Exception as e:
        logger.error(f"💥 CRITICAL TEST FAILURE: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)