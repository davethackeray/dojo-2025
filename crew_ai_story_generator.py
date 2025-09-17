#!/usr/bin/env python3
"""
CREWAI STORY GENERATOR MODULE - 9 SPECIALIZED AGENTS
Multi-agent story generation using CrewAI framework with Gemini AI backend
Implements the complete agentic workflow from SuperPrompt_Agentic_Workflow.md
"""

import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# CrewAI imports
from crewai import Agent, Task, Crew

# Local imports
try:
    from .crewai_config import CrewAIConfig, is_crewai_available
    from .story_generator import StoryGenerator  # Fallback to existing generator
except ImportError:
    # Fallback to absolute imports when running as script
    from crewai_config import CrewAIConfig, is_crewai_available
    from story_generator import StoryGenerator

logger = logging.getLogger(__name__)

class CrewAIStoryGenerator:
    """9-Agent multi-agent story generation using CrewAI framework"""
    
    def __init__(self, api_key: str, superprompt_path: Path):
        self.api_key = api_key
        self.superprompt_path = superprompt_path
        
        # Initialize CrewAI configuration
        self.config = CrewAIConfig(api_key=api_key)
        
        # Fallback to existing StoryGenerator if CrewAI not available
        self.fallback_generator = None
        if not self.config.is_enabled() or not is_crewai_available():
            logger.warning("CrewAI not available, using fallback StoryGenerator")
            self.fallback_generator = StoryGenerator(api_key, superprompt_path)
        
        # Load SuperPrompt content for agent instructions
        self.superprompt = self.config.load_superprompt(superprompt_path)
        self.optimized_superprompt = self._load_optimized_superprompt()
        
        # Initialize the 9 specialized agents
        self.agents = self._create_specialized_agents()
        self.tools = self.config.get_story_generation_tools()
        
        logger.info(f"🤖 CrewAI StoryGenerator initialized with {len(self.agents)} specialized agents")
    
    def _load_optimized_superprompt(self) -> str:
        """Load the optimized SuperPrompt for enhanced instructions"""
        try:
            optimized_path = self.superprompt_path.parent / "SuperPrompt_Optimized.md"
            if optimized_path.exists():
                with open(optimized_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info(f"Optimized SuperPrompt loaded: {len(content)} characters")
                return content
            else:
                logger.info("Using standard SuperPrompt (optimized version not found)")
                return self.superprompt
        except Exception as e:
            logger.warning(f"Failed to load optimized SuperPrompt: {str(e)}")
            return self.superprompt
    
    def _create_specialized_agents(self) -> Dict[str, Agent]:
        """Create the 9 specialized agents based on the agentic workflow architecture"""
        if not self.config.is_enabled():
            return {}
        
        try:
            agent_config = self.config.get_agent_config()
            tools = self.config.get_story_generation_tools()
            
            agents = {
                # AGENT 1: Content Analyst Agent
                'content_analyst': Agent(
                    role='Content Analyst Agent',
                    goal='Extract core insights and structure the foundation for educational stories',
                    backstory="""You are a brilliant content strategist with the analytical mind of a McKinsey consultant
                    and the pattern recognition abilities of a chess grandmaster. You see the hidden structures in complex
                    information and can distill chaos into clarity. Your mission is to extract the core insights from
                    podcast transcripts and structure the foundational learning framework for InvestingDojo stories.""",
                    tools=tools,
                    **agent_config
                ),
                
                # AGENT 2: Creative Writer Agent
                'creative_writer': Agent(
                    role='Creative Writer Agent',
                    goal='Craft engaging narrative with British wit and storytelling excellence',
                    backstory="""You are an incredible creative writer who is obsessed with making facts fun and practical.
                    You have the storytelling genius of Malcolm Gladwell, the narrative drive of a thriller novelist, and an
                    uncanny ability to make complex financial concepts feel like exciting adventures. Every sentence must earn
                    its place. You use British spelling throughout and craft compelling titles in sentence case.""",
                    tools=tools,
                    **agent_config
                ),
                
                # AGENT 3: Financial Expert Agent
                'financial_expert': Agent(
                    role='Financial Expert Agent',
                    goal='Ensure technical accuracy and provide investment wisdom',
                    backstory="""You are an astonishingly adept financial expert specialising in advising people how to be
                    smarter in making financial decisions. You have the analytical rigour of Warren Buffett, the practical
                    wisdom of Peter Lynch, and the teaching ability of a master educator. You never sacrifice accuracy for
                    entertainment and ensure all financial claims are validated with proper disclaimers.""",
                    tools=tools,
                    **agent_config
                ),
                
                # AGENT 4: Comedy Expert Agent
                'comedy_expert': Agent(
                    role='Comedy Expert Agent',
                    goal='Add strategic humor while preserving educational value',
                    backstory="""You are a comedy expert and there is nothing you love more than to take a story and develop
                    it into a hilarious romp like Jerry Seinfeld while retaining the core mission. You love to find deadpan
                    visual metaphors that you craft through words. You make people laugh while they learn, but never at the
                    expense of the lesson. Every joke must serve the learning mission.""",
                    tools=tools,
                    **agent_config
                ),
                
                # AGENT 5: Family Wealth Strategist Agent
                'family_wealth_strategist': Agent(
                    role='Family Wealth Strategist Agent',
                    goal='Focus on generational wealth building and family financial security',
                    backstory="""You are a generational wealth strategist who thinks in decades and centuries. You understand
                    that every financial decision impacts not just the individual, but their children, grandchildren, and
                    great-grandchildren. You are passionate about building family financial security and teaching money wisdom
                    across generations. Every story must serve the mission of building lasting family wealth.""",
                    tools=tools,
                    **agent_config
                ),
                
                # AGENT 6: AI Integration Specialist Agent
                'ai_integration_specialist': Agent(
                    role='AI Integration Specialist Agent',
                    goal='Identify AI enhancement opportunities and practical implementations',
                    backstory="""You are the ex-editor of The Economist and your lifelong mission is to help people better
                    understand the world through money and the markets, but you're also a cutting-edge AI researcher who sees
                    the transformative potential of artificial intelligence in investing. You bridge traditional wisdom with
                    technological innovation and identify specific AI applications for every investment strategy.""",
                    tools=tools,
                    **agent_config
                ),
                
                # AGENT 7: Multi-Platform Optimizer Agent
                'multi_platform_optimizer': Agent(
                    role='Multi-Platform Optimizer Agent',
                    goal='Adapt content for all platforms and maximize cross-channel engagement',
                    backstory="""You are a digital marketing genius who understands how content flows across platforms. You
                    think like a Netflix content strategist, a podcast producer, a newsletter editor, and a mobile app designer
                    all at once. You know how to make content work everywhere while maintaining its core value. You optimize
                    for newsletter, podcast, app, community, and events simultaneously.""",
                    tools=tools,
                    **agent_config
                ),
                
                # AGENT 8: Database Architect Agent
                'database_architect': Agent(
                    role='Database Architect Agent',
                    goal='Ensure perfect JSON schema compliance and database optimization',
                    backstory="""You are a database architect's dream - someone who understands that beautiful content means
                    nothing if it can't be properly stored, retrieved, and connected. You think in relationships, constraints,
                    and data integrity while never losing sight of the human experience the data serves. You ensure all ENUM
                    fields match database constraints exactly and populate previously empty fields with meaningful content.""",
                    tools=tools,
                    **agent_config
                ),
                
                # AGENT 9: Quality Assurance Agent
                'quality_assurance': Agent(
                    role='Quality Assurance Agent',
                    goal='Final validation and optimization of all content dimensions',
                    backstory="""You are the final guardian of quality - meticulous, thorough, and uncompromising. You have
                    the attention to detail of a Swiss watchmaker and the quality standards of a Michelin-starred chef. Nothing
                    gets past you that isn't absolutely perfect. You validate curriculum alignment, multi-platform readiness,
                    database compatibility, and educational disclaimers with unwavering precision.""",
                    tools=tools,
                    **agent_config
                )
            }
            
            logger.info(f"✅ Created {len(agents)} specialized CrewAI agents")
            return agents
            
        except Exception as e:
            logger.error(f"❌ Failed to create specialized agents: {str(e)}")
            return {}
    
    def _create_sequential_tasks(self, transcript: str, episode_metadata: Dict[str, Any]) -> List[Task]:
        """Create the 9-agent sequential task workflow with proper data handoffs"""
        task_config = self.config.get_task_config()
        
        # Truncate transcript for token limits while preserving key content
        transcript_preview = transcript[:6000] if len(transcript) > 6000 else transcript
        
        tasks = [
            # PHASE 1: Foundation Analysis (Content Analyst Agent)
            Task(
                description=f"""
                PHASE 1: FOUNDATION ANALYSIS
                
                You are a brilliant content strategist analyzing podcast transcript content for InvestingDojo.
                Your mission is to extract the core insights and structure the foundation for an engaging educational story.
                
                TRANSCRIPT TO ANALYZE:
                Podcast: {episode_metadata.get('podcast_title', 'Unknown')}
                Episode: {episode_metadata.get('episode_title', 'Unknown')}
                Published: {episode_metadata.get('published_date', 'Unknown')}
                
                {transcript_preview}
                
                ANALYZE AND PROVIDE:
                1. Core insight or strategy being discussed
                2. Belt level appropriateness (white through black)
                3. Curriculum category alignment
                4. Content type classification
                5. Key learning objectives (3-5 specific outcomes)
                6. Difficulty level and complexity assessment
                7. Knowledge graph relationships
                8. Prerequisites and follow-up content suggestions
                
                OUTPUT FORMAT: Structured analysis with clear categorization and learning framework.
                Focus on extracting 2-3 distinct investment insights that can become separate stories.
                """,
                agent=self.agents['content_analyst'],
                expected_output="Structured foundation analysis with 2-3 core insights, belt levels, and learning framework",
                **task_config
            ),
            
            # PHASE 2: Narrative Creation (Creative Writer Agent)
            Task(
                description="""
                PHASE 2: NARRATIVE CREATION
                
                You are an incredible creative writer transforming financial insights into compelling stories.
                Using the foundation analysis provided, craft engaging narratives that make complex concepts accessible and exciting.
                
                CREATE FOR EACH INSIGHT:
                1. Compelling title (sentence case, British spelling)
                2. Hook-driven summary (2-3 explosive sentences)
                3. Full narrative content with story arc
                4. Strong opening that grabs attention
                5. Clear progression from problem to solution
                6. Satisfying conclusion with call to action
                
                STYLE: Energetic, educational, entertaining. Think Malcolm Gladwell meets Jim Cramer with British wit.
                Use British spelling throughout and ensure titles are in sentence case.
                
                OUTPUT: 2-3 complete story drafts with compelling narratives and strong educational value.
                """,
                agent=self.agents['creative_writer'],
                expected_output="2-3 complete story drafts with compelling narratives, British spelling, and educational value",
                **task_config
            ),
            
            # PHASE 3: Financial Validation (Financial Expert Agent)
            Task(
                description="""
                PHASE 3: FINANCIAL VALIDATION
                
                You are a financial expert ensuring accuracy and educational value. Review the creative content
                and enhance it with technical depth while maintaining accessibility.
                
                ENHANCE EACH STORY WITH:
                1. Technical accuracy validation
                2. Risk assessments and warnings
                3. Contrarian viewpoints
                4. Actionable implementation steps
                5. Success metrics and measurement
                6. Appropriate financial disclaimers
                7. Expert credibility assessment
                
                ENSURE: All claims are accurate, risks are disclosed, and practical guidance is sound.
                Add specific actionable practices and implementation checklists.
                
                OUTPUT: Technically validated stories with enhanced practical guidance and proper disclaimers.
                """,
                agent=self.agents['financial_expert'],
                expected_output="Technically validated stories with actionable practices, risk warnings, and financial disclaimers",
                **task_config
            ),
            
            # PHASE 4: Entertainment Enhancement (Comedy Expert Agent)
            Task(
                description="""
                PHASE 4: ENTERTAINMENT ENHANCEMENT
                
                You are a comedy expert adding humor and memorable moments while preserving educational value.
                Your mission is to make learning fun without sacrificing the lesson.
                
                ADD TO EACH STORY:
                1. Strategic humor that reinforces learning
                2. Memorable analogies and metaphors
                3. Visual imagery through words
                4. Comedic timing in written form
                5. Entertaining examples that illustrate points
                6. Deadpan observations about market behavior
                
                BALANCE: Entertainment with respect for serious financial topics. Every joke must serve the mission.
                Make the content more engaging while maintaining educational integrity.
                
                OUTPUT: Enhanced stories with strategic humor, memorable analogies, and entertaining elements.
                """,
                agent=self.agents['comedy_expert'],
                expected_output="Enhanced stories with strategic humor, memorable analogies, and entertaining elements that reinforce learning",
                **task_config
            ),
            
            # PHASE 5: Family Focus (Family Wealth Strategist Agent)
            Task(
                description="""
                PHASE 5: FAMILY WEALTH FOCUS
                
                You are a generational wealth strategist ensuring every story serves family financial security.
                Transform the content to emphasize multi-generational wealth building and family education.
                
                DEVELOP FOR EACH STORY:
                1. Family security relevance and benefits
                2. Generational wealth building potential
                3. Age-appropriate educational angles (5-10, 11-16, 17+)
                4. Family discussion points and activities
                5. Emergency fund and risk considerations
                6. Teaching opportunities for parents
                7. Multi-generational learning elements
                
                FOCUS: How this builds lasting family wealth and can be taught across generations.
                Ensure every story serves the mission of family financial security.
                
                OUTPUT: Family-focused stories with generational wealth building and multi-age educational elements.
                """,
                agent=self.agents['family_wealth_strategist'],
                expected_output="Family-focused stories with generational wealth building, age-appropriate education, and family discussion points",
                **task_config
            ),
            
            # PHASE 6: AI Integration (AI Integration Specialist Agent)
            Task(
                description="""
                PHASE 6: AI INTEGRATION
                
                You are an AI integration specialist identifying how artificial intelligence can enhance every investment strategy.
                Add practical AI applications that make investors more effective.
                
                INTEGRATE FOR EACH STORY:
                1. Specific AI tools and applications
                2. Example prompts and use cases
                3. Implementation steps and difficulty levels
                4. ROI potential and time savings
                5. Limitations and pitfalls to avoid
                6. Free vs. paid tool recommendations
                7. Traditional vs. AI-augmented comparisons
                
                PROVIDE: Practical, actionable AI enhancement that families can implement immediately.
                Focus on tools like ChatGPT, Claude, Perplexity for investment research.
                
                OUTPUT: AI-enhanced stories with specific tools, prompts, implementation steps, and ROI assessments.
                """,
                agent=self.agents['ai_integration_specialist'],
                expected_output="AI-enhanced stories with specific tools, example prompts, implementation steps, and practical ROI assessments",
                **task_config
            ),
            
            # PHASE 7: Multi-Platform Optimization (Multi-Platform Optimizer Agent)
            Task(
                description="""
                PHASE 7: MULTI-PLATFORM OPTIMIZATION
                
                You are a multi-platform content strategist optimizing for newsletter, podcast, app, community, and events.
                Ensure the content works perfectly across all channels.
                
                OPTIMIZE EACH STORY FOR:
                1. Newsletter: Subject lines, preview text, scannable structure
                2. Podcast: Audio-friendly summaries, discussion prompts, soundbites
                3. App: Interactive elements, progress tracking, gamification
                4. Community: Discussion starters, peer challenges, mentorship
                5. Events: Workshop potential, presentation materials, networking
                6. Social Media: Viral hooks, sharing incentives, engagement triggers
                7. Monetization: Premium teasers, value stacking, urgency creation
                
                CREATE: Comprehensive multi-platform content package with cross-channel synergies.
                
                OUTPUT: Multi-platform optimized stories with specific elements for each channel and engagement triggers.
                """,
                agent=self.agents['multi_platform_optimizer'],
                expected_output="Multi-platform optimized stories with newsletter hooks, podcast elements, app features, and community catalysts",
                **task_config
            ),
            
            # PHASE 8: Database Optimization (Database Architect Agent)
            Task(
                description=f"""
                PHASE 8: DATABASE OPTIMIZATION
                
                You are a database architect ensuring perfect compatibility with the InvestingDojo schema.
                Transform the multi-platform content into the exact JSON structure required.
                
                STRUCTURE INTO JSON WITH:
                1. Exact ENUM field values matching database constraints
                2. Simplified time_required field (single string, not object)
                3. Fully populated previously empty fields
                4. Proper relationship data structures
                5. Complete metadata for all platforms
                6. Validation-ready field formats
                7. Optimized for database performance
                
                CRITICAL ENUM VALUES (use exactly):
                - belt_levels: white-belt|yellow-belt|orange-belt|green-belt|blue-belt|brown-belt|black-belt
                - content_type: curriculum-war-story|ai-breakthrough|systematic-strategy|family-wealth-builder|mastery-technique|mindset-hack|research-method|risk-lesson|epic-curriculum-fail|belt-progression-moment|ai-integration-guide|generational-wealth-wisdom
                - difficulty_level: foundational|intermediate-skill|advanced-mastery
                - time_required: 5-minutes|10-minutes|15-minutes|30-minutes|1-hour|2-hours|ongoing|varies
                
                ENSURE: Perfect database compatibility with zero import errors.
                
                OUTPUT: Complete JSON structure with investing-dojo-stories array and episode_summary.
                """,
                agent=self.agents['database_architect'],
                expected_output="Complete JSON structure with perfect database compatibility and all required fields populated",
                **task_config
            ),
            
            # PHASE 9: Quality Assurance (Quality Assurance Agent)
            Task(
                description="""
                PHASE 9: QUALITY ASSURANCE
                
                You are the final quality guardian ensuring excellence across all dimensions.
                Validate the complete JSON output against all requirements.
                
                VALIDATE:
                1. Curriculum alignment and belt progression value ≥ 8/10
                2. Practical applicability ≥ 8/10
                3. AI integration potential ≥ 6/10
                4. Family security relevance ≥ 7/10
                5. Confidence building ≥ 8/10
                6. Entertainment value ≥ 7/10
                7. Multi-platform readiness ≥ 8/10
                8. Database compatibility = 100%
                9. All required fields populated
                10. Educational disclaimers present
                
                FINAL OUTPUT: Return the complete, validated JSON in the exact format:
                {
                  "investing-dojo-stories": [
                    { ... complete story objects ... }
                  ],
                  "episode_summary": { ... }
                }
                
                ENSURE: Every story meets all quality standards and serves the InvestingDojo mission.
                """,
                agent=self.agents['quality_assurance'],
                expected_output="Final validated JSON with investing-dojo-stories array meeting all quality standards",
                **task_config
            )
        ]
        
        return tasks
    
    def _parse_crew_result_enhanced(self, result: Any, episode_metadata: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Enhanced parsing and validation of CrewAI result with comprehensive error handling"""
        try:
            # Convert result to string if needed
            if hasattr(result, 'raw'):
                result_text = result.raw
            elif hasattr(result, 'content'):
                result_text = result.content
            else:
                result_text = str(result)
            
            logger.debug(f"📄 Raw CrewAI result: {result_text[:500]}...")
            
            # Clean and parse JSON with enhanced validation
            cleaned_result = self._clean_json_response(result_text)
            
            # Save debug information
            self._save_debug_output(result_text, cleaned_result, episode_metadata)
            
            stories_data = json.loads(cleaned_result)
            
            # Extract stories from the expected format with multiple fallback options
            stories = None
            if isinstance(stories_data, dict):
                # Try different possible keys the AI might use
                possible_keys = ['investing-dojo-stories', 'stories', 'newsletter_content', 'content', 'articles']
                
                for key in possible_keys:
                    if key in stories_data:
                        stories = stories_data[key]
                        logger.info(f"✅ Found stories under key: '{key}'")
                        break
                
                if stories is None:
                    logger.warning(f"⚠️ No stories found in expected keys: {possible_keys}")
                    logger.debug(f"Available keys: {list(stories_data.keys())}")
                    return None
            else:
                logger.warning("⚠️ Invalid stories format - expected dict")
                return None
            
            if not isinstance(stories, list):
                logger.warning("⚠️ Invalid stories format - 'stories' should be a list")
                return None
            
            # Enhanced story validation and enhancement
            enhanced_stories = []
            
            for i, story in enumerate(stories):
                try:
                    # Validate required fields
                    if not isinstance(story, dict):
                        logger.warning(f"⚠️ Story {i+1}: Invalid format - should be dict")
                        continue
                    
                    # Check for required fields that match the enhanced importer validation
                    required_fields = ['id', 'title', 'summary', 'full_content', 'content_type']
                    missing_fields = [field for field in required_fields if field not in story]
                    
                    if missing_fields:
                        logger.warning(f"⚠️ Story {i+1}: Missing required fields: {missing_fields}")
                        continue
                    
                    # Validate ENUM fields
                    validation_errors = self._validate_story_enums(story, i+1)
                    if validation_errors:
                        logger.warning(f"⚠️ Story {i+1}: ENUM validation errors: {validation_errors}")
                        # Continue processing but log the issues
                    
                    # Enhance story with episode metadata and generation tracking
                    enhanced_story = {
                        **story,
                        'source_type': 'podcast',
                        'source_podcast': episode_metadata.get('podcast_title', 'Unknown'),
                        'source_episode': episode_metadata.get('episode_title', 'Unknown'),
                        'source_url': episode_metadata.get('episode_url', ''),
                        'published_date': episode_metadata.get('published_date', ''),
                        'processed_date': datetime.now().isoformat(),
                        'ai_generated': True,
                        'generation_method': 'crewai_9_agent_workflow',
                        'agent_workflow_version': '1.0',
                        'quality_score': self._calculate_quality_score(story)
                    }
                    
                    enhanced_stories.append(enhanced_story)
                    logger.info(f"✅ Story {i+1}: '{story.get('title', 'Untitled')}' validated and enhanced")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing story {i+1}: {str(e)}")
                    continue
            
            if enhanced_stories:
                logger.info(f"🎉 Successfully processed {len(enhanced_stories)} out of {len(stories)} stories")
            
            return enhanced_stories
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse CrewAI JSON result: {str(e)}")
            logger.debug(f"Raw result: {result}")
            return None
        except Exception as e:
            logger.error(f"❌ Error parsing CrewAI result: {str(e)}")
            return None
    
    def _validate_story_enums(self, story: Dict[str, Any], story_num: int) -> List[str]:
        """Validate ENUM fields against database constraints"""
        errors = []
        
        # Define valid ENUM values
        valid_enums = {
            'belt_levels': ['white-belt', 'yellow-belt', 'orange-belt', 'green-belt', 'blue-belt', 'brown-belt', 'black-belt'],
            'content_type': ['curriculum-war-story', 'ai-breakthrough', 'systematic-strategy', 'family-wealth-builder',
                           'mastery-technique', 'mindset-hack', 'research-method', 'risk-lesson', 'epic-curriculum-fail',
                           'belt-progression-moment', 'ai-integration-guide', 'generational-wealth-wisdom'],
            'difficulty_level': ['foundational', 'intermediate-skill', 'advanced-mastery'],
            'time_required': ['5-minutes', '10-minutes', '15-minutes', '30-minutes', '1-hour', '2-hours',
                            'ongoing', 'varies', 'immediate', 'quick-read', 'deep-dive']
        }
        
        # Check each ENUM field
        for field, valid_values in valid_enums.items():
            if field in story:
                value = story[field]
                if isinstance(value, list):
                    # For array fields like belt_levels
                    invalid_values = [v for v in value if v not in valid_values]
                    if invalid_values:
                        errors.append(f"{field}: invalid values {invalid_values}")
                elif isinstance(value, str):
                    # For single value fields
                    if value not in valid_values:
                        errors.append(f"{field}: '{value}' not in {valid_values}")
        
        return errors
    
    def _calculate_quality_score(self, story: Dict[str, Any]) -> float:
        """Calculate a quality score for the generated story"""
        score = 0.0
        max_score = 10.0
        
        # Check for required fields (2 points)
        required_fields = ['id', 'title', 'summary', 'full_content', 'content_type']
        if all(field in story and story[field] for field in required_fields):
            score += 2.0
        
        # Check for enhanced fields (2 points)
        enhanced_fields = ['actionable_practices', 'discussion_prompts', 'ai_tools_mentioned']
        present_enhanced = sum(1 for field in enhanced_fields if field in story and story[field])
        score += (present_enhanced / len(enhanced_fields)) * 2.0
        
        # Check content length (2 points)
        if 'full_content' in story:
            content_length = len(story['full_content'])
            if content_length > 1000:
                score += 2.0
            elif content_length > 500:
                score += 1.0
        
        # Check for family focus (2 points)
        family_fields = ['family_security_relevance', 'children_education_angle', 'family_discussion_points']
        present_family = sum(1 for field in family_fields if field in story and story[field])
        score += (present_family / len(family_fields)) * 2.0
        
        # Check for AI integration (2 points)
        if 'ai_tools_mentioned' in story and story['ai_tools_mentioned']:
            score += 2.0
        elif 'ai_integration_potential' in story:
            score += 1.0
        
        return min(score, max_score)
    
    def _save_debug_output(self, raw_result: str, cleaned_result: str, episode_metadata: Dict[str, Any]):
        """Save debug output for analysis"""
        try:
            debug_dir = Path("logs/crewai_debug")
            debug_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = int(time.time())
            episode_id = episode_metadata.get('id', 'unknown')
            
            debug_file = debug_dir / f"crewai_result_{episode_id}_{timestamp}.txt"
            
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"=== CREWAI 9-AGENT WORKFLOW DEBUG OUTPUT ===\n")
                f.write(f"Episode: {episode_metadata.get('episode_title', 'Unknown')}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n\n")
                f.write(f"=== RAW RESULT ===\n{raw_result}\n\n")
                f.write(f"=== CLEANED RESULT ===\n{cleaned_result}\n\n")
                
        except Exception as e:
            logger.debug(f"Failed to save debug output: {str(e)}")
    
    def _log_generation_metrics(self, stories: List[Dict[str, Any]], processing_time: float):
        """Log detailed metrics about the generation process"""
        try:
            total_stories = len(stories)
            avg_quality = sum(story.get('quality_score', 0) for story in stories) / total_stories if total_stories > 0 else 0
            
            # Count content types
            content_types = {}
            belt_levels = {}
            
            for story in stories:
                content_type = story.get('content_type', 'unknown')
                content_types[content_type] = content_types.get(content_type, 0) + 1
                
                story_belts = story.get('belt_levels', [])
                if isinstance(story_belts, list):
                    for belt in story_belts:
                        belt_levels[belt] = belt_levels.get(belt, 0) + 1
            
            logger.info(f"📊 Generation Metrics:")
            logger.info(f"   • Total stories: {total_stories}")
            logger.info(f"   • Processing time: {processing_time:.2f}s")
            logger.info(f"   • Average quality score: {avg_quality:.1f}/10")
            logger.info(f"   • Content types: {content_types}")
            logger.info(f"   • Belt levels: {belt_levels}")
            
        except Exception as e:
            logger.debug(f"Failed to log generation metrics: {str(e)}")
    
    def generate_stories_from_transcript(self, transcript: str, episode_metadata: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Generate stories using CrewAI 9-agent multi-agent workflow with comprehensive error handling"""
        
        # Use fallback if CrewAI not available
        if self.fallback_generator:
            logger.info("🔄 Using fallback StoryGenerator (CrewAI not available)")
            return self.fallback_generator.generate_stories_from_transcript(transcript, episode_metadata)
        
        if not self.config.is_enabled() or not self.agents:
            logger.error("❌ CrewAI not properly configured, falling back to standard generator")
            if not self.fallback_generator:
                self.fallback_generator = StoryGenerator(self.api_key, self.superprompt_path)
            return self.fallback_generator.generate_stories_from_transcript(transcript, episode_metadata)
        
        # Validate required agents are present
        required_agents = [
            'content_analyst', 'creative_writer', 'financial_expert', 'comedy_expert',
            'family_wealth_strategist', 'ai_integration_specialist', 'multi_platform_optimizer',
            'database_architect', 'quality_assurance'
        ]
        
        missing_agents = [agent for agent in required_agents if agent not in self.agents]
        if missing_agents:
            logger.error(f"❌ Missing required agents: {missing_agents}, falling back to standard generator")
            if not self.fallback_generator:
                self.fallback_generator = StoryGenerator(self.api_key, self.superprompt_path)
            return self.fallback_generator.generate_stories_from_transcript(transcript, episode_metadata)
        
        try:
            logger.info(f"🤖 Starting 9-agent CrewAI story generation ({len(transcript)} chars)")
            logger.info(f"📊 Episode: {episode_metadata.get('episode_title', 'Unknown')}")
            start_time = time.time()
            
            # Check rate limits
            if not self.config.check_rate_limits():
                logger.warning("⚠️ Rate limit exceeded, falling back to standard generator")
                if not self.fallback_generator:
                    self.fallback_generator = StoryGenerator(self.api_key, self.superprompt_path)
                return self.fallback_generator.generate_stories_from_transcript(transcript, episode_metadata)
            
            # Create the 9-agent sequential tasks for this transcript
            logger.info("🔧 Creating 9-agent sequential task workflow...")
            tasks = self._create_sequential_tasks(transcript, episode_metadata)
            logger.info(f"✅ Created {len(tasks)} sequential tasks")
            
            # Create and run crew with enhanced monitoring
            crew_config = self.config.get_crew_config()
            crew = Crew(
                agents=list(self.agents.values()),
                tasks=tasks,
                **crew_config
            )
            
            # Execute the crew workflow with progress monitoring
            logger.info("🚀 Executing 9-agent CrewAI workflow...")
            logger.info("📋 Agent sequence: Content Analyst → Creative Writer → Financial Expert → Comedy Expert → Family Strategist → AI Specialist → Platform Optimizer → Database Architect → Quality Assurance")
            
            result = crew.kickoff()
            
            processing_time = time.time() - start_time
            logger.info(f"✅ 9-agent CrewAI workflow completed in {processing_time:.2f}s")
            
            # Parse and validate result with enhanced error handling
            stories = self._parse_crew_result_enhanced(result, episode_metadata)
            
            if stories:
                logger.info(f"🎉 Generated {len(stories)} stories using 9-agent CrewAI workflow")
                self._log_generation_metrics(stories, processing_time)
                return stories
            else:
                logger.error("❌ Failed to parse CrewAI result, falling back to standard generator")
                if not self.fallback_generator:
                    self.fallback_generator = StoryGenerator(self.api_key, self.superprompt_path)
                return self.fallback_generator.generate_stories_from_transcript(transcript, episode_metadata)
                
        except Exception as e:
            logger.error(f"❌ 9-agent CrewAI story generation failed: {str(e)}")
            logger.error(f"📄 Transcript preview: {transcript[:200]}...")
            logger.info("🔄 Falling back to standard StoryGenerator")
            
            # Automatic fallback to existing system
            try:
                if not self.fallback_generator:
                    self.fallback_generator = StoryGenerator(self.api_key, self.superprompt_path)
                return self.fallback_generator.generate_stories_from_transcript(transcript, episode_metadata)
            except Exception as fallback_error:
                logger.error(f"❌ Fallback generator also failed: {str(fallback_error)}")
                return None
    
    def _parse_crew_result(self, result: Any, episode_metadata: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Parse and validate CrewAI result"""
        try:
            # Convert result to string if needed
            if hasattr(result, 'raw'):
                result_text = result.raw
            elif hasattr(result, 'content'):
                result_text = result.content
            else:
                result_text = str(result)
            
            logger.debug(f"Raw CrewAI result: {result_text[:500]}...")
            
            # Clean and parse JSON
            cleaned_result = self._clean_json_response(result_text)
            stories_data = json.loads(cleaned_result)
            
            # Extract stories from the expected format
            if isinstance(stories_data, dict) and 'investing-dojo-stories' in stories_data:
                stories = stories_data['investing-dojo-stories']
            elif isinstance(stories_data, list):
                stories = stories_data
            else:
                logger.error(f"Unexpected result format: {type(stories_data)}")
                return None
            
            # Enhance stories with episode metadata
            enhanced_stories = []
            for story in stories:
                if isinstance(story, dict):
                    enhanced_story = {
                        **story,
                        'source_type': 'podcast',
                        'source_podcast': episode_metadata.get('podcast_title', 'Unknown'),
                        'source_episode': episode_metadata.get('episode_title', 'Unknown'),
                        'source_url': episode_metadata.get('episode_url', ''),
                        'published_date': episode_metadata.get('published_date', ''),
                        'processed_date': datetime.now().isoformat(),
                        'ai_generated': True,
                        'generation_method': 'crewai_multi_agent'
                    }
                    enhanced_stories.append(enhanced_story)
            
            return enhanced_stories
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse CrewAI JSON result: {str(e)}")
            logger.debug(f"Raw result: {result}")
            return None
        except Exception as e:
            logger.error(f"Error parsing CrewAI result: {str(e)}")
            return None
    
    def _clean_json_response(self, response: str) -> str:
        """Clean JSON response from potential markdown formatting"""
        import re
        
        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*$', '', response)
        
        # Remove any leading/trailing whitespace
        response = response.strip()
        
        return response
    
    def transcribe_audio_file(self, audio_path: Path) -> Optional[str]:
        """Transcribe audio file (delegate to fallback or use existing method)"""
        if self.fallback_generator:
            return self.fallback_generator.transcribe_audio_file(audio_path)
        
        # For now, CrewAI doesn't handle audio transcription directly
        # This would need to be implemented with additional tools
        logger.warning("Audio transcription not implemented in CrewAI version")
        return None
    
    def process_episodes_batch(self, episodes: List[Dict[str, Any]], batch_size: int = 3) -> List[Dict[str, Any]]:
        """Process episodes in batches using CrewAI or fallback"""
        
        # Use fallback if CrewAI not available
        if self.fallback_generator:
            logger.info("Using fallback StoryGenerator for batch processing")
            return self.fallback_generator.process_episodes_batch(episodes, batch_size)
        
        logger.info(f"🤖 Processing {len(episodes)} episodes with CrewAI (batch size: {batch_size})")
        
        all_stories = []
        
        # Process in batches
        for i in range(0, len(episodes), batch_size):
            batch = episodes[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(episodes) + batch_size - 1) // batch_size
            
            logger.info(f"🔄 Processing CrewAI batch {batch_num}/{total_batches} ({len(batch)} episodes)")
            
            batch_stories = []
            
            for episode in batch:
                try:
                    # Check if episode has transcript or audio file
                    transcript = episode.get('transcript')
                    if not transcript and episode.get('compressed_filepath'):
                        # Would need to transcribe first
                        audio_path = Path(episode['compressed_filepath'])
                        if audio_path.exists():
                            transcript = self.transcribe_audio_file(audio_path)
                    
                    if not transcript:
                        logger.warning(f"Episode {episode['id']}: No transcript available")
                        continue
                    
                    # Generate stories using CrewAI
                    stories = self.generate_stories_from_transcript(transcript, episode)
                    if stories:
                        # Add episode reference to each story
                        for story in stories:
                            story['episode_id'] = episode['id']
                            story['transcript'] = transcript
                        
                        batch_stories.extend(stories)
                        logger.info(f"✅ Episode {episode['id']}: Generated {len(stories)} stories")
                    else:
                        logger.error(f"❌ Episode {episode['id']}: CrewAI generation failed")
                
                except Exception as e:
                    logger.error(f"❌ Episode {episode['id']}: Processing error - {str(e)}")
                    continue
            
            all_stories.extend(batch_stories)
            logger.info(f"✅ Batch {batch_num} completed: {len(batch_stories)} stories generated")
            
            # Brief pause between batches
            if i + batch_size < len(episodes):
                logger.info("⏸️ Pausing between batches...")
                time.sleep(5)
        
        logger.info(f"🎉 All CrewAI batches completed: {len(all_stories)} total stories generated")
        return all_stories
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status and configuration"""
        return {
            'crewai_enabled': self.config.is_enabled(),
            'crewai_available': is_crewai_available(),
            'using_fallback': self.fallback_generator is not None,
            'agents_created': len(self.agents),
            'environment_info': self.config.get_environment_info()
        }


def create_story_generator(api_key: str, superprompt_path: Path, use_crewai: bool = True) -> Any:
    """Factory function to create appropriate story generator"""
    
    if use_crewai and is_crewai_available():
        logger.info("🤖 Creating CrewAI StoryGenerator")
        return CrewAIStoryGenerator(api_key, superprompt_path)
    else:
        logger.info("📝 Creating standard StoryGenerator")
        return StoryGenerator(api_key, superprompt_path)


if __name__ == "__main__":
    # Test CrewAI story generator
    import os
    
    print("🧪 Testing CrewAI Story Generator")
    print("=" * 40)
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        exit(1)
    
    superprompt_path = Path("automation/SuperPrompt.md")
    if not superprompt_path.exists():
        print("❌ SuperPrompt.md not found")
        exit(1)
    
    try:
        generator = CrewAIStoryGenerator(api_key, superprompt_path)
        status = generator.get_status()
        
        print("✅ CrewAI Story Generator created successfully")
        print(f"📊 Status: {status}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")