#!/usr/bin/env python3
"""
TEST COMPLETE AUTOMATION SYSTEM
Validates the complete daily automation before production use

This script tests:
1. Configuration loading
2. Database connections (local and production)
3. API key validation
4. File system permissions
5. Import system functionality

Run this before enabling the daily automation at 9am!
"""

import os
import sys
import json
import mysql.connector
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_environment_setup():
    """Test basic environment setup"""
    print("🔧 Testing Environment Setup...")
    
    # Check GEMINI_API_KEY
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return False
    else:
        print(f"✅ GEMINI_API_KEY found: {api_key[:10]}...")
    
    # Check SuperPrompt exists
    superprompt_path = Path("automation/SuperPrompt.md")
    if not superprompt_path.exists():
        print("❌ SuperPrompt.md not found")
        return False
    else:
        print("✅ SuperPrompt.md found")
    
    # Check directories
    temp_dir = Path("temp_processing")
    temp_dir.mkdir(exist_ok=True)
    print("✅ temp_processing directory ready")
    
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    print("✅ logs directory ready")
    
    return True

def test_database_connections():
    """Test both local and production database connections"""
    print("\n💾 Testing Database Connections...")
    
    # Local database config
    local_config = {
        'host': 'localhost',
        'database': 'u219832816_investing_dojo',
        'user': 'u219832816_davethackeray',
        'password': 'ToTheM00n!',
        'charset': 'utf8mb4',
        'use_unicode': True,
        'autocommit': False
    }
    
    # Production database config
    production_config = {
        'host': 'srv1910.hstgr.io',
        'database': 'u219832816_investing_dojo',
        'user': 'u219832816_davethackeray',
        'password': 'ToTheM00n!',
        'charset': 'utf8mb4',
        'use_unicode': True,
        'autocommit': False
    }
    
    # Test local database
    try:
        print("  Testing local database connection...")
        connection = mysql.connector.connect(**local_config)
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM stories")
        local_count = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        print(f"  ✅ Local database connected - {local_count} stories found")
    except Exception as e:
        print(f"  ❌ Local database connection failed: {str(e)}")
        return False
    
    # Test production database
    try:
        print("  Testing production database connection...")
        connection = mysql.connector.connect(**production_config)
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM stories")
        production_count = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        print(f"  ✅ Production database connected - {production_count} stories found")
    except Exception as e:
        print(f"  ❌ Production database connection failed: {str(e)}")
        return False
    
    return True

def test_import_system():
    """Test the enhanced import system"""
    print("\n📥 Testing Import System...")
    
    try:
        # Test importing the enhanced importer
        import importlib.util
        import_file = project_root / "automation" / "import-to-devEnvironment.py"
        
        if not import_file.exists():
            print("❌ import-to-devEnvironment.py not found")
            return False
        
        spec = importlib.util.spec_from_file_location("import_to_devEnvironment", import_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        EnhancedContentImporter = module.EnhancedContentImporter
        
        print("✅ Enhanced importer loaded successfully")
        
        # Test creating a dummy JSON file
        test_data = {
            "investing-dojo-stories": [
                {
                    "id": "test_story_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "title": "Test Story for Automation Validation",
                    "content": "This is a test story to validate the automation system.",
                    "summary": "Test story summary for automation validation",
                    "full_content": "This is the full content of the test story to validate the automation system works correctly.",
                    "content_type": "story",
                    "belt_level": "white",
                    "category": "general",
                    "source": "automation_test",
                    "created_at": datetime.now().isoformat(),
                    "url": "https://test.com/test-story",
                    "domain": "test.com",
                    "author": "Automation Test",
                    "published_date": datetime.now().isoformat(),
                    "word_count": 50,
                    "reading_time": 1,
                    "difficulty_score": 1.0,
                    "engagement_score": 1.0,
                    "concepts": ["testing", "automation"],
                    "tags": ["test", "automation", "validation"]
                }
            ]
        }
        
        test_file = Path("temp_processing") / "test_import.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        print("✅ Test JSON file created")
        
        # Test importer initialization (dry run)
        importer = EnhancedContentImporter(str(test_file), dry_run=True)
        
        if importer.load_json():
            print("✅ JSON loading test passed")
        else:
            print("❌ JSON loading test failed")
            return False
        
        # Clean up test file
        test_file.unlink()
        print("✅ Import system test completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Import system test failed: {str(e)}")
        return False

def test_automation_class():
    """Test the main automation class initialization"""
    print("\n🤖 Testing Automation Class...")
    
    try:
        from automation.COMPLETE_DAILY_AUTOMATION import CompleteDailyAutomation
        
        # Test initialization
        automation = CompleteDailyAutomation()
        print("✅ Automation class initialized successfully")
        
        # Test configuration
        if automation.config.get('gemini_api_key'):
            print("✅ Configuration loaded successfully")
        else:
            print("❌ Configuration loading failed")
            return False
        
        # Test RSS feeds
        if len(automation.rss_feeds) > 0:
            print(f"✅ RSS feeds loaded: {len(automation.rss_feeds)} feeds")
        else:
            print("❌ No RSS feeds loaded")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Automation class test failed: {str(e)}")
        return False

def test_batch_file():
    """Test the Windows batch file"""
    print("\n📝 Testing Batch File...")
    
    batch_file = Path("automation/run_daily_automation.bat")
    if not batch_file.exists():
        print("❌ run_daily_automation.bat not found")
        return False
    
    # Read and validate batch file content
    content = batch_file.read_text()
    
    if "GEMINI_API_KEY" in content:
        print("✅ API key environment variable set in batch file")
    else:
        print("❌ API key not found in batch file")
        return False
    
    if "COMPLETE_DAILY_AUTOMATION.py" in content:
        print("✅ Correct automation script referenced")
    else:
        print("❌ Wrong automation script in batch file")
        return False
    
    if "cd /d" in content:
        print("✅ Working directory change command found")
    else:
        print("❌ Working directory not set in batch file")
        return False
    
    print("✅ Batch file validation passed")
    return True

def main():
    """Run all tests"""
    print("🧪 COMPLETE AUTOMATION SYSTEM TEST")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    print()
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Database Connections", test_database_connections),
        ("Import System", test_import_system),
        ("Automation Class", test_automation_class),
        ("Batch File", test_batch_file)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"💥 {test_name}: ERROR - {str(e)}")
        print()
    
    print("=" * 50)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Automation system is ready for 9am tomorrow!")
        return True
    else:
        print("❌ SOME TESTS FAILED! Please fix issues before enabling automation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)