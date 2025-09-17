#!/usr/bin/env python3
"""
TEST CREWAI ACTIVATION
Check why CrewAI isn't being activated even when CREWAI_ENABLED=true
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_crewai_availability():
    """Test if CrewAI is actually available"""
    print("🔍 Testing CrewAI availability...")
    
    try:
        import crewai
        print(f"✅ CrewAI imported successfully: {crewai.__version__ if hasattr(crewai, '__version__') else 'version unknown'}")
        crewai_available = True
    except ImportError as e:
        print(f"❌ CrewAI not available: {str(e)}")
        crewai_available = False
    
    try:
        from automation.crew_ai_story_generator import CrewAIStoryGenerator
        print("✅ CrewAIStoryGenerator imported successfully")
        generator_available = True
    except ImportError as e:
        print(f"❌ CrewAIStoryGenerator not available: {str(e)}")
        generator_available = False
    
    return crewai_available and generator_available

def test_integration_config():
    """Test the integration configuration"""
    print("⚙️ Testing integration configuration...")
    
    try:
        from automation.crewai_integration import IntegrationConfig
        
        # Test with CrewAI enabled
        os.environ['CREWAI_ENABLED'] = 'true'
        os.environ['CREWAI_ROLLOUT_PERCENTAGE'] = '100'  # Set to 100% for testing
        
        config = IntegrationConfig()
        
        print(f"CrewAI Enabled: {config.crewai_enabled}")
        print(f"Rollout Percentage: {config.rollout_percentage}")
        print(f"Should use CrewAI: {config.should_use_crewai()}")
        
        summary = config.get_config_summary()
        print(f"Config Summary: {summary}")
        
        return config.should_use_crewai()
        
    except Exception as e:
        print(f"❌ Integration config test failed: {str(e)}")
        return False

def test_factory_with_rollout():
    """Test factory with proper rollout configuration"""
    print("🏭 Testing factory with rollout configuration...")
    
    try:
        from automation.crewai_integration import StoryGeneratorFactory
        
        # Set environment for CrewAI activation
        os.environ['CREWAI_ENABLED'] = 'true'
        os.environ['CREWAI_ROLLOUT_PERCENTAGE'] = '100'
        
        # Find SuperPrompt file
        automation_dir = Path(__file__).parent
        superprompt_path = None
        
        possible_paths = [
            automation_dir / "SuperPrompt_Optimized.md",
            automation_dir / "SuperPrompt.md"
        ]
        
        for path in possible_paths:
            if path.exists():
                superprompt_path = path
                break
        
        if not superprompt_path:
            print("❌ No SuperPrompt file found")
            return False
        
        # Create generator with explicit config
        config = {'crewai_enabled': True, 'rollout_percentage': 100}
        generator = StoryGeneratorFactory.create_story_generator(
            api_key='test_key',
            superprompt_path=superprompt_path,
            config=config
        )
        
        generator_type = type(generator).__name__
        print(f"✅ Factory created: {generator_type}")
        
        # Check if it's the CrewAI generator
        is_crewai = 'CrewAI' in generator_type or 'Integrated' in generator_type
        print(f"Is CrewAI generator: {is_crewai}")
        
        return is_crewai
        
    except Exception as e:
        print(f"❌ Factory test with rollout failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_integrated_generator():
    """Test the IntegratedStoryGenerator directly"""
    print("🔗 Testing IntegratedStoryGenerator...")
    
    try:
        from automation.crewai_integration import IntegratedStoryGenerator
        
        # Set environment for CrewAI activation
        os.environ['CREWAI_ENABLED'] = 'true'
        os.environ['CREWAI_ROLLOUT_PERCENTAGE'] = '100'
        
        # Find SuperPrompt file
        automation_dir = Path(__file__).parent
        superprompt_path = None
        
        possible_paths = [
            automation_dir / "SuperPrompt_Optimized.md",
            automation_dir / "SuperPrompt.md"
        ]
        
        for path in possible_paths:
            if path.exists():
                superprompt_path = path
                break
        
        if not superprompt_path:
            print("❌ No SuperPrompt file found")
            return False
        
        # Create integrated generator
        config = {'crewai_enabled': True, 'rollout_percentage': 100}
        generator = IntegratedStoryGenerator(
            api_key='test_key',
            superprompt_path=superprompt_path,
            config=config
        )
        
        status = generator.get_status()
        print(f"✅ IntegratedStoryGenerator created")
        print(f"Generators available: {status['generators_available']}")
        print(f"Config: {status['config']}")
        
        return status['generators_available']['crewai']
        
    except Exception as e:
        print(f"❌ IntegratedStoryGenerator test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all activation tests"""
    print("🧪 CREWAI ACTIVATION TESTING")
    print("=" * 40)
    
    tests = [
        ("CrewAI Availability", test_crewai_availability),
        ("Integration Config", test_integration_config),
        ("Factory with Rollout", test_factory_with_rollout),
        ("IntegratedStoryGenerator", test_integrated_generator)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n📊 ACTIVATION TEST RESULTS")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if results.get("CrewAI Availability", False):
        print("🎉 CrewAI is properly installed and available!")
    else:
        print("⚠️ CrewAI is not installed - this explains why it's not being used")
        print("💡 To enable CrewAI: pip install crewai")
    
    return passed >= 2  # At least basic functionality should work

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)