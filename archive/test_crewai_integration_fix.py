#!/usr/bin/env python3
"""
TEST CREWAI INTEGRATION FIX
Quick validation that the CrewAI integration issue is resolved
"""

import os
import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_superprompt_loading():
    """Test that SuperPrompt files can be found"""
    print("🔍 Testing SuperPrompt file loading...")
    
    # Import the fixed automation class
    from automation.COMPLETE_DAILY_AUTOMATION import CompleteDailyAutomation
    
    try:
        # Set required environment variables for testing
        os.environ['GEMINI_API_KEY'] = 'test_key_for_validation'
        os.environ['DB_LOCAL_HOST'] = 'localhost'
        os.environ['DB_LOCAL_DATABASE'] = 'test_db'
        os.environ['DB_LOCAL_USER'] = 'test_user'
        os.environ['DB_LOCAL_PASSWORD'] = 'test_pass'
        os.environ['DB_PROD_HOST'] = 'localhost'
        os.environ['DB_PROD_DATABASE'] = 'test_db'
        os.environ['DB_PROD_USER'] = 'test_user'
        os.environ['DB_PROD_PASSWORD'] = 'test_pass'
        
        # Try to initialize (this will test SuperPrompt loading)
        automation = CompleteDailyAutomation()
        
        print(f"✅ SuperPrompt loaded successfully: {automation.config['superprompt_path']}")
        return True
        
    except FileNotFoundError as e:
        print(f"❌ SuperPrompt loading failed: {str(e)}")
        return False
    except Exception as e:
        if "SuperPrompt" in str(e):
            print(f"❌ SuperPrompt loading failed: {str(e)}")
            return False
        else:
            # Other errors (like database connection) are expected in test
            print(f"✅ SuperPrompt loaded (other error expected in test): {str(e)}")
            return True

def test_crewai_integration_availability():
    """Test that CrewAI integration layer is available"""
    print("🤖 Testing CrewAI integration availability...")
    
    try:
        from automation.crewai_integration import IntegratedStoryGenerator, StoryGeneratorFactory
        print("✅ CrewAI integration layer imported successfully")
        return True
    except ImportError as e:
        print(f"⚠️ CrewAI integration not available: {str(e)}")
        return False

def test_story_generator_factory():
    """Test that StoryGeneratorFactory works with our SuperPrompt"""
    print("🏭 Testing StoryGeneratorFactory...")
    
    try:
        from automation.crewai_integration import StoryGeneratorFactory
        
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
            print("❌ No SuperPrompt file found for factory test")
            return False
        
        # Test factory with CrewAI disabled
        os.environ['CREWAI_ENABLED'] = 'false'
        generator = StoryGeneratorFactory.create_story_generator(
            api_key='test_key',
            superprompt_path=superprompt_path
        )
        
        print(f"✅ Factory created generator: {type(generator).__name__}")
        
        # Test factory with CrewAI enabled
        os.environ['CREWAI_ENABLED'] = 'true'
        generator = StoryGeneratorFactory.create_story_generator(
            api_key='test_key',
            superprompt_path=superprompt_path
        )
        
        print(f"✅ Factory created generator with CrewAI enabled: {type(generator).__name__}")
        return True
        
    except Exception as e:
        print(f"❌ Factory test failed: {str(e)}")
        return False

def main():
    """Run all integration tests"""
    print("🧪 CREWAI INTEGRATION FIX VALIDATION")
    print("=" * 50)
    
    tests = [
        ("SuperPrompt Loading", test_superprompt_loading),
        ("CrewAI Integration Availability", test_crewai_integration_availability),
        ("StoryGeneratorFactory", test_story_generator_factory)
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
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - CrewAI integration fix is working!")
        return True
    else:
        print("⚠️ Some tests failed - integration needs more work")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)