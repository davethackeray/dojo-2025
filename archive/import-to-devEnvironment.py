#!/usr/bin/env python3
"""
InvestingDojo Enhanced Content Importer - Complete Version
Beautifully integrates complex JSON structures into MariaDB with full data preservation
"""

import json
import mysql.connector
from mysql.connector import Error
import sys
import os
from datetime import datetime
import argparse
import logging
import re
from typing import Dict, List, Any, Tuple, Union, Optional, Set
import uuid
from decimal import Decimal
import hashlib

# Configure logging with more detail - Fix Unicode issue
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EnhancedContentImporter:
    """Enhanced importer with better JSON handling and data integrity"""
    
    def __init__(self, json_file_path: str, dry_run: bool = False):
        self.json_file_path = json_file_path
        self.dry_run = dry_run
        self.connection = None
        self.cursor = None
        self.content_data = None
        self.lookup_data = None
        self.imported_count = 0
        self.errors = []
        self.warnings = []
        
        # Track all entities for relationship validation
        self.existing_entities = {
            'belt_levels': set(),
            'content_types': set(),
            'tags': set(),
            'ai_tools': set(),
            'concepts': set(),
            'seasonal_challenges': set()
        }
        
        # Time mapping for the ENUM field - FIXED MAPPING
        self.time_required_mapping = {
            '': None,
            None: None,
            '5 minutes': '5 minutes',
            '10 minutes': '5 minutes',
            '15 minutes': '5 minutes',
            '30 minutes': 'weekend practice',
            '1 hour': 'weekend practice',
            '2 hours': 'weekend practice',
            'weekend practice': 'weekend practice',
            'ongoing': 'ongoing',
            '2 hours per quarter': 'ongoing',
            '1 hour per quarter': 'ongoing',
            '2 hours per quarter for review': 'ongoing',
            '15 minutes (eight times a year)': '5 minutes',
            '1 hour per quarter': 'ongoing',
            '2 hours per quarter': 'ongoing',
            '2 hours per year': 'ongoing'
        }
        
        # Enhanced database config - FIXED autocommit
        self.db_config = {
            'host': 'localhost',
            'database': 'u219832816_investing_dojo',
            'user': 'u219832816_davethackeray',
            'password': 'ToTheM00n!',
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'use_unicode': True,
            'autocommit': True,  # Changed to True to avoid transaction issues
            'raise_on_warnings': False,
            'sql_mode': 'TRADITIONAL'
        }
        
    def load_json(self) -> bool:
        """Load and validate JSON with enhanced structure handling"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract stories from various possible structures
            stories = []
            if 'investing-dojo-stories' in data:
                stories = data['investing-dojo-stories']
                # Also extract lookup data if present
                self.lookup_data = data.get('lookup_data_definitions', {})
            else:
                # Handle other structures
                for key in ['newsletter_content', 'stories']:
                    if key in data:
                        stories = data[key]
                        break
                if not stories and isinstance(data, list):
                    stories = data
            
            if not stories:
                logger.error("No stories found in JSON")
                return False
            
            self.content_data = {'stories': stories}
            
            # Validate story structure
            for i, story in enumerate(stories):
                if not self._validate_story_structure(story, i):
                    return False
            
            logger.info(f"Successfully loaded {len(stories)} stories")
            return True
            
        except Exception as e:
            logger.error(f"Error loading JSON: {e}")
            return False
    
    def _validate_story_structure(self, story: Dict, index: int) -> bool:
        """Validate essential story fields"""
        required_fields = ['id', 'title', 'summary', 'full_content', 'content_type']
        missing = [f for f in required_fields if not story.get(f)]
        
        if missing:
            logger.error(f"Story {index} missing required fields: {missing}")
            return False
        
        # Validate nested structures
        if 'scoring' in story and not isinstance(story['scoring'], dict):
            logger.warning(f"Story {story['id']} has invalid scoring structure")
        
        return True
    
    def connect_to_database(self) -> bool:
        """Enhanced database connection with better error handling"""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            self.cursor = self.connection.cursor(dictionary=True, buffered=True)
            
            # Set session parameters
            self.cursor.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            self.cursor.execute("SET CHARACTER SET utf8mb4")
            self.cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
            
            # Load existing entities for validation
            self._load_existing_entities()
            
            logger.info("Successfully connected to MariaDB with enhanced settings")
            return True
            
        except Error as e:
            logger.error(f"Database connection error: {e}")
            return False
    
    def _load_existing_entities(self):
        """Pre-load existing entities for relationship validation"""
        try:
            # Load belt levels
            self.cursor.execute("SELECT name FROM belt_levels")
            self.existing_entities['belt_levels'] = {row['name'] for row in self.cursor.fetchall()}
            
            # Load content types
            self.cursor.execute("SELECT name FROM content_types")
            self.existing_entities['content_types'] = {row['name'] for row in self.cursor.fetchall()}
            
            # Load tags
            self.cursor.execute("SELECT name FROM tags")
            self.existing_entities['tags'] = {row['name'] for row in self.cursor.fetchall()}
            
            # Load seasonal challenges
            self.cursor.execute("SELECT challenge_type FROM seasonal_challenges")
            self.existing_entities['seasonal_challenges'] = {row['challenge_type'] for row in self.cursor.fetchall()}
            
            logger.info(f"Loaded existing entities: {sum(len(v) for v in self.existing_entities.values())} total")
            
        except Error as e:
            logger.warning(f"Could not pre-load entities: {e}")
    
    def _map_time_required(self, time_value: Any) -> Optional[str]:
        """Map various time values to the allowed ENUM values"""
        if time_value is None or time_value == '':
            return None
        
        # Convert to string and clean
        time_str = str(time_value).strip()
        
        # Check direct mapping first
        if time_str in self.time_required_mapping:
            return self.time_required_mapping[time_str]
        
        # Try lowercase match
        time_lower = time_str.lower()
        for key, mapped_value in self.time_required_mapping.items():
            if key and key.lower() == time_lower:
                return mapped_value
        
        # Pattern matching
        if 'minute' in time_lower:
            minutes = re.search(r'(\d+)', time_lower)
            if minutes:
                mins = int(minutes.group(1))
                if mins <= 15:
                    return '5 minutes'
                else:
                    return 'weekend practice'
        
        if 'hour' in time_lower:
            return 'weekend practice'
        
        if 'ongoing' in time_lower or 'quarter' in time_lower or 'year' in time_lower:
            return 'ongoing'
        
        # Default to weekend practice if we can't determine
        logger.warning(f"Could not map time_required value '{time_str}', defaulting to 'weekend practice'")
        return 'weekend practice'
    
    def _ensure_lookup_entity(self, entity_type: str, entity_name: str, entity_data: Dict = None) -> int:
        """Ensure a lookup entity exists and return its ID"""
        table_map = {
            'belt_levels': 'belt_levels',
            'content_types': 'content_types',
            'tags': 'tags',
            'ai_tools': 'ai_tools',
            'concepts': 'concepts',
            'seasonal_challenges': 'seasonal_challenges'
        }
        
        if entity_type not in table_map:
            return None
        
        table = table_map[entity_type]
        
        try:
            # Check if exists
            if entity_type == 'seasonal_challenges':
                self.cursor.execute(f"SELECT id FROM {table} WHERE challenge_type = %s", (entity_name,))
            else:
                self.cursor.execute(f"SELECT id FROM {table} WHERE name = %s", (entity_name,))
            
            result = self.cursor.fetchone()
            if result:
                return result['id']
            
            # Create if not exists
            if entity_type == 'belt_levels':
                # Use lookup data if available
                if self.lookup_data and 'belt_levels' in self.lookup_data:
                    belt_data = next((b for b in self.lookup_data['belt_levels'] if b['name'] == entity_name), None)
                    if belt_data:
                        self.cursor.execute(
                            "INSERT INTO belt_levels (name, display_name, description, level_order, xp_required) VALUES (%s, %s, %s, %s, %s)",
                            (entity_name, entity_name.replace('-', ' ').title(), belt_data.get('description', ''), 
                             belt_data.get('order', 99), 0)
                        )
                    else:
                        self._create_default_belt_level(entity_name)
                else:
                    self._create_default_belt_level(entity_name)
                    
            elif entity_type == 'content_types':
                display_name = entity_name.replace('-', ' ').title()
                self.cursor.execute(
                    "INSERT INTO content_types (name, description) VALUES (%s, %s)",
                    (entity_name, f"Auto-created: {display_name}")
                )
                
            elif entity_type == 'tags':
                self.cursor.execute(
                    "INSERT INTO tags (name, usage_count) VALUES (%s, 0)",
                    (entity_name,)
                )
                
            elif entity_type == 'seasonal_challenges':
                self.cursor.execute(
                    "INSERT INTO seasonal_challenges (challenge_type, description) VALUES (%s, %s)",
                    (entity_name, f"Auto-created: {entity_name.replace('_', ' ').title()}")
                )
            
            entity_id = self.cursor.lastrowid
            self.existing_entities[entity_type].add(entity_name)
            logger.debug(f"Created new {entity_type}: {entity_name} (ID: {entity_id})")
            
            return entity_id
            
        except Error as e:
            logger.error(f"Error ensuring {entity_type} '{entity_name}': {e}")
            return None
    
    def _create_default_belt_level(self, belt_name: str):
        """Create a default belt level entry"""
        order_map = {
            'white-belt': 1, 'yellow-belt': 2, 'orange-belt': 3,
            'green-belt': 4, 'blue-belt': 5, 'brown-belt': 6, 'black-belt': 7
        }
        order = order_map.get(belt_name, 99)
        display_name = belt_name.replace('-', ' ').title()
        
        self.cursor.execute(
            "INSERT INTO belt_levels (name, display_name, description, level_order, xp_required) VALUES (%s, %s, %s, %s, %s)",
            (belt_name, display_name, f"Auto-created: {display_name}", order, 0)
        )
    
    def _safe_json(self, data: Any) -> Optional[str]:
        """Safely convert data to JSON string"""
        if data is None:
            return None
        if isinstance(data, str):
            return data
        try:
            return json.dumps(data, ensure_ascii=False)
        except:
            return None
    
    def _safe_decimal(self, value: Any) -> Optional[Decimal]:
        """Safely convert to decimal"""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except:
            return None
    
    def _safe_int(self, value: Any, default: int = None) -> Optional[int]:
        """Safely convert to integer"""
        if value is None:
            return default
        try:
            return int(value)
        except:
            return default
    
    def _safe_str(self, value: Any, max_length: int = None) -> Optional[str]:
        """Safely convert to string with optional truncation"""
        if value is None:
            return None
        
        result = str(value)
        if max_length and len(result) > max_length:
            result = result[:max_length-3] + '...'
        
        return result
    
    def _extract_from_nested(self, data: Dict, path: str, default: Any = None) -> Any:
        """Extract value from nested dictionary using dot notation"""
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    def import_story(self, story: Dict) -> bool:
        """Import a single story with all related data"""
        story_id = story.get('id')
        
        if not story_id:
            logger.error("Story missing ID")
            return False
        
        try:
            # Since autocommit is True, we manage transactions manually
            self.cursor.execute("START TRANSACTION")
            
            # 1. Import main story
            if not self._import_main_story(story):
                self.cursor.execute("ROLLBACK")
                return False
            
            # Store story_id for related tables
            self.cursor.execute("SET @story_id = %s", (story_id,))
            
            # 2. Import all related data
            self._import_story_source(story)
            self._import_story_scores(story)
            self._import_learning_outcomes(story)
            self._import_actionable_practices(story)
            self._import_discussion_prompts(story)
            self._import_risk_warnings(story)
            self._import_family_discussion_points(story)
            self._import_contrarian_viewpoints(story)
            self._import_age_translations(story)
            self._import_teaching_activities(story)
            self._import_search_keywords(story)
            
            # 3. Import relationships
            self._import_belt_levels(story)
            self._import_tags(story)
            self._import_seasonal_challenges(story)
            
            # Commit transaction
            self.cursor.execute("COMMIT")
            logger.info(f"Successfully imported story: {story_id}")
            return True
            
        except Exception as e:
            self.cursor.execute("ROLLBACK")
            logger.error(f"Error importing story '{story_id}': {e}")
            self.errors.append(f"Story '{story_id}': {str(e)}")
            return False
    
    def _import_main_story(self, story: Dict) -> bool:
        """Import the main story record with enhanced field handling"""
        try:
            # Get content type ID
            content_type = story.get('content_type', 'curriculum-war-story')
            content_type_id = self._ensure_lookup_entity('content_types', content_type)
            
            # Extract complex fields
            family_engagement = story.get('family_engagement_metrics', {})
            seasonal_challenge = story.get('seasonal_challenge_integration', {})
            performance_metrics = story.get('performance_metrics', {})
            spark_generation = story.get('spark_generation', {})
            
            # Map time_required to ENUM value - CRITICAL FIX
            raw_time = story.get('time_required')
            if not raw_time:
                raw_time = self._extract_from_nested(story, 'time_investment.learning_time')
            time_required = self._map_time_required(raw_time)
            
            # Prepare SQL
            sql = """
            INSERT INTO stories (
                id, title, summary, full_content, content_type_id,
                curriculum_alignment, ai_skill_level, ai_roi_potential,
                investment_domain_primary, difficulty_level, urgency,
                concept_hierarchy_level, learning_sequence_position,
                experience_assumptions, tech_savviness_required,
                expert_credentials, track_record_mentions, source_bias_assessment,
                quote_highlight, family_security_relevance, generational_wealth_relevance,
                children_education_angle, emergency_fund_consideration,
                risk_level, time_required, email_subject_line, social_snippet,
                community_hook, app_hook, podcast_hook, financial_disclaimer,
                is_spark, spark_xp_value, spark_discussion_prompt,
                dinner_table_readiness, family_activity_suggestion, generational_wealth_lesson,
                season_relevance, challenge_points, family_competition_angle,
                spark_3_minute_hook, spark_visual_metaphor, spark_swipe_up_moment,
                estimated_read_time, complexity_rating, retention_probability, application_difficulty,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                NOW(), NOW()
            )
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                summary = VALUES(summary),
                full_content = VALUES(full_content),
                updated_at = NOW()
            """
            
            # Extract season relevance properly
            season_relevance = []
            if seasonal_challenge:
                if 'season_relevance' in seasonal_challenge:
                    season_relevance = seasonal_challenge['season_relevance']
                elif 'challenge_milestones' in seasonal_challenge:
                    # Try to extract from milestones
                    for milestone in seasonal_challenge['challenge_milestones']:
                        if 'season_type' in milestone:
                            season_relevance.append(milestone['season_type'])
            
            params = (
                story['id'],
                story['title'],
                story['summary'],
                story['full_content'],
                content_type_id,
                story.get('curriculum_alignment'),
                story.get('ai_skill_level'),
                story.get('ai_roi_potential'),
                story.get('investment_domain_primary'),
                story.get('difficulty_level'),
                story.get('urgency'),
                story.get('concept_hierarchy_level'),
                story.get('learning_sequence_position'),
                story.get('experience_assumptions'),
                story.get('tech_savviness_required'),
                self._safe_json(story.get('expert_credentials')),
                story.get('track_record_mentions'),
                self._safe_json(story.get('source_bias_assessment')),
                story.get('quote_highlight'),
                self._extract_from_nested(story, 'family_security_relevance.primary_benefit') or story.get('family_security_relevance'),
                self._extract_from_nested(story, 'generational_wealth_relevance.wealth_building_potential') or story.get('generational_wealth_relevance'),
                self._safe_json(story.get('children_education_angle')),
                story.get('emergency_fund_consideration'),
                story.get('risk_level'),
                time_required,  # Now properly mapped
                story.get('email_subject_line'),
                self._extract_from_nested(story, 'social_media_hooks.twitter') or story.get('social_snippet'),
                self._extract_from_nested(story, 'community_engagement.discussion_starter') or story.get('community_hook'),
                self._extract_from_nested(story, 'app_integration.progress_tracking') or story.get('app_hook'),
                self._extract_from_nested(story, 'podcast_hooks.episode_tease') or story.get('podcast_hook'),
                bool(story.get('financial_disclaimer', True)),
                bool(spark_generation),  # is_spark
                self._safe_int(spark_generation.get('xp_value'), 10),
                spark_generation.get('family_discussion_starter') or story.get('spark_discussion_prompt'),
                self._safe_int(family_engagement.get('dinner_table_readiness')),
                family_engagement.get('family_activity_suggestion'),
                family_engagement.get('generational_wealth_lesson'),
                self._safe_json(season_relevance) if season_relevance else None,
                self._safe_int(seasonal_challenge.get('challenge_points')),
                seasonal_challenge.get('family_competition_angle'),
                spark_generation.get('3_minute_hook'),
                spark_generation.get('visual_metaphor'),
                spark_generation.get('swipe_up_moment'),
                performance_metrics.get('estimated_read_time'),
                performance_metrics.get('complexity_rating'),
                performance_metrics.get('retention_probability'),
                performance_metrics.get('application_difficulty')
            )
            
            self.cursor.execute(sql, params)
            return True
            
        except Exception as e:
            logger.error(f"Error importing main story: {e}")
            raise
    
    def _import_story_source(self, story: Dict):
        """Import story source information"""
        source = story.get('source', {})
        if not source:
            return
        
        try:
            sql = """
            INSERT INTO story_sources (
                story_id, podcast_title, episode_title, episode_url,
                media_url, episode_timestamp, host_name
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                podcast_title = VALUES(podcast_title),
                episode_title = VALUES(episode_title)
            """
            
            # Parse timestamp
            timestamp = source.get('timestamp', '00:00:00')
            if not re.match(r'^\d{2}:\d{2}:\d{2}$', timestamp):
                timestamp = '00:00:00'
            
            params = (
                story['id'],
                source.get('podcast_title'),
                source.get('episode_title'),
                source.get('episode_url'),
                source.get('media_url'),
                timestamp,
                source.get('host_name')
            )
            
            self.cursor.execute(sql, params)
            
        except Exception as e:
            logger.warning(f"Could not import source for story {story['id']}: {e}")
    
    def _import_story_scores(self, story: Dict):
        """Import story scores with enhanced handling"""
        try:
            scoring = story.get('scoring', {})
            
            sql = """
            INSERT INTO story_scores (
                story_id, curriculum_value, engagement_score, practical_score,
                ai_innovation_score, belt_progression_xp,
                confidence_building, family_impact, mastery_potential, viral_potential
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                curriculum_value = VALUES(curriculum_value),
                engagement_score = VALUES(engagement_score)
            """
            
            params = (
                story['id'],
                self._safe_int(scoring.get('curriculum_value'), 5),
                self._safe_int(scoring.get('engagement_score'), 5),
                self._safe_int(scoring.get('practical_score'), 5),
                self._safe_int(scoring.get('ai_innovation_score'), 5),
                self._safe_int(story.get('belt_progression_xp'), 10),
                self._safe_int(scoring.get('confidence_building'), 5),
                self._safe_int(scoring.get('family_impact'), 5),
                self._safe_int(scoring.get('mastery_potential'), 5),
                self._safe_int(scoring.get('viral_potential'), 5)
            )
            
            self.cursor.execute(sql, params)
            
        except Exception as e:
            logger.warning(f"Could not import scores for story {story['id']}: {e}")
    
    def _import_learning_outcomes(self, story: Dict):
        """Import learning outcomes"""
        outcomes = story.get('learning_outcomes', [])
        if not outcomes:
            return
        
        for i, outcome_data in enumerate(outcomes):
            try:
                if isinstance(outcome_data, str):
                    outcome_text = outcome_data
                else:
                    outcome_text = outcome_data.get('outcome', str(outcome_data))
                
                sql = """
                INSERT INTO learning_outcomes (story_id, outcome, display_order)
                VALUES (%s, %s, %s)
                """
                
                self.cursor.execute(sql, (story['id'], outcome_text, i + 1))
                
            except Exception as e:
                logger.warning(f"Could not import learning outcome {i} for story {story['id']}: {e}")
    
    def _import_actionable_practices(self, story: Dict):
        """Import actionable practices"""
        practices = story.get('actionable_practices', [])
        checklist = story.get('implementation_checklist', [])
        
        order = 1
        
        # Import regular practices
        for practice_data in practices:
            try:
                if isinstance(practice_data, str):
                    practice_text = practice_data
                else:
                    practice_text = practice_data.get('practice', str(practice_data))
                
                sql = """
                INSERT INTO actionable_practices (story_id, practice, display_order)
                VALUES (%s, %s, %s)
                """
                
                self.cursor.execute(sql, (story['id'], practice_text, order))
                order += 1
                
            except Exception as e:
                logger.warning(f"Could not import practice for story {story['id']}: {e}")
        
        # Import checklist items as practices
        for i, item in enumerate(checklist):
            try:
                step_text = item.get('step', '') if isinstance(item, dict) else str(item)
                if step_text:
                    practice_text = f"[Checklist] {step_text}"
                    sql = """
                    INSERT INTO actionable_practices (story_id, practice, display_order)
                    VALUES (%s, %s, %s)
                    """
                    self.cursor.execute(sql, (story['id'], practice_text, 100 + i))
                    
            except Exception as e:
                logger.warning(f"Could not import checklist item for story {story['id']}: {e}")
    
    def _import_discussion_prompts(self, story: Dict):
        """Import discussion prompts"""
        prompts = story.get('discussion_prompts', [])
        
        for i, prompt_data in enumerate(prompts):
            try:
                if isinstance(prompt_data, str):
                    prompt_text = prompt_data
                else:
                    prompt_text = prompt_data.get('prompt', str(prompt_data))
                
                sql = """
                INSERT INTO discussion_prompts (story_id, prompt, display_order)
                VALUES (%s, %s, %s)
                """
                
                self.cursor.execute(sql, (story['id'], prompt_text, i + 1))
                
            except Exception as e:
                logger.warning(f"Could not import prompt for story {story['id']}: {e}")
    
    def _import_risk_warnings(self, story: Dict):
        """Import risk warnings"""
        warnings = story.get('risk_warnings', [])
        
        for i, warning_data in enumerate(warnings):
            try:
                if isinstance(warning_data, str):
                    warning_text = warning_data
                else:
                    warning_text = warning_data.get('warning', str(warning_data))
                
                sql = """
                INSERT INTO risk_warnings (story_id, warning, display_order)
                VALUES (%s, %s, %s)
                """
                
                self.cursor.execute(sql, (story['id'], warning_text, i + 1))
                
            except Exception as e:
                logger.warning(f"Could not import warning for story {story['id']}: {e}")
    
    def _import_family_discussion_points(self, story: Dict):
        """Import family discussion points"""
        points = story.get('family_discussion_points', [])
        
        for i, point_data in enumerate(points):
            try:
                if isinstance(point_data, str):
                    point_text = point_data
                else:
                    point_text = point_data.get('topic', str(point_data))
                
                sql = """
                INSERT INTO family_discussion_points (story_id, point, display_order)
                VALUES (%s, %s, %s)
                """
                
                self.cursor.execute(sql, (story['id'], point_text, i + 1))
                
            except Exception as e:
                logger.warning(f"Could not import family point for story {story['id']}: {e}")
    
    def _import_contrarian_viewpoints(self, story: Dict):
        """Import contrarian viewpoints"""
        viewpoints = story.get('contrarian_viewpoints', [])
        
        for i, viewpoint_data in enumerate(viewpoints):
            try:
                if isinstance(viewpoint_data, str):
                    viewpoint_text = viewpoint_data
                else:
                    viewpoint_text = viewpoint_data.get('viewpoint', str(viewpoint_data))
                
                sql = """
                INSERT INTO contrarian_viewpoints (story_id, viewpoint, display_order)
                VALUES (%s, %s, %s)
                """
                
                self.cursor.execute(sql, (story['id'], viewpoint_text, i + 1))
                
            except Exception as e:
                logger.warning(f"Could not import viewpoint for story {story['id']}: {e}")
    
    def _import_age_translations(self, story: Dict):
        """Import age-appropriate translations"""
        children_ed = story.get('children_education_angle', {})
        if not isinstance(children_ed, dict):
            return
        
        age_concepts = children_ed.get('age_appropriate_concepts', {})
        if not isinstance(age_concepts, dict):
            return
        
        order = 0
        for age_group, translation in age_concepts.items():
            try:
                if translation and age_group in ['ages_5_10', 'ages_11_16', 'ages_17_plus']:
                    sql = """
                    INSERT INTO story_age_translations (
                        story_id, age_group, translation, display_order
                    ) VALUES (%s, %s, %s, %s)
                    """
                    
                    self.cursor.execute(sql, (story['id'], age_group, translation, order))
                    order += 1
                    
            except Exception as e:
                logger.warning(f"Could not import age translation for story {story['id']}: {e}")
    
    def _import_teaching_activities(self, story: Dict):
        """Import teaching activities"""
        children_ed = story.get('children_education_angle', {})
        if isinstance(children_ed, dict):
            activities = children_ed.get('teaching_activities', [])
            
            for i, activity in enumerate(activities):
                try:
                    if activity:
                        sql = """
                        INSERT INTO story_teaching_activities (
                            story_id, activity, age_group, display_order
                        ) VALUES (%s, %s, %s, %s)
                        """
                        
                        self.cursor.execute(sql, (story['id'], activity, 'all', i + 1))
                        
                except Exception as e:
                    logger.warning(f"Could not import teaching activity for story {story['id']}: {e}")
    
    def _import_search_keywords(self, story: Dict):
        """Import search keywords"""
        keywords = story.get('search_keywords', [])
        
        for keyword_data in keywords:
            try:
                if isinstance(keyword_data, str):
                    keyword_text = keyword_data
                else:
                    keyword_text = keyword_data.get('keyword', str(keyword_data))
                
                if keyword_text:
                    sql = """
                    INSERT INTO search_keywords (story_id, keyword)
                    VALUES (%s, %s)
                    """
                    
                    self.cursor.execute(sql, (story['id'], keyword_text))
                    
            except Exception as e:
                logger.warning(f"Could not import keyword for story {story['id']}: {e}")
    
    def _import_belt_levels(self, story: Dict):
        """Import belt level relationships"""
        belt_levels = story.get('belt_levels', [])
        
        for belt_name in belt_levels:
            try:
                belt_id = self._ensure_lookup_entity('belt_levels', belt_name)
                if belt_id:
                    sql = """
                    INSERT IGNORE INTO story_belt_levels (story_id, belt_level_id)
                    VALUES (%s, %s)
                    """
                    
                    self.cursor.execute(sql, (story['id'], belt_id))
                    
            except Exception as e:
                logger.warning(f"Could not link belt level '{belt_name}' to story {story['id']}: {e}")
    
    def _import_tags(self, story: Dict):
        """Import tag relationships with enhanced handling"""
        tags_data = story.get('tags', {})
        all_tags = set()
        
        if isinstance(tags_data, dict):
            all_tags.update(tags_data.get('primary', []))
            all_tags.update(tags_data.get('secondary', []))
            all_tags.update(tags_data.get('trending', []))
        elif isinstance(tags_data, list):
            all_tags.update(tags_data)
        
        for tag in all_tags:
            if not tag:
                continue
            
            try:
                tag_id = self._ensure_lookup_entity('tags', tag)
                if tag_id:
                    sql = """
                    INSERT IGNORE INTO story_tags (story_id, tag_id)
                    VALUES (%s, %s)
                    """
                    
                    self.cursor.execute(sql, (story['id'], tag_id))
                    
                    # Update usage count
                    self.cursor.execute(
                        "UPDATE tags SET usage_count = usage_count + 1 WHERE id = %s",
                        (tag_id,)
                    )
                    
            except Exception as e:
                logger.warning(f"Could not link tag '{tag}' to story {story['id']}: {e}")
    
    def _import_seasonal_challenges(self, story: Dict):
        """Import seasonal challenge relationships"""
        seasonal_data = story.get('seasonal_challenge_integration', {})
        season_types = set()
        
        # Extract from different possible locations
        if isinstance(seasonal_data, dict):
            season_relevance = seasonal_data.get('season_relevance', [])
            if isinstance(season_relevance, list):
                season_types.update(season_relevance)
        
        # Also check direct season_relevance field
        direct_relevance = story.get('season_relevance')
        if isinstance(direct_relevance, list):
            season_types.update(direct_relevance)
        elif isinstance(direct_relevance, str):
            # Handle JSON string
            try:
                parsed = json.loads(direct_relevance)
                if isinstance(parsed, list):
                    season_types.update(parsed)
            except:
                pass
        
        for season_type in season_types:
            if not season_type:
                continue
            
            try:
                # Ensure the seasonal challenge exists
                challenge_id = self._ensure_lookup_entity('seasonal_challenges', season_type)
                
                if challenge_id:
                    sql = """
                    INSERT IGNORE INTO story_seasonal_challenges (story_id, season_type)
                    VALUES (%s, %s)
                    """
                    
                    self.cursor.execute(sql, (story['id'], season_type))
                    
            except Exception as e:
                logger.warning(f"Could not link seasonal challenge '{season_type}' to story {story['id']}: {e}")
    
    def process_all_stories(self) -> bool:
        """Process all stories with progress tracking"""
        if not self.content_data:
            logger.error("No content data loaded")
            return False
        
        stories = self.content_data['stories']
        total = len(stories)
        success_count = 0
        
        logger.info(f"Starting import of {total} stories...")
        
        for i, story in enumerate(stories, 1):
            title = story.get('title', 'Untitled')
            story_id = story.get('id', 'Unknown')
            
            logger.info(f"[{i}/{total}] Processing: {title}")
            
            if self.dry_run:
                logger.info(f"  [DRY RUN] Would import story: {story_id}")
                success_count += 1
            else:
                if self.import_story(story):
                    success_count += 1
                else:
                    logger.error(f"  Failed to import: {story_id}")
        
        self.imported_count = success_count
        
        # Summary
        logger.info("=" * 70)
        logger.info(f"Import Summary:")
        logger.info(f"  Total stories: {total}")
        logger.info(f"  Successfully imported: {success_count}")
        logger.info(f"  Failed: {total - success_count}")
        logger.info(f"  Errors: {len(self.errors)}")
        logger.info(f"  Warnings: {len(self.warnings)}")
        
        if self.errors:
            logger.error("First 5 errors:")
            for error in self.errors[:5]:
                logger.error(f"  - {error}")
        
        return success_count > 0
    
    def close_connection(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Database connection closed")
    
    def run(self) -> bool:
        """Main execution method"""
        logger.info(f"Starting enhanced import process")
        logger.info(f"JSON file: {self.json_file_path}")
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE IMPORT'}")
        
        # Load JSON
        if not self.load_json():
            return False
        
        # Connect to database
        if not self.connect_to_database():
            return False
        
        try:
            # Process all stories
            success = self.process_all_stories()
            
            if success:
                logger.info("Import completed successfully!")
            else:
                logger.error("Import failed")
            
            return success
            
        finally:
            self.close_connection()


def main():
    """Enhanced main entry point"""
    parser = argparse.ArgumentParser(
        description='Enhanced InvestingDojo Content Importer - Beautifully integrates JSON into MariaDB'
    )
    parser.add_argument(
        'json_file',
        help='Path to JSON file containing investing-dojo stories'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Analyze what would be imported without executing'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate JSON file exists
    if not os.path.exists(args.json_file):
        logger.error(f"JSON file not found: {args.json_file}")
        sys.exit(1)
    
    # Create and run importer
    importer = EnhancedContentImporter(args.json_file, dry_run=args.dry_run)
    success = importer.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
