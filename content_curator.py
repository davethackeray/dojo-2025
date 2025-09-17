#!/usr/bin/env python3
"""
CONTENT CURATOR
InvestingDojo.co - Manual Content Curation Interface

This module provides a Python script interface for manual content curation.
It allows users to:
1. Submit a list of links with notes
2. Initiate CrewAI Editorial Director workflow
3. Process content through existing automation pipeline

This is Stage 1 of the multi-content ingestion system as described in the task.

Created for Epic 3: Multi-Content Type Ingestion System
Task 3.3: Create content curation and AI processing workflow
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from automation.multi_content_processor import (
    MultiContentProcessor, ContentItem, ContentType, create_content_item
)
from automation.editorial_director import EditorialDirector
from automation.crew_ai_story_generator import CrewAIStoryGenerator
from automation.database_importer import DatabaseImporter

class ContentCurator:
    """
    Manual Content Curation Interface
    
    This class provides the interface for Stage 1 of the multi-content system:
    - Accept list of links and user notes
    - Process through Editorial Director
    - Generate stories via CrewAI workflow
    - Import to database
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup_logging()
        
        # Initialize components
        self.content_processor = MultiContentProcessor(config)
        self.editorial_director = EditorialDirector(
            api_key=config.get('gemini_api_key'),
            config=config
        )
        
        # Initialize CrewAI if available
        try:
            self.crewai_generator = CrewAIStoryGenerator(config)
            self.crewai_available = True
        except Exception as e:
            self.logger.warning(f"CrewAI not available: {str(e)}")
            self.crewai_available = False
        
        # Initialize database importer
        self.database_importer = DatabaseImporter(config)
        
        self.logger.info("🎯 Content Curator initialized - Ready for manual curation")
    
    def setup_logging(self):
        """Setup logging"""
        self.logger = logging.getLogger(f"{__name__}.ContentCurator")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - CURATOR - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def curate_content_batch(self, content_links: List[Dict[str, Any]], 
                           user_notes: str = "") -> Dict[str, Any]:
        """
        Main curation workflow for Stage 1
        
        Args:
            content_links: List of content items with URLs, titles, types
            user_notes: User's notes and considerations
            
        Returns:
            Dictionary with processing results and generated stories
        """
        
        self.logger.info(f"🎬 STARTING CONTENT CURATION BATCH")
        self.logger.info(f"📊 Processing {len(content_links)} content items")
        self.logger.info(f"📝 User notes: {len(user_notes)} characters")
        
        curation_results = {
            'batch_id': f"curation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'input_summary': {
                'content_count': len(content_links),
                'user_notes_length': len(user_notes),
                'content_types': self._analyze_content_types(content_links)
            },
            'processing_stages': {},
            'generated_stories': [],
            'errors': []
        }
        
        try:
            # Stage 1: Process all content items into transcripts
            self.logger.info("📖 STAGE 1: Processing content into transcripts")
            content_items = self._create_content_items(content_links)
            processed_content = self.content_processor.process_content_list(content_items)
            
            curation_results['processing_stages']['content_processing'] = {
                'input_count': len(content_items),
                'processed_count': len(processed_content),
                'success_rate': len(processed_content) / len(content_items) if content_items else 0
            }
            
            if not processed_content:
                raise ValueError("No content could be processed successfully")
            
            # Stage 2: Editorial Director analysis
            self.logger.info("🎯 STAGE 2: Editorial Director analysis")
            editorial_analyses = self._run_editorial_analysis(processed_content, user_notes)
            
            curation_results['processing_stages']['editorial_analysis'] = {
                'analyses_count': len(editorial_analyses),
                'avg_quality_score': sum(a.quality_score for a in editorial_analyses) / len(editorial_analyses) if editorial_analyses else 0,
                'high_quality_count': len([a for a in editorial_analyses if a.quality_score >= 7.0])
            }
            
            # Stage 3: Editorial decisions
            self.logger.info("📋 STAGE 3: Making editorial decisions")
            editorial_decisions = self._make_editorial_decisions(editorial_analyses, user_notes)
            
            curation_results['processing_stages']['editorial_decisions'] = {
                'decisions_count': len(editorial_decisions),
                'priority_breakdown': self._analyze_decision_priorities(editorial_decisions)
            }
            
            # Stage 4: Story generation
            self.logger.info("✍️ STAGE 4: Generating stories")
            generated_stories = self._generate_stories(editorial_decisions, processed_content)
            
            curation_results['generated_stories'] = generated_stories
            curation_results['processing_stages']['story_generation'] = {
                'stories_generated': len(generated_stories),
                'generation_method': 'crewai' if self.crewai_available else 'fallback'
            }
            
            # Stage 5: Database import
            self.logger.info("💾 STAGE 5: Importing to database")
            import_results = self._import_to_database(generated_stories)
            
            curation_results['processing_stages']['database_import'] = import_results
            
            self.logger.info(f"🎉 CURATION COMPLETE: {len(generated_stories)} stories generated")
            
        except Exception as e:
            error_msg = f"Curation failed: {str(e)}"
            self.logger.error(error_msg)
            curation_results['errors'].append(error_msg)
            curation_results['status'] = 'failed'
            return curation_results
        
        curation_results['status'] = 'success'
        return curation_results
    
    def _create_content_items(self, content_links: List[Dict[str, Any]]) -> List[ContentItem]:
        """Convert content links to ContentItem objects"""
        content_items = []
        
        for link_data in content_links:
            try:
                # Extract required fields
                url = link_data.get('url', '')
                title = link_data.get('title', 'Untitled Content')
                content_type = link_data.get('type', 'webpage')
                author = link_data.get('author', '')
                raw_content = link_data.get('content', '')
                
                # Detect content type if not specified
                if content_type == 'auto':
                    content_type = self._detect_content_type(url)
                
                # Create content item
                content_item = create_content_item(
                    content_type=content_type,
                    source_url=url,
                    title=title,
                    author=author,
                    raw_content=raw_content,
                    metadata=link_data.get('metadata', {})
                )
                
                content_items.append(content_item)
                
            except Exception as e:
                self.logger.error(f"Failed to create content item for {link_data}: {str(e)}")
                continue
        
        return content_items
    
    def _detect_content_type(self, url: str) -> str:
        """Auto-detect content type from URL"""
        url_lower = url.lower()
        
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif url_lower.endswith('.pdf'):
            return 'ebook'
        elif url_lower.endswith('.epub'):
            return 'ebook'
        elif url_lower.endswith('.mp3'):
            return 'personal_podcast'
        elif 'newsletter' in url_lower or 'substack' in url_lower:
            return 'newsletter'
        else:
            return 'webpage'
    
    def _run_editorial_analysis(self, processed_content: List, user_notes: str) -> List:
        """Run Editorial Director analysis on processed content"""
        
        # Convert processed content to format expected by Editorial Director
        transcript_data = []
        for content in processed_content:
            transcript_data.append({
                'id': content.content_id,
                'title': content.title,
                'transcript_text': content.transcript,
                'source': content.attribution
            })
        
        # Add user notes as context
        if user_notes:
            # Create a special "user notes" transcript
            user_notes_transcript = {
                'id': f"user_notes_{int(time.time())}",
                'title': "User Curation Notes",
                'transcript_text': f"USER CURATION NOTES:\n\n{user_notes}",
                'source': {
                    'podcast_title': 'User Input',
                    'host_name': 'Content Curator'
                }
            }
            transcript_data.append(user_notes_transcript)
        
        # Run Editorial Director analysis
        return self.editorial_director.analyze_daily_transcripts(transcript_data)
    
    def _make_editorial_decisions(self, analyses: List, user_notes: str) -> List:
        """Make editorial decisions based on analyses"""
        
        # Identify common threads
        theme_groups = self.editorial_director.identify_common_threads(analyses)
        
        # Make editorial decisions
        decisions = self.editorial_director.make_editorial_decisions(analyses, theme_groups)
        
        # Enhance decisions with user notes context
        for decision in decisions:
            if user_notes:
                decision.editorial_rationale += f" User notes considered: {user_notes[:200]}..."
        
        return decisions
    
    def _generate_stories(self, editorial_decisions: List, processed_content: List) -> List[Dict[str, Any]]:
        """Generate stories based on editorial decisions"""
        
        generated_stories = []
        
        for decision in editorial_decisions:
            try:
                # Find relevant content for this decision
                relevant_content = []
                for content in processed_content:
                    if content.content_id in decision.selected_transcripts:
                        relevant_content.append({
                            'transcript_text': content.transcript,
                            'title': content.title,
                            'source': content.attribution
                        })
                
                if not relevant_content:
                    self.logger.warning(f"No content found for decision: {decision.content_strategy}")
                    continue
                
                # Generate story using CrewAI or fallback
                if self.crewai_available:
                    story = self._generate_story_crewai(decision, relevant_content)
                else:
                    story = self._generate_story_fallback(decision, relevant_content)
                
                if story:
                    generated_stories.append(story)
                    self.logger.info(f"✅ Generated story: {story.get('title', 'Untitled')[:50]}...")
                
            except Exception as e:
                self.logger.error(f"Failed to generate story for decision {decision.content_strategy}: {str(e)}")
                continue
        
        return generated_stories
    
    def _generate_story_crewai(self, decision, relevant_content: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Generate story using CrewAI workflow"""
        try:
            # Create editorial brief for CrewAI
            editorial_brief = {
                'content_strategy': decision.content_strategy,
                'story_angle': decision.suggested_story_angle,
                'target_belt_levels': decision.target_belt_levels,
                'family_discussion_hooks': decision.family_discussion_hooks,
                'learning_objectives': decision.learning_objectives,
                'priority_level': decision.priority_level,
                'editorial_rationale': decision.editorial_rationale
            }
            
            # Generate story using CrewAI
            story_result = self.crewai_generator.generate_story_from_transcripts(
                transcripts=relevant_content,
                editorial_brief=editorial_brief
            )
            
            return story_result
            
        except Exception as e:
            self.logger.error(f"CrewAI story generation failed: {str(e)}")
            return None
    
    def _generate_story_fallback(self, decision, relevant_content: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Generate story using fallback method"""
        try:
            # Use traditional story generator as fallback
            from automation.story_generator import StoryGenerator
            
            story_generator = StoryGenerator(self.config)
            
            # Combine content for processing
            combined_transcript = "\n\n".join([
                f"CONTENT: {content['title']}\n{content['transcript_text']}"
                for content in relevant_content
            ])
            
            # Generate story
            story_result = story_generator.generate_story(
                transcript_text=combined_transcript,
                editorial_guidance=decision.editorial_rationale
            )
            
            return story_result
            
        except Exception as e:
            self.logger.error(f"Fallback story generation failed: {str(e)}")
            return None
    
    def _import_to_database(self, stories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Import generated stories to database"""
        try:
            import_results = {
                'attempted': len(stories),
                'successful': 0,
                'failed': 0,
                'errors': []
            }
            
            for story in stories:
                try:
                    # Import story to database
                    result = self.database_importer.import_story(story)
                    
                    if result.get('success', False):
                        import_results['successful'] += 1
                    else:
                        import_results['failed'] += 1
                        import_results['errors'].append(result.get('error', 'Unknown error'))
                        
                except Exception as e:
                    import_results['failed'] += 1
                    import_results['errors'].append(str(e))
            
            return import_results
            
        except Exception as e:
            self.logger.error(f"Database import failed: {str(e)}")
            return {
                'attempted': len(stories),
                'successful': 0,
                'failed': len(stories),
                'errors': [str(e)]
            }
    
    def _analyze_content_types(self, content_links: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of content types"""
        type_counts = {}
        
        for link in content_links:
            content_type = link.get('type', 'webpage')
            if content_type == 'auto':
                content_type = self._detect_content_type(link.get('url', ''))
            
            type_counts[content_type] = type_counts.get(content_type, 0) + 1
        
        return type_counts
    
    def _analyze_decision_priorities(self, decisions: List) -> Dict[str, int]:
        """Analyze priority distribution of editorial decisions"""
        priority_counts = {}
        
        for decision in decisions:
            priority = decision.priority_level
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        return priority_counts

def run_interactive_curation():
    """Interactive command-line interface for content curation"""
    
    print("🎯 INVESTING DOJO CONTENT CURATOR")
    print("=" * 50)
    print("Stage 1: Manual Content Curation Interface")
    print()
    
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable required")
        return
    
    # Initialize curator
    config = {
        'gemini_api_key': api_key,
        'crewai_enabled': os.getenv('CREWAI_ENABLED', 'false').lower() == 'true'
    }
    
    try:
        curator = ContentCurator(config)
        print("✅ Content Curator initialized")
        print()
        
        # Get content links
        print("📝 STEP 1: Enter content links")
        print("Enter content items (one per line, format: URL|Title|Type|Author)")
        print("Types: webpage, youtube, ebook, newsletter, personal_podcast, auto")
        print("Enter empty line when done:")
        print()
        
        content_links = []
        while True:
            line = input("> ").strip()
            if not line:
                break
            
            parts = line.split('|')
            if len(parts) >= 2:
                content_item = {
                    'url': parts[0].strip(),
                    'title': parts[1].strip(),
                    'type': parts[2].strip() if len(parts) > 2 else 'auto',
                    'author': parts[3].strip() if len(parts) > 3 else ''
                }
                content_links.append(content_item)
                print(f"  ✅ Added: {content_item['title']}")
            else:
                print(f"  ❌ Invalid format: {line}")
        
        if not content_links:
            print("❌ No content links provided")
            return
        
        print(f"\n📊 Total content items: {len(content_links)}")
        
        # Get user notes
        print("\n📝 STEP 2: Enter your curation notes")
        print("Describe what you want the AI to focus on, common themes, etc.")
        print("Enter empty line when done:")
        print()
        
        user_notes_lines = []
        while True:
            line = input("> ")
            if not line:
                break
            user_notes_lines.append(line)
        
        user_notes = "\n".join(user_notes_lines)
        print(f"\n📝 User notes: {len(user_notes)} characters")
        
        # Run curation
        print("\n🎬 STEP 3: Running content curation...")
        print("This may take several minutes...")
        print()
        
        results = curator.curate_content_batch(content_links, user_notes)
        
        # Display results
        print("\n🎉 CURATION RESULTS")
        print("=" * 30)
        print(f"Status: {results['status']}")
        print(f"Batch ID: {results['batch_id']}")
        print()
        
        if results['status'] == 'success':
            print("📊 Processing Summary:")
            for stage, data in results['processing_stages'].items():
                print(f"  {stage}: {data}")
            print()
            
            print(f"✍️ Generated Stories: {len(results['generated_stories'])}")
            for i, story in enumerate(results['generated_stories'], 1):
                print(f"  {i}. {story.get('title', 'Untitled')}")
        
        if results['errors']:
            print("\n❌ Errors:")
            for error in results['errors']:
                print(f"  - {error}")
        
        # Save results
        results_file = f"curation_results_{results['batch_id']}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {results_file}")
        
    except Exception as e:
        print(f"❌ Curation failed: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    run_interactive_curation()