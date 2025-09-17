#!/usr/bin/env python3
"""
DEBUG TIME NORMALIZATION ISSUE
Test the _normalize_time_required function to identify why it's failing
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from automation.COMPLETE_DAILY_AUTOMATION import CompleteDailyAutomation

def test_time_normalization():
    """Test the time normalization function with various inputs"""
    
    print("🔍 DEBUGGING TIME NORMALIZATION FUNCTION")
    print("=" * 50)
    
    # Initialize automation to get access to the function
    automation = CompleteDailyAutomation()
    
    # Test cases that should work
    test_cases = [
        # Direct matches
        "5-minutes",
        "10-minutes", 
        "15-minutes",
        "30-minutes",
        "1-hour",
        "2-hours",
        "quick-read",
        "deep-dive",
        
        # Fuzzy matches
        "5min",
        "10min",
        "15min", 
        "30min",
        "1hr",
        "2hr",
        "quick",
        "fast",
        "short",
        "medium",
        "long",
        "extended",
        "daily",
        "weekly",
        "monthly",
        
        # Edge cases
        "",
        None,
        "unknown_value",
        "45 minutes",
        "3.5 hours"
    ]
    
    print("Testing normalization function:")
    print()
    
    for test_input in test_cases:
        try:
            result = automation._normalize_time_required(test_input)
            status = "✅" if result != "15-minutes" or test_input in ["15-minutes", "", None] else "❌"
            print(f"{status} Input: '{test_input}' -> Output: '{result}'")
        except Exception as e:
            print(f"💥 Input: '{test_input}' -> ERROR: {str(e)}")
    
    print()
    print("Supported values from config:")
    for value in automation.config['supported_time_required_values']:
        print(f"  - {value}")
    
    print()
    print("🔍 ANALYSIS:")
    
    # Test specific problematic cases
    problematic_inputs = ["5min", "1hr", "quick", "short"]
    
    for test_input in problematic_inputs:
        result = automation._normalize_time_required(test_input)
        expected_mapping = {
            "5min": "5-minutes",
            "1hr": "1-hour", 
            "quick": "quick-read",
            "short": "10-minutes"
        }
        expected = expected_mapping.get(test_input, "15-minutes")
        
        if result == expected:
            print(f"✅ '{test_input}' correctly mapped to '{result}'")
        else:
            print(f"❌ '{test_input}' should map to '{expected}' but got '{result}'")
            
            # Debug the function step by step
            print(f"   Debug for '{test_input}':")
            time_lower = str(test_input).lower().strip()
            print(f"   - Lowercase: '{time_lower}'")
            
            # Check direct matches
            supported_values = automation.config.get('supported_time_required_values', [])
            direct_match = None
            for supported in supported_values:
                if time_lower == supported.lower():
                    direct_match = supported
                    break
            print(f"   - Direct match: {direct_match}")
            
            # Check fuzzy matches
            time_mappings = {
                '5min': '5-minutes',
                '10min': '10-minutes',
                '15min': '15-minutes',
                '30min': '30-minutes',
                '1hr': '1-hour',
                '2hr': '2-hours',
                'quick': 'quick-read',
                'fast': '5-minutes',
                'short': '10-minutes',
                'medium': '30-minutes',
                'long': '1-hour',
                'extended': '2-hours',
                'daily': '1-day',
                'weekly': '1-week',
                'monthly': '1-month'
            }
            
            fuzzy_match = None
            for pattern, normalized in time_mappings.items():
                if pattern in time_lower:
                    fuzzy_match = normalized
                    break
            print(f"   - Fuzzy match: {fuzzy_match}")

if __name__ == "__main__":
    test_time_normalization()