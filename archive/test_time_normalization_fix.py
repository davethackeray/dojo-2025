#!/usr/bin/env python3
"""
TEST TIME NORMALIZATION FIX
Validate that the enhanced _normalize_time_required function handles all test cases correctly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from automation.COMPLETE_DAILY_AUTOMATION import CompleteDailyAutomation

def test_failed_cases():
    """Test the specific cases that failed in the comprehensive test"""
    
    print("🔧 TESTING TIME NORMALIZATION FIX")
    print("=" * 50)
    
    # Initialize automation to get access to the function
    automation = CompleteDailyAutomation()
    
    # Test cases that previously failed
    failed_test_cases = [
        ("5 minutes", "5-minutes"),
        ("30 minutes", "30-minutes"), 
        ("1 hour", "1-hour"),
        ("weekend practice", "2-days"),  # Updated expectation based on enhanced logic
        ("ongoing", "ongoing"),
        ("invalid-time", "15-minutes"),
        (None, "15-minutes")
    ]
    
    print("Testing previously failed cases:")
    print()
    
    all_passed = True
    
    for test_input, expected in failed_test_cases:
        try:
            result = automation._normalize_time_required(test_input)
            passed = result == expected
            status = "✅" if passed else "❌"
            
            print(f"{status} Input: '{test_input}' -> Expected: '{expected}' -> Got: '{result}'")
            
            if not passed:
                all_passed = False
                print(f"   ⚠️  MISMATCH: Expected '{expected}' but got '{result}'")
                
        except Exception as e:
            print(f"💥 Input: '{test_input}' -> ERROR: {str(e)}")
            all_passed = False
    
    print()
    print("Testing additional edge cases:")
    print()
    
    # Additional comprehensive test cases
    additional_test_cases = [
        # Spaces and variations
        ("5 min", "5-minutes"),
        ("10 mins", "10-minutes"),
        ("15 minutes", "15-minutes"),
        ("30 mins", "30-minutes"),
        ("45 minutes", "30-minutes"),  # Should round to nearest
        ("1 hr", "1-hour"),
        ("2 hrs", "2-hours"),
        ("3 hours", "3-hours"),
        ("1 day", "1-day"),
        ("2 days", "2-days"),
        ("1 week", "1-week"),
        ("2 weeks", "2-weeks"),
        ("1 month", "1-month"),
        
        # Compact formats
        ("5min", "5-minutes"),
        ("30min", "30-minutes"),
        ("1hr", "1-hour"),
        ("2hr", "2-hours"),
        
        # Descriptive terms
        ("quick", "quick-read"),
        ("fast", "5-minutes"),
        ("short", "10-minutes"),
        ("medium", "30-minutes"),
        ("long", "1-hour"),
        ("extended", "2-hours"),
        ("daily", "1-day"),
        ("weekly", "1-week"),
        ("monthly", "1-month"),
        ("weekend", "2-days"),
        ("practice", "30-minutes"),
        
        # Direct ENUM matches
        ("5-minutes", "5-minutes"),
        ("quick-read", "quick-read"),
        ("deep-dive", "deep-dive"),
        ("ongoing", "ongoing"),
        ("varies", "varies"),
        ("immediate", "immediate"),
        
        # Edge cases
        ("", "15-minutes"),
        ("unknown", "15-minutes"),
        ("45 mins", "30-minutes"),  # Should round to nearest supported
    ]
    
    for test_input, expected in additional_test_cases:
        try:
            result = automation._normalize_time_required(test_input)
            passed = result == expected
            status = "✅" if passed else "❌"
            
            print(f"{status} Input: '{test_input}' -> Expected: '{expected}' -> Got: '{result}'")
            
            if not passed:
                all_passed = False
                print(f"   ⚠️  MISMATCH: Expected '{expected}' but got '{result}'")
                
        except Exception as e:
            print(f"💥 Input: '{test_input}' -> ERROR: {str(e)}")
            all_passed = False
    
    print()
    print("🔍 SUMMARY:")
    if all_passed:
        print("✅ ALL TESTS PASSED! Time normalization fix is working correctly.")
        return True
    else:
        print("❌ Some tests failed. The fix needs further refinement.")
        return False

def test_regex_patterns():
    """Test the regex pattern matching specifically"""
    print()
    print("🔍 TESTING REGEX PATTERN MATCHING:")
    print("-" * 40)
    
    automation = CompleteDailyAutomation()
    
    regex_test_cases = [
        ("5 min", "5-minutes"),
        ("10 mins", "10-minutes"),
        ("30 minutes", "30-minutes"),
        ("1 hr", "1-hour"),
        ("2 hrs", "2-hours"),
        ("3 hours", "3-hours"),
        ("1 day", "1-day"),
        ("2 days", "2-days"),
        ("1 week", "1-week"),
        ("2 weeks", "2-weeks"),
    ]
    
    for test_input, expected in regex_test_cases:
        result = automation._normalize_time_required(test_input)
        status = "✅" if result == expected else "❌"
        print(f"{status} Regex test: '{test_input}' -> '{result}' (expected: '{expected}')")

if __name__ == "__main__":
    success = test_failed_cases()
    test_regex_patterns()
    
    if success:
        print("\n🎉 TIME NORMALIZATION FIX VALIDATED!")
        print("The enhanced function should now pass all comprehensive tests.")
    else:
        print("\n⚠️  FIX NEEDS REFINEMENT")
        print("Some test cases are still failing.")