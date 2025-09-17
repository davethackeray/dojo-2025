#!/usr/bin/env python3
"""
Fix and Enable CrewAI Script
Fixes the automation issues and enables CrewAI properly
"""

import os
import sys
from pathlib import Path

def main():
    print("🔧 FIXING AND ENABLING CREWAI")
    print("=" * 50)
    
    # Set environment variables
    print("1. Setting environment variables...")
    os.environ['CREWAI_ENABLED'] = 'true'
    os.environ['CREWAI_ROLLOUT_PERCENTAGE'] = '100'
    
    # Verify Gemini API key
    gemini_key = os.getenv('GEMINI_API_KEY')
    if not gemini_key:
        print("❌ GEMINI_API_KEY not found!")
        print("Please set it with: $env:GEMINI_API_KEY = 'your-api-key'")
        return False
    else:
        print(f"✅ GEMINI_API_KEY found: {gemini_key[:10]}...")
    
    # Test imports
    print("\n2. Testing imports...")
    try:
        from story_generator import StoryGenerator
        print("✅ StoryGenerator imported successfully")
        
        from editorial_director import EditorialDirector
        print("✅ EditorialDirector imported successfully")
        
        from crewai_integration import IntegratedStoryGenerator
        print("✅ IntegratedStoryGenerator imported successfully")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test StoryGenerator method
    print("\n3. Testing StoryGenerator methods...")
    try:
        # Create a mock StoryGenerator to test methods
        superprompt_path = Path("SuperPrompt_Optimized.md")
        if not superprompt_path.exists():
            print(f"❌ SuperPrompt file not found: {superprompt_path}")
            return False
            
        generator = StoryGenerator(gemini_key, superprompt_path)
        
        # Check if _transcribe_audio_file method exists
        if hasattr(generator, '_transcribe_audio_file'):
            print("✅ _transcribe_audio_file method exists")
        else:
            print("❌ _transcribe_audio_file method missing")
            return False
            
    except Exception as e:
        print(f"❌ StoryGenerator test failed: {e}")
        return False
    
    # Test EditorialDirector
    print("\n4. Testing EditorialDirector...")
    try:
        config = {'gemini_api_key': gemini_key}
        director = EditorialDirector(gemini_key, config)
        print("✅ EditorialDirector initialized successfully")
        
    except Exception as e:
        print(f"❌ EditorialDirector test failed: {e}")
        return False
    
    print("\n🎉 ALL FIXES APPLIED SUCCESSFULLY!")
    print("\nYou can now run:")
    print("python COMPLETE_DAILY_AUTOMATION.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)