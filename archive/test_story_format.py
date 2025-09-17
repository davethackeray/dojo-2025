#!/usr/bin/env python3
"""
TEST STORY FORMAT
Quick test to verify the story generation format issue
"""

import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_story_format():
    """Test the story format parsing"""
    
    # Sample response that might come from AI (simplified)
    sample_ai_response = {
        "investing-dojo-stories": [
            {
                "id": "test-story-format",
                "title": "Test story for format validation",
                "content": "This is test content",
                "belt_level": "white-belt"
            }
        ]
    }
    
    # Test the validation logic from story_generator.py
    def validate_stories(stories_data):
        """Replicate the validation logic"""
        # Check for both possible JSON formats
        stories = None
        if isinstance(stories_data, dict):
            if 'investing-dojo-stories' in stories_data:
                stories = stories_data['investing-dojo-stories']
                logger.info("✅ Found 'investing-dojo-stories' key")
            elif 'stories' in stories_data:
                stories = stories_data['stories']
                logger.info("✅ Found 'stories' key")
            else:
                logger.warning("❌ Invalid stories format - expected dict with 'investing-dojo-stories' or 'stories' key")
                logger.debug(f"Available keys: {list(stories_data.keys())}")
                return []
        else:
            logger.warning("❌ Invalid stories format - expected dict")
            return []
        
        if not isinstance(stories, list):
            logger.warning("❌ Invalid stories format - 'stories' should be a list")
            return []
        
        logger.info(f"✅ Found {len(stories)} stories")
        return stories
    
    # Test with correct format
    logger.info("Testing with 'investing-dojo-stories' format:")
    result = validate_stories(sample_ai_response)
    logger.info(f"Result: {len(result)} stories found")
    
    # Test with old format
    logger.info("\nTesting with 'stories' format:")
    old_format = {"stories": sample_ai_response["investing-dojo-stories"]}
    result = validate_stories(old_format)
    logger.info(f"Result: {len(result)} stories found")
    
    # Test with invalid format
    logger.info("\nTesting with invalid format:")
    invalid_format = {"invalid_key": []}
    result = validate_stories(invalid_format)
    logger.info(f"Result: {len(result)} stories found")

if __name__ == "__main__":
    test_story_format()