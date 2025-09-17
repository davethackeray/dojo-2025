#!/usr/bin/env python3
"""
USER PROFILE AND PROGRESS TRACKING SYSTEM
InvestingDojo 2025 - Personalization Foundation

This module provides the complete user profile and progress tracking system for the
transformation from automation to personalized investment intelligence platform.

KEY FEATURES:
- User profiles with investment experience and goals
- Belt progression tracking with XP system
- Learning history and content consumption analytics
- Achievement and milestone system
- Personalized learning path recommendations

DATABASE DESIGN:
- Creates NEW tables without modifying existing ones
- Integrates with existing content system
- Maintains data integrity and performance
- Supports future scaling and feature expansion

ARCHITECTURE:
- UserProfileManager: Main orchestration class
- UserProfile: User data management
- ProgressTracker: Belt progression and XP
- LearningHistory: Content consumption tracking
- AchievementSystem: Milestones and rewards
"""

import mysql.connector
from mysql.connector import Error
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import uuid

logger = logging.getLogger(__name__)

class UserProfileSystem:
    """Complete user profile and progress tracking system"""

    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
        self.cursor = None

        # Belt system configuration
        self.belt_levels = {
            'white-belt': {'name': 'White Belt', 'min_xp': 0, 'max_xp': 100, 'description': 'Foundation & Mindset'},
            'yellow-belt': {'name': 'Yellow Belt', 'min_xp': 100, 'max_xp': 300, 'description': 'Core Knowledge'},
            'orange-belt': {'name': 'Orange Belt', 'min_xp': 300, 'max_xp': 600, 'description': 'Research Mastery'},
            'green-belt': {'name': 'Green Belt', 'min_xp': 600, 'max_xp': 1000, 'description': 'Edge Development'},
            'blue-belt': {'name': 'Blue Belt', 'min_xp': 1000, 'max_xp': 1500, 'description': 'Execution Mastery'},
            'brown-belt': {'name': 'Brown Belt', 'min_xp': 1500, 'max_xp': 2200, 'description': 'Systematic Mastery'},
            'black-belt': {'name': 'Black Belt', 'min_xp': 2200, 'max_xp': 999999, 'description': 'Adaptive Mastery'}
        }

        # XP rewards for different activities
        self.xp_rewards = {
            'content_view': 5,
            'content_complete': 15,
            'quiz_pass': 25,
            'discussion_participate': 10,
            'milestone_achieve': 50,
            'streak_maintain': 20,
            'peer_help': 30,
            'advanced_content': 35
        }

        logger.info("User Profile System initialized")

    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=self.db_config['host'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                charset=self.db_config.get('charset', 'utf8mb4'),
                autocommit=False
            )

            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                logger.info("✅ Connected to database for user profile system")
                return True
            else:
                logger.error("❌ Failed to connect to database")
                return False

        except Error as e:
            logger.error(f"❌ Database connection error: {str(e)}")
            return False

    def disconnect(self):
        """Close database connection"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection and self.connection.is_connected():
                self.connection.close()
                logger.info("User profile system database connection closed")
        except Error as e:
            logger.error(f"Error closing database connection: {str(e)}")

    def create_tables(self) -> bool:
        """Create all necessary tables for the user profile system"""
        try:
            # User Profiles Table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id VARCHAR(36) PRIMARY KEY,
                    email VARCHAR(255) UNIQUE,
                    username VARCHAR(100) UNIQUE,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    avatar_url VARCHAR(500),
                    bio TEXT,
                    location VARCHAR(100),
                    timezone VARCHAR(50) DEFAULT 'UTC',

                    -- Investment Profile
                    investment_experience ENUM('beginner', 'intermediate', 'advanced', 'expert') DEFAULT 'beginner',
                    risk_tolerance ENUM('conservative', 'moderate', 'aggressive') DEFAULT 'moderate',
                    investment_goals TEXT,
                    time_horizon ENUM('short_term', 'medium_term', 'long_term') DEFAULT 'long_term',
                    capital_available DECIMAL(15,2),

                    -- Learning Preferences
                    learning_style ENUM('visual', 'auditory', 'reading', 'kinesthetic') DEFAULT 'reading',
                    preferred_content_types TEXT, -- JSON array
                    daily_learning_goal INT DEFAULT 30, -- minutes
                    weekly_learning_goal INT DEFAULT 210, -- minutes

                    -- Family & Demographics
                    family_status ENUM('single', 'married', 'family') DEFAULT 'single',
                    children_count INT DEFAULT 0,
                    age_group ENUM('18-24', '25-34', '35-44', '45-54', '55-64', '65+'),
                    occupation VARCHAR(100),

                    -- System Fields
                    current_belt VARCHAR(20) DEFAULT 'white-belt',
                    total_xp INT DEFAULT 0,
                    level INT DEFAULT 1,
                    streak_days INT DEFAULT 0,
                    last_activity_date DATE,
                    account_status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                    INDEX idx_email (email),
                    INDEX idx_current_belt (current_belt),
                    INDEX idx_total_xp (total_xp),
                    INDEX idx_account_status (account_status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # User Progress Table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_progress (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    belt_level VARCHAR(20) NOT NULL,
                    xp_earned INT DEFAULT 0,
                    xp_required INT NOT NULL,
                    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
                    skills_mastered TEXT, -- JSON array of skill IDs
                    completed_milestones TEXT, -- JSON array of milestone IDs
                    current_challenges TEXT, -- JSON array of active challenges
                    belt_achieved_date TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                    FOREIGN KEY (user_id) REFERENCES user_profiles(id) ON DELETE CASCADE,
                    INDEX idx_user_belt (user_id, belt_level),
                    INDEX idx_progress_pct (progress_percentage)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # Learning History Table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_history (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    content_id VARCHAR(255) NOT NULL, -- References existing stories.id
                    content_type VARCHAR(50),
                    activity_type ENUM('view', 'complete', 'bookmark', 'share', 'rate') NOT NULL,
                    time_spent_seconds INT DEFAULT 0,
                    completion_rate DECIMAL(5,2) DEFAULT 0.00,
                    user_rating INT, -- 1-5 stars
                    notes TEXT,
                    xp_earned INT DEFAULT 0,
                    belt_relevance VARCHAR(20),
                    learning_objectives_achieved TEXT, -- JSON array
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (user_id) REFERENCES user_profiles(id) ON DELETE CASCADE,
                    INDEX idx_user_content (user_id, content_id),
                    INDEX idx_activity_type (activity_type),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # Achievement System Table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_achievements (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    achievement_type VARCHAR(50) NOT NULL,
                    achievement_name VARCHAR(100) NOT NULL,
                    achievement_description TEXT,
                    achievement_icon VARCHAR(100),
                    xp_reward INT DEFAULT 0,
                    rarity ENUM('common', 'uncommon', 'rare', 'epic', 'legendary') DEFAULT 'common',
                    category VARCHAR(50),
                    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,

                    FOREIGN KEY (user_id) REFERENCES user_profiles(id) ON DELETE CASCADE,
                    INDEX idx_user_type (user_id, achievement_type),
                    INDEX idx_rarity (rarity)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # User Preferences Table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    notification_email BOOLEAN DEFAULT TRUE,
                    notification_push BOOLEAN DEFAULT TRUE,
                    notification_sms BOOLEAN DEFAULT FALSE,
                    email_frequency ENUM('daily', 'weekly', 'monthly', 'never') DEFAULT 'weekly',
                    content_recommendations BOOLEAN DEFAULT TRUE,
                    market_alerts BOOLEAN DEFAULT TRUE,
                    community_updates BOOLEAN DEFAULT TRUE,
                    learning_reminders BOOLEAN DEFAULT TRUE,
                    privacy_profile_visible BOOLEAN DEFAULT TRUE,
                    privacy_progress_visible BOOLEAN DEFAULT TRUE,
                    privacy_achievements_visible BOOLEAN DEFAULT TRUE,
                    theme_preference ENUM('light', 'dark', 'auto') DEFAULT 'auto',
                    language_preference VARCHAR(10) DEFAULT 'en',
                    timezone VARCHAR(50) DEFAULT 'UTC',

                    FOREIGN KEY (user_id) REFERENCES user_profiles(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_user_prefs (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # Learning Streaks Table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_streaks (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    streak_type ENUM('daily', 'weekly', 'monthly') NOT NULL,
                    current_streak INT DEFAULT 0,
                    longest_streak INT DEFAULT 0,
                    last_activity_date DATE,
                    streak_start_date DATE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                    FOREIGN KEY (user_id) REFERENCES user_profiles(id) ON DELETE CASCADE,
                    INDEX idx_user_streak (user_id, streak_type),
                    INDEX idx_active_streaks (is_active, streak_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            self.connection.commit()
            logger.info("✅ All user profile system tables created successfully")
            return True

        except Error as e:
            logger.error(f"❌ Failed to create tables: {str(e)}")
            self.connection.rollback()
            return False

    def create_user_profile(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Create a new user profile"""
        try:
            user_id = str(uuid.uuid4())

            # Prepare user data with defaults
            profile_data = {
                'id': user_id,
                'email': user_data.get('email'),
                'username': user_data.get('username'),
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', ''),
                'investment_experience': user_data.get('investment_experience', 'beginner'),
                'risk_tolerance': user_data.get('risk_tolerance', 'moderate'),
                'learning_style': user_data.get('learning_style', 'reading'),
                'age_group': user_data.get('age_group'),
                'current_belt': 'white-belt',
                'total_xp': 0,
                'level': 1,
                'streak_days': 0,
                'account_status': 'active'
            }

            # Insert user profile
            fields = list(profile_data.keys())
            placeholders = ', '.join(['%s'] * len(fields))
            query = f"INSERT INTO user_profiles ({', '.join(fields)}) VALUES ({placeholders})"

            self.cursor.execute(query, list(profile_data.values()))

            # Create initial progress record
            self._create_initial_progress(user_id)

            # Create default preferences
            self._create_default_preferences(user_id)

            # Create initial streaks
            self._create_initial_streaks(user_id)

            self.connection.commit()
            logger.info(f"✅ Created user profile for: {user_data.get('email')}")
            return user_id

        except Error as e:
            logger.error(f"❌ Failed to create user profile: {str(e)}")
            self.connection.rollback()
            return None

    def _create_initial_progress(self, user_id: str):
        """Create initial progress record for new user"""
        for belt_level, belt_info in self.belt_levels.items():
            progress_data = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'belt_level': belt_level,
                'xp_earned': 0 if belt_level == 'white-belt' else 0,
                'xp_required': belt_info['max_xp'] - belt_info['min_xp'],
                'progress_percentage': 0.00,
                'skills_mastered': '[]',
                'completed_milestones': '[]',
                'current_challenges': '[]'
            }

            fields = list(progress_data.keys())
            placeholders = ', '.join(['%s'] * len(fields))
            query = f"INSERT INTO user_progress ({', '.join(fields)}) VALUES ({placeholders})"
            self.cursor.execute(query, list(progress_data.values()))

    def _create_default_preferences(self, user_id: str):
        """Create default user preferences"""
        prefs_data = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'notification_email': True,
            'notification_push': True,
            'email_frequency': 'weekly',
            'content_recommendations': True,
            'market_alerts': True,
            'learning_reminders': True,
            'privacy_profile_visible': True
        }

        fields = list(prefs_data.keys())
        placeholders = ', '.join(['%s'] * len(fields))
        query = f"INSERT INTO user_preferences ({', '.join(fields)}) VALUES ({placeholders})"
        self.cursor.execute(query, list(prefs_data.values()))

    def _create_initial_streaks(self, user_id: str):
        """Create initial streak records for new user"""
        streak_types = ['daily', 'weekly', 'monthly']

        for streak_type in streak_types:
            streak_data = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'streak_type': streak_type,
                'current_streak': 0,
                'longest_streak': 0,
                'is_active': True
            }

            fields = list(streak_data.keys())
            placeholders = ', '.join(['%s'] * len(fields))
            query = f"INSERT INTO learning_streaks ({', '.join(fields)}) VALUES ({placeholders})"
            self.cursor.execute(query, list(streak_data.values()))

    def record_learning_activity(self, user_id: str, content_id: str,
                               activity_type: str, time_spent: int = 0,
                               completion_rate: float = 0.0) -> bool:
        """Record a learning activity for XP and progress tracking"""
        try:
            # Calculate XP earned
            xp_earned = self.xp_rewards.get(activity_type, 5)

            # Record learning history
            history_data = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'content_id': content_id,
                'activity_type': activity_type,
                'time_spent_seconds': time_spent,
                'completion_rate': completion_rate,
                'xp_earned': xp_earned
            }

            fields = list(history_data.keys())
            placeholders = ', '.join(['%s'] * len(fields))
            query = f"INSERT INTO learning_history ({', '.join(fields)}) VALUES ({placeholders})"
            self.cursor.execute(query, list(history_data.values()))

            # Update user XP and progress
            self._update_user_xp(user_id, xp_earned)

            # Update learning streaks
            self._update_learning_streaks(user_id)

            self.connection.commit()
            logger.info(f"✅ Recorded learning activity: {activity_type} for user {user_id}")
            return True

        except Error as e:
            logger.error(f"❌ Failed to record learning activity: {str(e)}")
            self.connection.rollback()
            return False

    def _update_user_xp(self, user_id: str, xp_gained: int):
        """Update user's total XP and belt progression"""
        try:
            # Update total XP
            query = "UPDATE user_profiles SET total_xp = total_xp + %s, updated_at = NOW() WHERE id = %s"
            self.cursor.execute(query, (xp_gained, user_id))

            # Get current user data
            query = "SELECT total_xp, current_belt FROM user_profiles WHERE id = %s"
            self.cursor.execute(query, (user_id,))
            user_data = self.cursor.fetchone()

            if user_data:
                total_xp = user_data['total_xp']
                current_belt = user_data['current_belt']

                # Check if user should advance to next belt
                next_belt = self._calculate_next_belt(current_belt, total_xp)
                if next_belt != current_belt:
                    self._advance_belt(user_id, next_belt, total_xp)

                # Update progress percentage for current belt
                self._update_belt_progress(user_id, current_belt, total_xp)

        except Error as e:
            logger.error(f"❌ Failed to update user XP: {str(e)}")

    def _calculate_next_belt(self, current_belt: str, total_xp: int) -> str:
        """Calculate if user should advance to next belt"""
        for belt_level, belt_info in self.belt_levels.items():
            if total_xp >= belt_info['min_xp'] and belt_level != current_belt:
                # Check if this is the appropriate next belt
                current_min_xp = self.belt_levels[current_belt]['min_xp']
                if belt_info['min_xp'] > current_min_xp:
                    return belt_level

        return current_belt

    def _advance_belt(self, user_id: str, new_belt: str, total_xp: int):
        """Advance user to new belt level"""
        try:
            # Update user profile
            query = "UPDATE user_profiles SET current_belt = %s, updated_at = NOW() WHERE id = %s"
            self.cursor.execute(query, (new_belt, user_id))

            # Update progress record
            query = """
                UPDATE user_progress
                SET belt_achieved_date = NOW(), updated_at = NOW()
                WHERE user_id = %s AND belt_level = %s
            """
            self.cursor.execute(query, (user_id, new_belt))

            # Create achievement record
            achievement_data = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'achievement_type': 'belt_advancement',
                'achievement_name': f"{self.belt_levels[new_belt]['name']} Achieved",
                'achievement_description': f"Congratulations! You've advanced to {self.belt_levels[new_belt]['name']} level.",
                'xp_reward': 100,
                'rarity': 'rare',
                'category': 'progression'
            }

            fields = list(achievement_data.keys())
            placeholders = ', '.join(['%s'] * len(fields))
            query = f"INSERT INTO user_achievements ({', '.join(fields)}) VALUES ({placeholders})"
            self.cursor.execute(query, list(achievement_data.values()))

            logger.info(f"🎉 User {user_id} advanced to {new_belt} belt!")

        except Error as e:
            logger.error(f"❌ Failed to advance belt: {str(e)}")

    def _update_belt_progress(self, user_id: str, current_belt: str, total_xp: int):
        """Update progress percentage for current belt"""
        try:
            belt_info = self.belt_levels[current_belt]
            belt_xp_range = belt_info['max_xp'] - belt_info['min_xp']
            belt_xp_earned = total_xp - belt_info['min_xp']

            if belt_xp_range > 0:
                progress_percentage = min(100.00, (belt_xp_earned / belt_xp_range) * 100)
            else:
                progress_percentage = 100.00

            query = """
                UPDATE user_progress
                SET progress_percentage = %s, xp_earned = %s, updated_at = NOW()
                WHERE user_id = %s AND belt_level = %s
            """
            self.cursor.execute(query, (progress_percentage, belt_xp_earned, user_id, current_belt))

        except Error as e:
            logger.error(f"❌ Failed to update belt progress: {str(e)}")

    def _update_learning_streaks(self, user_id: str):
        """Update learning streaks for user"""
        try:
            today = datetime.now().date()

            # Update daily streak
            query = """
                SELECT last_activity_date, current_streak, longest_streak
                FROM learning_streaks
                WHERE user_id = %s AND streak_type = 'daily'
            """
            self.cursor.execute(query, (user_id,))
            streak_data = self.cursor.fetchone()

            if streak_data:
                last_activity = streak_data['last_activity_date']
                current_streak = streak_data['current_streak']
                longest_streak = streak_data['longest_streak']

                if last_activity == today - timedelta(days=1):
                    # Continue streak
                    current_streak += 1
                elif last_activity != today:
                    # Reset streak
                    current_streak = 1

                longest_streak = max(longest_streak, current_streak)

                query = """
                    UPDATE learning_streaks
                    SET current_streak = %s, longest_streak = %s,
                        last_activity_date = %s, updated_at = NOW()
                    WHERE user_id = %s AND streak_type = 'daily'
                """
                self.cursor.execute(query, (current_streak, longest_streak, today, user_id))

        except Error as e:
            logger.error(f"❌ Failed to update learning streaks: {str(e)}")

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get complete user profile with progress information"""
        try:
            # Get user profile
            query = "SELECT * FROM user_profiles WHERE id = %s"
            self.cursor.execute(query, (user_id,))
            profile = self.cursor.fetchone()

            if not profile:
                return None

            # Get current progress
            query = """
                SELECT * FROM user_progress
                WHERE user_id = %s AND belt_level = %s
            """
            self.cursor.execute(query, (user_id, profile['current_belt']))
            progress = self.cursor.fetchone()

            # Get recent achievements
            query = """
                SELECT * FROM user_achievements
                WHERE user_id = %s AND is_active = TRUE
                ORDER BY unlocked_at DESC LIMIT 5
            """
            self.cursor.execute(query, (user_id,))
            achievements = self.cursor.fetchall()

            # Get learning statistics
            query = """
                SELECT
                    COUNT(*) as total_activities,
                    SUM(time_spent_seconds) as total_time_spent,
                    SUM(xp_earned) as total_xp_earned,
                    AVG(completion_rate) as avg_completion_rate
                FROM learning_history
                WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """
            self.cursor.execute(query, (user_id,))
            stats = self.cursor.fetchone()

            return {
                'profile': profile,
                'progress': progress,
                'achievements': achievements,
                'stats': stats or {}
            }

        except Error as e:
            logger.error(f"❌ Failed to get user profile: {str(e)}")
            return None

    def get_personalized_recommendations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get personalized content recommendations based on user profile and progress"""
        try:
            # Get user profile and preferences
            profile = self.get_user_profile(user_id)
            if not profile:
                return []

            user_belt = profile['profile']['current_belt']
            learning_style = profile['profile']['learning_style']
            risk_tolerance = profile['profile']['risk_tolerance']

            # This would integrate with the existing content system
            # For now, return a placeholder structure
            recommendations = []

            # TODO: Implement actual recommendation logic based on:
            # - User's current belt level
            # - Learning history and preferences
            # - Content difficulty and belt alignment
            # - User's risk tolerance and goals
            # - Learning style preferences

            return recommendations

        except Error as e:
            logger.error(f"❌ Failed to get recommendations: {str(e)}")
            return []

    def get_leaderboard(self, belt_level: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get leaderboard for belt progression or overall XP"""
        try:
            if belt_level:
                query = """
                    SELECT
                        up.username,
                        up.first_name,
                        up.last_name,
                        up.total_xp,
                        up.current_belt,
                        up.avatar_url,
                        up.location,
                        ROW_NUMBER() OVER (ORDER BY up.total_xp DESC) as rank
                    FROM user_profiles up
                    WHERE up.current_belt = %s AND up.account_status = 'active'
                    ORDER BY up.total_xp DESC
                    LIMIT %s
                """
                self.cursor.execute(query, (belt_level, limit))
            else:
                query = """
                    SELECT
                        up.username,
                        up.first_name,
                        up.last_name,
                        up.total_xp,
                        up.current_belt,
                        up.avatar_url,
                        up.location,
                        ROW_NUMBER() OVER (ORDER BY up.total_xp DESC) as rank
                    FROM user_profiles up
                    WHERE up.account_status = 'active'
                    ORDER BY up.total_xp DESC
                    LIMIT %s
                """
                self.cursor.execute(query, (limit,))

            return self.cursor.fetchall()

        except Error as e:
            logger.error(f"❌ Failed to get leaderboard: {str(e)}")
            return []

# Example usage and testing functions
def test_user_profile_system():
    """Test the user profile system functionality"""
    # This would be used for testing the system
    pass

if __name__ == "__main__":
    # Example usage
    print("User Profile System - Ready for integration!")
    print("Run this module through your main application to initialize the user system.")