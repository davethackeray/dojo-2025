#!/usr/bin/env python3
"""
USER PROFILE SYSTEM INITIALIZATION
InvestingDojo 2025 - Database Setup and Testing

This script initializes the user profile and progress tracking system by:
1. Creating all necessary database tables
2. Setting up initial data structures
3. Testing basic functionality
4. Providing example usage

USAGE:
python initialize_user_system.py

This creates NEW tables without affecting existing database operations.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from user_profile_system import UserProfileSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_database_config():
    """Get database configuration from environment or defaults"""
    return {
        'host': os.getenv('DB_LOCAL_HOST', 'localhost'),
        'database': os.getenv('DB_LOCAL_DATABASE', 'u219832816_investing_dojo'),
        'user': os.getenv('DB_LOCAL_USER', 'u219832816_davethackeray'),
        'password': os.getenv('DB_LOCAL_PASSWORD', 'ToTheM00n!'),
        'charset': 'utf8mb4',
        'use_unicode': True,
        'autocommit': False
    }

def initialize_user_system():
    """Initialize the complete user profile system"""
    logger.info("🚀 Initializing InvestingDojo User Profile System...")

    # Initialize the system
    db_config = get_database_config()
    user_system = UserProfileSystem(db_config)

    try:
        # Connect to database
        if not user_system.connect():
            logger.error("❌ Failed to connect to database")
            return False

        # Create all tables
        logger.info("📋 Creating database tables...")
        if not user_system.create_tables():
            logger.error("❌ Failed to create database tables")
            return False

        logger.info("✅ Database tables created successfully!")

        # Create sample user for testing
        logger.info("👤 Creating sample user profile...")
        sample_user_data = {
            'email': 'demo@investingdojo.co',
            'username': 'demo_investor',
            'first_name': 'Demo',
            'last_name': 'Investor',
            'investment_experience': 'intermediate',
            'risk_tolerance': 'moderate',
            'learning_style': 'reading',
            'age_group': '35-44',
            'investment_goals': 'Build long-term wealth for family',
            'time_horizon': 'long_term',
            'capital_available': 50000.00
        }

        user_id = user_system.create_user_profile(sample_user_data)
        if user_id:
            logger.info(f"✅ Sample user created with ID: {user_id}")

            # Test learning activity recording
            logger.info("📚 Testing learning activity recording...")
            test_content_id = "sample_content_001"

            # Record different types of activities
            activities = [
                ('view', 300),  # 5 minutes reading
                ('complete', 900),  # 15 minutes completion
                ('bookmark', 0),  # Quick bookmark
                ('rate', 0)  # Rating given
            ]

            for activity_type, time_spent in activities:
                success = user_system.record_learning_activity(
                    user_id=user_id,
                    content_id=test_content_id,
                    activity_type=activity_type,
                    time_spent=time_spent,
                    completion_rate=1.0 if activity_type == 'complete' else 0.0
                )
                if success:
                    logger.info(f"✅ Recorded {activity_type} activity")
                else:
                    logger.warning(f"⚠️ Failed to record {activity_type} activity")

            # Get and display user profile
            logger.info("📊 Retrieving user profile...")
            profile_data = user_system.get_user_profile(user_id)
            if profile_data:
                profile = profile_data['profile']
                progress = profile_data['progress']
                stats = profile_data['stats']

                logger.info("=== USER PROFILE SUMMARY ===")
                logger.info(f"Name: {profile['first_name']} {profile['last_name']}")
                logger.info(f"Email: {profile['email']}")
                logger.info(f"Current Belt: {profile['current_belt']}")
                logger.info(f"Total XP: {profile['total_xp']}")
                logger.info(f"Belt Progress: {progress['progress_percentage']:.1f}%" if progress else "N/A")
                logger.info(f"Learning Activities (30 days): {stats.get('total_activities', 0)}")
                logger.info(f"Time Spent Learning: {stats.get('total_time_spent', 0) // 60} minutes")
                logger.info("============================")

            # Test leaderboard
            logger.info("🏆 Testing leaderboard functionality...")
            leaderboard = user_system.get_leaderboard(limit=10)
            if leaderboard:
                logger.info("=== TOP 10 LEADERBOARD ===")
                for i, entry in enumerate(leaderboard[:5], 1):  # Show top 5
                    logger.info(f"{i}. {entry['username'] or 'Anonymous'} - {entry['total_xp']} XP ({entry['current_belt']})")
                logger.info("==========================")

        else:
            logger.error("❌ Failed to create sample user")

        # Disconnect from database
        user_system.disconnect()

        logger.info("🎉 User Profile System initialization completed successfully!")
        logger.info("")
        logger.info("NEXT STEPS:")
        logger.info("1. Integrate user system into your main application")
        logger.info("2. Add user authentication and session management")
        logger.info("3. Create API endpoints for user profile operations")
        logger.info("4. Build frontend components for user dashboard")
        logger.info("5. Implement content recommendation engine")
        logger.info("")
        logger.info("The system is ready for Phase 1 development! 🚀")

        return True

    except Exception as e:
        logger.error(f"❌ Initialization failed: {str(e)}")
        user_system.disconnect()
        return False

def create_sample_content_recommendations():
    """Create sample content recommendations for testing"""
    logger.info("📝 Creating sample content recommendations...")

    # This would typically integrate with your existing content system
    # For now, we'll create a placeholder structure

    sample_recommendations = [
        {
            'content_id': 'white_belt_foundation_001',
            'title': 'Understanding Compound Interest',
            'belt_level': 'white-belt',
            'content_type': 'curriculum-war-story',
            'difficulty_level': 'foundational',
            'estimated_time': 15,
            'relevance_score': 95,
            'reason': 'Perfect foundation content for new investors'
        },
        {
            'content_id': 'yellow_belt_basics_002',
            'title': 'Building Your First Emergency Fund',
            'belt_level': 'yellow-belt',
            'content_type': 'family-wealth-builder',
            'difficulty_level': 'foundational',
            'estimated_time': 20,
            'relevance_score': 88,
            'reason': 'Essential for financial security'
        },
        {
            'content_id': 'ai_integration_guide_003',
            'title': 'Using ChatGPT for Investment Research',
            'belt_level': 'orange-belt',
            'content_type': 'ai-integration-guide',
            'difficulty_level': 'intermediate-skill',
            'estimated_time': 25,
            'relevance_score': 92,
            'reason': 'Modern research techniques for serious investors'
        }
    ]

    # Save sample recommendations to file for reference
    recommendations_file = Path("sample_recommendations.json")
    with open(recommendations_file, 'w', encoding='utf-8') as f:
        json.dump(sample_recommendations, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ Sample recommendations saved to {recommendations_file}")
    return sample_recommendations

def main():
    """Main initialization function"""
    print("🎯 InvestingDojo User Profile System Initialization")
    print("=" * 60)

    # Check if we should create sample data
    create_samples = input("Create sample user and test data? (y/n): ").lower().strip() == 'y'

    # Initialize the system
    success = initialize_user_system()

    if success and create_samples:
        create_sample_content_recommendations()

    if success:
        print("\n🎉 SUCCESS: User Profile System is ready!")
        print("\nTo integrate into your application:")
        print("1. Import: from user_profile_system import UserProfileSystem")
        print("2. Initialize: user_system = UserProfileSystem(db_config)")
        print("3. Connect: user_system.connect()")
        print("4. Use: user_system.create_user_profile(user_data)")
    else:
        print("\n❌ FAILED: Check logs for error details")
        sys.exit(1)

if __name__ == "__main__":
    main()