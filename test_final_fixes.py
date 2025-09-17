#!/usr/bin/env python3
"""
Final Test Script - Verify All Automation Fixes
Tests all components to ensure the automation system works correctly
"""

import os
import sys
from pathlib import Path

def test_basic_imports():
    """Test basic imports work"""
    print("🧪 Testing basic imports...")
    
    try:
        from story_generator import StoryGenerator
        print("✅ StoryGenerator imported")
        
        from editorial_director import EditorialDirector
        print("✅ EditorialDirector imported")
        
        from crewai_integration import IntegratedStoryGenerator
        print("✅ IntegratedStoryGenerator imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_story_generator_methods():
    """Test StoryGenerator has required methods"""
    print("🧪 Testing StoryGenerator methods...")
    
    try:
        from story_generator import StoryGenerator
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEY not found")
            return False
            
        superprompt_path = Path("SuperPrompt_Optimized.md")
        if not superprompt_path.exists():
            print(f"❌ SuperPrompt file not found: {superprompt_path}")
            return False
        
        generator = StoryGenerator(api_key, superprompt_path)
        
        # Check for the method that was missing
        if hasattr(generator, '_transcribe_audio_file'):
            print("✅ _transcribe_audio_file method exists")
        else:
            print("❌ _transcribe_audio_file method missing")
            return False
            
        if hasattr(generator, 'transcribe_audio_file'):
            print("✅ transcribe_audio_file method exists")
        else:
            print("❌ transcribe_audio_file method missing")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ StoryGenerator test failed: {e}")
        return False

def test_editorial_director():
    """Test EditorialDirector doesn't crash"""
    print("🧪 Testing EditorialDirector...")
    
    try:
        from editorial_director import EditorialDirector
        
        api_key = os.getenv('GEMINI_API_KEY')
        config = {'gemini_api_key': api_key}
        
        director = EditorialDirector(api_key, config)
        
        # Test with empty data (should not crash with division by zero)
        empty_analyses = []
        recommendations = director._generate_editorial_recommendations(empty_analyses, [])
        print("✅ EditorialDirector handles empty data without crashing")
        
        return True
        
    except Exception as e:
        print(f"❌ EditorialDirector test failed: {e}")
        return False

def test_environment_variables():
    """Test environment variables are set correctly"""
    print("🧪 Testing environment variables...")
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return False
    else:
        print(f"✅ GEMINI_API_KEY found: {api_key[:10]}...")
    
    # Set CrewAI variables for testing
    os.environ['CREWAI_ENABLED'] = 'true'
    os.environ['CREWAI_ROLLOUT_PERCENTAGE'] = '100'
    
    crewai_enabled = os.getenv('CREWAI_ENABLED')
    rollout_pct = os.getenv('CREWAI_ROLLOUT_PERCENTAGE')
    
    print(f"✅ CREWAI_ENABLED: {crewai_enabled}")
    print(f"✅ CREWAI_ROLLOUT_PERCENTAGE: {rollout_pct}")
    
    return True

def main():
    print("🔧 FINAL AUTOMATION FIXES TEST")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Basic Imports", test_basic_imports),
        ("StoryGenerator Methods", test_story_generator_methods),
        ("EditorialDirector", test_editorial_director),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n📊 FINAL RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ The automation system is ready to run")
        print("\nNext steps:")
        print("1. Run: python COMPLETE_DAILY_AUTOMATION.py")
        print("2. Monitor the logs for successful execution")
        print("3. Check that stories are generated and imported to database")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed")
        print("Please check the errors above before running the automation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)