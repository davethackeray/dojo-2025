#!/usr/bin/env python3

"""
InvestingDojo Content Importer
Converts JSON story files to SQL and imports them into the database
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
from typing import Dict, List, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class ContentImporter:
    """Handles the conversion of JSON content to SQL and database import"""
    
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
        self.connection = None
        self.cursor = None
        self.content_data = None
        self.imported_count = 0
        self.errors = []
        
        # Cache for lookup tables
        self.lookup_cache = {
            'content_types': {},
            'belt_levels': {},
            'curriculum_categories': {},
            'ai_tools': {},
            'investor_profiles': {},
            'life_stages': {},
            'time_horizons': {},
            'capital_sizes': {},
            'tags': {},
            'concepts': {}
        }
        
        # Database connection parameters with environment variables
        self.db_config = {
            'host': os.getenv('DB_PROD_HOST', 'srv1910.hstgr.io'),
            'database': os.getenv('DB_PROD_DATABASE', 'u219832816_investing_dojo'),
            'user': os.getenv('DB_PROD_USER', 'u219832816_davethackeray'),
            'password': os.getenv('DB_PROD_PASSWORD', 'ToTheM00n!'),
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': False
        }
        
        # Validate database configuration
        self._validate_db_config()
    
    def _validate_db_config(self):
        """Validate database configuration and provide helpful error messages"""
        required_fields = ['host', 'database', 'user', 'password']
        missing_fields = []
        
        for field in required_fields:
            if not self.db_config.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            env_vars = {
                'host': 'DB_PROD_HOST',
                'database': 'DB_PROD_DATABASE',
                'user': 'DB_PROD_USER',
                'password': 'DB_PROD_PASSWORD'
            }
            
            missing_env_vars = [env_vars[field] for field in missing_fields]
            
            logger.error("❌ Missing production database configuration:")
            for field, env_var in zip(missing_fields, missing_env_vars):
                logger.error(f"   - {field}: Set environment variable {env_var}")
            
            logger.error("\n💡 To fix this:")
            logger.error("   1. Create a .env file based on .env.example")
            logger.error("   2. Set the missing environment variables:")
            for env_var in missing_env_vars:
                logger.error(f"      export {env_var}=your_value")
            logger.error("   3. Or set them in your system environment")
            
            raise ValueError(f"Missing required database configuration: {', '.join(missing_fields)}")
        
        # Warn if using default credentials
        if self.db_config['password'] == 'ToTheM00n!' and os.getenv('ENVIRONMENT') == 'production':
            logger.warning("⚠️ Using default database password in production environment!")
            logger.warning("   Please set DB_PROD_PASSWORD environment variable for security.")
        
        logger.info("✅ Production database configuration validated")
    
    def load_json(self) -> bool:
        """Load and validate JSON file"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                self.content_data = json.load(f)
            
            # Check for both possible keys
            if 'investing-dojo-story' in self.content_data:
                self.content_data['stories'] = self.content_data['investing-dojo-story']
            elif 'newsletter_content' in self.content_data:
                self.content_data['stories'] = self.content_data['newsletter_content']
            else:
                logger.error("JSON file missing story data")
                return False
            
            logger.info(f"Loaded {len(self.content_data['stories'])} stories from JSON")
            return True
        except Exception as e:
            logger.error(f"Error loading JSON file: {e}")
            return False
    
    def connect_to_database(self) -> bool:
        """Establish connection to MySQL database"""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            self.cursor = self.connection.cursor()
            
            # Ensure clean transaction state
            try:
                if self.connection.in_transaction:
                    self.connection.rollback()
            except:
                pass  # Ignore if checking transaction state fails
            
            logger.info("Successfully connected to database")
            return True
        except Error as e:
            logger.error(f"Error connecting to database: {e}")
            return False
    
    def initialize_lookup_data(self) -> bool:
        """Populate lookup tables with required data"""
        try:
            # Belt levels
            belt_levels = [
                ('white-belt', 'White Belt', 'Foundational Understanding & Mindset', 1, 0),
                ('yellow-belt', 'Yellow Belt', 'Core Investing Knowledge', 2, 100),
                ('orange-belt', 'Orange Belt', 'Early Trading Strategies & Research', 3, 300),
                ('green-belt', 'Green Belt', 'Developing Your Edge', 4, 600),
                ('blue-belt', 'Blue Belt', 'Refining Execution & Control', 5, 1000),
                ('brown-belt', 'Brown Belt', 'Analytical Mastery & Systematisation', 6, 1500),
                ('black-belt', 'Black Belt', 'Adaptive Mastery & Lifelong Practice', 7, 2000),
                ('all-levels', 'All Levels', 'Universal wisdom that transcends belt levels', 0, 0)
            ]
            
            for name, display_name, desc, order, xp in belt_levels:
                self.cursor.execute("""
                    INSERT IGNORE INTO belt_levels (name, display_name, description, level_order, xp_required)
                    VALUES (%s, %s, %s, %s, %s)
                """, (name, display_name, desc, order, xp))
            
            # Curriculum categories
            categories = [
                'mindset-discipline', 'system-building', 'risk-management', 'research-analysis',
                'edge-identification', 'execution-tactics', 'market-cycles', 'continuous-improvement',
                'master-investor-study', 'portfolio-construction', 'ai-augmentation'
            ]
            
            for cat in categories:
                self.cursor.execute("""
                    INSERT IGNORE INTO curriculum_categories (name, description)
                    VALUES (%s, %s)
                """, (cat, f"Curriculum category: {cat.replace('-', ' ').title()}"))
            
            # Investor profiles
            profiles = ['conservative', 'moderate', 'aggressive']
            for profile in profiles:
                self.cursor.execute("""
                    INSERT IGNORE INTO investor_profiles (name)
                    VALUES (%s)
                """, (profile,))
            
            # Life stages
            stages = ['family-building', 'pre-retirement', 'retired']
            for stage in stages:
                self.cursor.execute("""
                    INSERT IGNORE INTO life_stages (name)
                    VALUES (%s)
                """, (stage,))
            
            # Time horizons
            horizons = ['short-term', 'medium-term', 'long-term']
            for horizon in horizons:
                self.cursor.execute("""
                    INSERT IGNORE INTO time_horizons (name)
                    VALUES (%s)
                """, (horizon,))
            
            # Capital sizes
            capital_sizes = [
                ('under-1k', 0, 1000),
                ('1k-10k', 1000, 10000),
                ('10k-100k', 10000, 100000),
                ('100k-1m', 100000, 1000000),
                ('any-size', 0, None)
            ]
            
            for name, min_amt, max_amt in capital_sizes:
                self.cursor.execute("""
                    INSERT IGNORE INTO capital_sizes (name, min_amount, max_amount)
                    VALUES (%s, %s, %s)
                """, (name, min_amt, max_amt))
            
            logger.info("Lookup data initialized successfully")
            return True
        except Error as e:
            logger.error(f"Error initializing lookup data: {e}")
            return False
    
    def load_lookup_cache(self):
        """Load all lookup table IDs into cache"""
        lookup_queries = {
            'content_types': "SELECT id, name FROM content_types",
            'belt_levels': "SELECT id, name FROM belt_levels", 
            'curriculum_categories': "SELECT id, name FROM curriculum_categories",
            'ai_tools': "SELECT id, name FROM ai_tools",
            'investor_profiles': "SELECT id, name FROM investor_profiles",
            'life_stages': "SELECT id, name FROM life_stages",
            'time_horizons': "SELECT id, name FROM time_horizons",
            'capital_sizes': "SELECT id, name FROM capital_sizes",
            'tags': "SELECT id, name FROM tags",
            'concepts': "SELECT id, name FROM concepts"
        }
        
        for table, query in lookup_queries.items():
            try:
                self.cursor.execute(query)
                for row in self.cursor.fetchall():
                    self.lookup_cache[table][row[1]] = row[0]
                logger.debug(f"Loaded {len(self.lookup_cache[table])} entries for {table}")
            except Error as e:
                logger.warning(f"Could not load {table}: {e}")
                # Continue with empty cache for this table
                pass
    
    def get_or_create_id(self, table: str, name: str, additional_fields: Dict = None) -> Optional[int]:
        """Get ID from cache or create new entry and return ID"""
        if name in self.lookup_cache[table]:
            return self.lookup_cache[table][name]
        
        # Create new entry
        try:
            if table == 'tags':
                self.cursor.execute("""
                    INSERT INTO tags (name, usage_count) VALUES (%s, 0)
                """, (name,))
            elif table == 'concepts':
                self.cursor.execute("""
                    INSERT INTO concepts (name, concept_type) VALUES (%s, 'node')
                """, (name,))
            elif table == 'ai_tools':
                self.cursor.execute("""
                    INSERT INTO ai_tools (name) VALUES (%s)
                """, (name,))
            else:
                logger.warning(f"Cannot auto-create entry for table {table}")
                return None
            
            new_id = self.cursor.lastrowid
            self.lookup_cache[table][name] = new_id
            return new_id
        except Error as e:
            logger.error(f"Error creating entry in {table}: {e}")
            return None
    
    def process_story(self, story: Dict[str, Any]) -> bool:
        """Process a single story"""
        try:
            # Get content type ID  
            content_type = story.get('content_type')
            if isinstance(content_type, list) and len(content_type) > 0:
                content_type = content_type[0]
            
            content_type_id = self.lookup_cache['content_types'].get(content_type)
            if not content_type_id:
                logger.error(f"Unknown content type: {content_type}")
                return False
            
            # Insert main story
            story_values = (
                story.get('id'),
                story.get('title'),
                story.get('summary'),
                story.get('full_content'),
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
                story.get('expert_credentials'),
                story.get('track_record_mentions'),
                story.get('source_bias_assessment'),
                story.get('quote_highlight'),
                story.get('family_security_relevance'),
                story.get('generational_wealth_relevance'),
                story.get('children_education_angle'),
                story.get('emergency_fund_consideration'),
                story.get('risk_level'),
                story.get('time_required'),
                story.get('email_subject_line'),
                story.get('social_snippet'),
                story.get('community_hook'),
                story.get('app_hook'),
                story.get('podcast_hook'),
                1 if story.get('financial_disclaimer', True) else 0
            )
            
            self.cursor.execute("""
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
                    community_hook, app_hook, podcast_hook, financial_disclaimer
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, story_values)
            
            story_id = story.get('id')
            
            # Process related data
            self.process_belt_levels(story_id, story.get('belt_levels', []))
            self.process_curriculum_categories(story_id, story.get('curriculum_categories', []))
            self.process_prerequisites(story_id, story.get('prerequisites', []))
            self.process_learning_outcomes(story_id, story.get('learning_outcomes', []))
            self.process_ai_tools(story_id, story.get('ai_tools_mentioned', []))
            self.process_concepts(story_id, story)
            self.process_user_matching(story_id, story)
            self.process_source(story_id, story.get('source', {}))
            self.process_scores(story_id, story)
            self.process_learning_pathway(story_id, story.get('learning_pathway_position', {}))
            self.process_actionable_content(story_id, story)
            self.process_tags(story_id, story.get('tags', []))
            self.process_keywords(story_id, story.get('search_keywords', []))
            self.process_risk_warnings(story_id, story.get('risk_warnings', []))
            
            return True
        except Error as e:
            logger.error(f"Error processing story {story.get('id')}: {e}")
            return False
    
    def process_belt_levels(self, story_id: str, belt_levels: List[str]):
        """Process belt levels for a story"""
        for belt in belt_levels:
            belt_id = self.lookup_cache['belt_levels'].get(belt)
            if belt_id:
                self.cursor.execute("""
                    INSERT INTO story_belt_levels (story_id, belt_level_id)
                    VALUES (%s, %s)
                """, (story_id, belt_id))
    
    def process_curriculum_categories(self, story_id: str, categories: List[str]):
        """Process curriculum categories"""
        for cat in categories:
            cat_id = self.lookup_cache['curriculum_categories'].get(cat)
            if cat_id:
                self.cursor.execute("""
                    INSERT INTO story_curriculum_categories (story_id, category_id)
                    VALUES (%s, %s)
                """, (story_id, cat_id))
    
    def process_prerequisites(self, story_id: str, prerequisites: List[str]):
        """Process prerequisites"""
        for prereq in prerequisites:
            belt_id = self.lookup_cache['belt_levels'].get(prereq)
            if belt_id:
                self.cursor.execute("""
                    INSERT INTO story_prerequisites (story_id, prerequisite_belt_id)
                    VALUES (%s, %s)
                """, (story_id, belt_id))
    
    def process_learning_outcomes(self, story_id: str, outcomes: List[str]):
        """Process learning outcomes"""
        for i, outcome in enumerate(outcomes):
            self.cursor.execute("""
                INSERT INTO learning_outcomes (story_id, outcome, display_order)
                VALUES (%s, %s, %s)
            """, (story_id, outcome, i))
    
    def process_ai_tools(self, story_id: str, tools: List[str]):
        """Process AI tools"""
        for tool in tools:
            tool_id = self.get_or_create_id('ai_tools', tool)
            if tool_id:
                self.cursor.execute("""
                    INSERT INTO story_ai_tools (story_id, ai_tool_id)
                    VALUES (%s, %s)
                """, (story_id, tool_id))
    
    def process_concepts(self, story_id: str, story: Dict):
        """Process all concept-related data"""
        concept_mappings = [
            ('knowledge_graph_nodes', 'knowledge_node'),
            ('parent_concepts', 'parent_concept'),
            ('child_concepts', 'child_concept'),
            ('pillar_topic_candidates', 'pillar_candidate'),
            ('content_cluster_suggestions', 'cluster_suggestion'),
            ('course_module_potential', 'course_module')
        ]
        
        for field, relationship_type in concept_mappings:
            concepts = story.get(field, [])
            for concept in concepts:
                concept_id = self.get_or_create_id('concepts', concept)
                if concept_id:
                    self.cursor.execute("""
                        INSERT INTO story_concepts (story_id, concept_id, relationship_type)
                        VALUES (%s, %s, %s)
                    """, (story_id, concept_id, relationship_type))
    
    def process_user_matching(self, story_id: str, story: Dict):
        """Process user personalisation matching"""
        # Investor profiles
        for profile in story.get('investor_profile_match', []):
            profile_id = self.lookup_cache['investor_profiles'].get(profile)
            if profile_id:
                self.cursor.execute("""
                    INSERT INTO story_investor_profiles (story_id, profile_id)
                    VALUES (%s, %s)
                """, (story_id, profile_id))
        
        # Life stages
        for stage in story.get('life_stage_relevance', []):
            stage_id = self.lookup_cache['life_stages'].get(stage)
            if stage_id:
                self.cursor.execute("""
                    INSERT INTO story_life_stages (story_id, life_stage_id)
                    VALUES (%s, %s)
                """, (story_id, stage_id))
        
        # Time horizons
        for horizon in story.get('time_horizon_focus', []):
            horizon_id = self.lookup_cache['time_horizons'].get(horizon)
            if horizon_id:
                self.cursor.execute("""
                    INSERT INTO story_time_horizons (story_id, time_horizon_id)
                    VALUES (%s, %s)
                """, (story_id, horizon_id))
        
        # Capital sizes
        for size in story.get('capital_size_relevance', []):
            size_id = self.lookup_cache['capital_sizes'].get(size)
            if size_id:
                self.cursor.execute("""
                    INSERT INTO story_capital_sizes (story_id, capital_size_id)
                    VALUES (%s, %s)
                """, (story_id, size_id))
    
    def process_source(self, story_id: str, source: Dict):
        """Process source information"""
        if source:
            # Parse timestamp
            timestamp_str = source.get('timestamp', '00:00:00')
            self.cursor.execute("""
                INSERT INTO story_sources (
                    story_id, podcast_title, episode_title, episode_url,
                    media_url, timestamp, host_name
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                story_id,
                source.get('podcast_title'),
                source.get('episode_title'),
                source.get('episode_url'),
                source.get('media_url'),
                timestamp_str,
                source.get('host_name')
            ))
    
    def process_scores(self, story_id: str, story: Dict):
        """Process story scores"""
        xp = story.get('belt_progression_xp', 0)
        curriculum_value = story.get('curriculum_value', 5)
        engagement_score = story.get('engagement_score', 5)
        practical_score = story.get('practical_score', 5)
        ai_innovation_score = story.get('ai_innovation_score', 5)
        
        # Ensure values are within acceptable range (1-10)
        curriculum_value = max(1, min(10, curriculum_value))
        engagement_score = max(1, min(10, engagement_score))
        practical_score = max(1, min(10, practical_score))
        ai_innovation_score = max(1, min(10, ai_innovation_score))
        
        self.cursor.execute("""
            INSERT INTO story_scores (
                story_id, curriculum_value, engagement_score,
                practical_score, ai_innovation_score, belt_progression_xp
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            story_id,
            curriculum_value,
            engagement_score,
            practical_score,
            ai_innovation_score,
            xp
        ))
    
    def process_learning_pathway(self, story_id: str, pathway: Dict):
        """Process learning pathway data"""
        if pathway:
            self.cursor.execute("""
                INSERT INTO learning_pathways (
                    story_id, journey_stage, skill_tree_position
                ) VALUES (%s, %s, %s)
            """, (
                story_id,
                pathway.get('journey_stage'),
                pathway.get('skill_tree_position')
            ))
            
            pathway_id = self.cursor.lastrowid
            
            # Process pathway branches
            for branch in pathway.get('pathway_branches', []):
                self.cursor.execute("""
                    INSERT INTO pathway_branches (pathway_id, branch_name)
                    VALUES (%s, %s)
                """, (pathway_id, branch))
    
    def process_actionable_content(self, story_id: str, story: Dict):
        """Process all actionable content"""
        # Actionable practices
        for i, practice in enumerate(story.get('actionable_practices', [])):
            self.cursor.execute("""
                INSERT INTO actionable_practices (story_id, practice, display_order)
                VALUES (%s, %s, %s)
            """, (story_id, practice, i))
        
        # Discussion prompts
        for i, prompt in enumerate(story.get('discussion_prompts', [])):
            self.cursor.execute("""
                INSERT INTO discussion_prompts (story_id, prompt, display_order)
                VALUES (%s, %s, %s)
            """, (story_id, prompt, i))
        
        # Family discussion points
        for i, point in enumerate(story.get('family_discussion_points', [])):
            self.cursor.execute("""
                INSERT INTO family_discussion_points (story_id, point, display_order)
                VALUES (%s, %s, %s)
            """, (story_id, point, i))
        
        # Contrarian viewpoints
        for i, viewpoint in enumerate(story.get('contrarian_viewpoints', [])):
            self.cursor.execute("""
                INSERT INTO contrarian_viewpoints (story_id, viewpoint, display_order)
                VALUES (%s, %s, %s)
            """, (story_id, viewpoint, i))
    
    def process_tags(self, story_id: str, tags: List[str]):
        """Process tags"""
        for tag in tags:
            tag_id = self.get_or_create_id('tags', tag)
            if tag_id:
                self.cursor.execute("""
                    INSERT INTO story_tags (story_id, tag_id)
                    VALUES (%s, %s)
                """, (story_id, tag_id))
                
                # Update usage count
                self.cursor.execute("""
                    UPDATE tags SET usage_count = usage_count + 1
                    WHERE id = %s
                """, (tag_id,))
    
    def process_keywords(self, story_id: str, keywords: List[str]):
        """Process search keywords"""
        for keyword in keywords:
            self.cursor.execute("""
                INSERT INTO search_keywords (story_id, keyword)
                VALUES (%s, %s)
            """, (story_id, keyword))
    
    def process_risk_warnings(self, story_id: str, warnings: List[str]):
        """Process risk warnings"""
        for i, warning in enumerate(warnings):
            self.cursor.execute("""
                INSERT INTO risk_warnings (story_id, warning, display_order)
                VALUES (%s, %s, %s)
            """, (story_id, warning, i))
    
    def process_episode_summary(self):
        """Process episode summary if present"""
        if 'episode_summary' in self.content_data:
            summary = self.content_data['episode_summary']
            
            # Get first story's source for episode info
            if len(self.content_data['stories']) > 0:
                first_source = self.content_data['stories'][0].get('source', {})
                
                self.cursor.execute("""
                    INSERT INTO episode_summaries (
                        podcast_title, episode_title, total_extracted,
                        curriculum_quality, ai_opportunities, family_security_impact
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    first_source.get('podcast_title'),
                    first_source.get('episode_title'),
                    summary.get('total_extracted', 0),
                    summary.get('curriculum_quality'),
                    summary.get('ai_opportunities'),
                    summary.get('family_security_impact')
                ))
                
                episode_id = self.cursor.lastrowid
                
                # Process target belts
                for belt in summary.get('target_belts', []):
                    belt_id = self.lookup_cache['belt_levels'].get(belt)
                    if belt_id:
                        self.cursor.execute("""
                            INSERT INTO episode_summary_belts (episode_summary_id, belt_level_id)
                            VALUES (%s, %s)
                        """, (episode_id, belt_id))
    
    def run(self, dry_run: bool = False) -> bool:
        """Main execution method"""
        logger.info(f"Starting import process for: {self.json_file_path}")
        
        # Load JSON
        if not self.load_json():
            return False
        
        if dry_run:
            logger.info("Dry run mode - no database changes will be made")
            return True
        
        # Connect to database
        if not self.connect_to_database():
            return False
        
        try:
            # Initialize lookup data
            if not self.initialize_lookup_data():
                return False
            
            # Commit the lookup data initialization
            self.connection.commit()
            
            # Load lookup cache
            self.load_lookup_cache()
            
            # Process each story
            success_count = 0
            for story in self.content_data['stories']:
                logger.info(f"Processing: {story.get('title', 'Untitled')}")
                
                # Start fresh transaction for each story
                try:
                    # Ensure we're not in a transaction
                    if self.connection.in_transaction:
                        self.connection.rollback()
                    
                    self.connection.start_transaction()
                    
                    if self.process_story(story):
                        success_count += 1
                        self.connection.commit()
                        logger.info(f"Successfully processed: {story.get('title', 'Untitled')}")
                    else:
                        self.connection.rollback()
                        logger.error(f"Failed to process: {story.get('title', 'Untitled')}")
                        
                except Exception as e:
                    if self.connection.in_transaction:
                        self.connection.rollback()
                    logger.error(f"Exception processing story: {e}")
            
            # Process episode summary
            if 'episode_summary' in self.content_data:
                try:
                    if self.connection.in_transaction:
                        self.connection.rollback()
                        
                    self.connection.start_transaction()
                    self.process_episode_summary()
                    self.connection.commit()
                except Exception as e:
                    if self.connection.in_transaction:
                        self.connection.rollback()
                    logger.error(f"Exception processing episode summary: {e}")
            
            self.imported_count = success_count
            logger.info(f"Import complete: {success_count}/{len(self.content_data['stories'])} stories imported")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            if self.connection and self.connection.in_transaction:
                self.connection.rollback()
            import traceback
            traceback.print_exc()
            return False
        finally:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("Database connection closed")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Import InvestingDojo content from JSON to MySQL database'
    )
    
    parser.add_argument(
        'json_file',
        help='Path to JSON file containing story content'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Generate SQL file without executing (for review)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
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
    importer = ContentImporter(args.json_file)
    success = importer.run(dry_run=args.dry_run)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
