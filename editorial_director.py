#!/usr/bin/env python3
"""
EDITORIAL DIRECTOR AGENT
InvestingDojo.co - Content Curation and Editorial Intelligence

This agent acts as the newsroom editor, analyzing all transcripts from the day's automation,
identifying the most incisive, inspiring, and growth-forward content, and orchestrating
the content creation workflow with strategic editorial decisions.

MISSION ALIGNMENT:
- Help 1 million families become financially free
- Publish only the most captivating, trendsetting, thought-leading content
- Create kitchen table conversations about investment strategies
- Build generational wealth through real-life lessons

EDITORIAL STANDARDS:
- Incisive: Cuts through noise to core insights
- Inspiring: Motivates families to take action
- Relevant: Addresses real family financial challenges
- Growth-obsessed: Focuses on wealth building and progress
- Learning-forward: Educational and skill-building
- Exciting: Engages and captivates readers
- Unexpected: Provides fresh perspectives and surprises
- Captivating: Holds attention and drives engagement
- Trendsetting: Identifies and leads market trends
- Thought-leading: Provides expert-level insights

NEWS STORY QUALITY CRITERIA (Industry Standard):
1. Accuracy & Verification (25%) - Factual correctness, sourcing, verification
2. Editorial Independence (20%) - Freedom from external influence, integrity
3. Fairness & Balance (15%) - Multiple perspectives, avoiding bias
4. Relevance & Timeliness (15%) - Public interest, currency, timing
5. Clarity & Accessibility (10%) - Clear communication, appropriate language
6. Entertainment & Engagement (10%) - Compelling narrative, audience interest
7. Impact & Significance (5%) - Democratic contribution, accountability

Created for Epic 8: Agentic AI Content Enhancement Workflow
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import traceback
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class ContentAnalysis:
    """Analysis results for a single transcript"""
    transcript_id: str
    title: str
    source: str
    quality_score: float
    editorial_notes: List[str]
    suggested_angles: List[str]
    belt_level_recommendations: List[str]
    family_engagement_potential: float
    trending_topics: List[str]
    common_threads: List[str]
    urgency_score: float
    viral_potential: float

@dataclass
class EditorialDecision:
    """Editorial decision for content creation"""
    selected_transcripts: List[str]
    content_strategy: str
    suggested_story_angle: str
    target_belt_levels: List[str]
    family_discussion_hooks: List[str]
    learning_objectives: List[str]
    expected_outcomes: List[str]
    priority_level: str
    editorial_rationale: str

class EditorialDirector:
    """
    Editorial Director Agent - The newsroom editor for InvestingDojo
    
    Responsibilities:
    1. Analyze all daily transcripts for editorial quality and potential
    2. Identify common threads and trending themes across content
    3. Curate the best content based on InvestingDojo editorial standards
    4. Orchestrate content creation with strategic editorial decisions
    5. Ensure content serves the mission of helping families become financially free
    """
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        self.api_key = api_key
        self.config = config
        self.setup_logging()
        
        # Professional News Story Quality Criteria (Industry Standard)
        self.quality_criteria = {
            "accuracy_verification": {
                "weight": 0.25,
                "description": "Factual correctness, proper sourcing, verification of claims",
                "indicators": ["Multiple source verification", "Primary source access", "Fact-checking rigor", "Transparent corrections policy"]
            },
            "editorial_independence": {
                "weight": 0.20,
                "description": "Freedom from external influence, conflicts of interest disclosure",
                "indicators": ["No undue external pressure", "Conflict transparency", "Editorial autonomy", "Financial independence"]
            },
            "fairness_balance": {
                "weight": 0.15,
                "description": "Presenting relevant perspectives, right of reply, avoiding bias",
                "indicators": ["Multiple viewpoints", "Right of reply", "Context provided", "Bias mitigation"]
            },
            "relevance_timeliness": {
                "weight": 0.15,
                "description": "Public interest significance, currency of information, timing",
                "indicators": ["Public interest value", "Information currency", "Appropriate timing", "Audience relevance"]
            },
            "clarity_accessibility": {
                "weight": 0.10,
                "description": "Clear communication, appropriate language for audience",
                "indicators": ["Clear writing style", "Logical flow", "Appropriate complexity", "Effective structure"]
            },
            "entertainment_engagement": {
                "weight": 0.10,
                "description": "Ability to capture and maintain audience interest",
                "indicators": ["Compelling narrative", "Appropriate humor", "Reader engagement", "Memorable presentation"]
            },
            "impact_significance": {
                "weight": 0.05,
                "description": "Contribution to public discourse, accountability function",
                "indicators": ["Democratic contribution", "Accountability function", "Public discourse", "Long-term significance"]
            }
        }
        
        # Editorial standards and criteria
        self.editorial_standards = {
            'incisive': 'Cuts through noise to core insights',
            'inspiring': 'Motivates families to take action',
            'relevant': 'Addresses real family financial challenges',
            'growth_obsessed': 'Focuses on wealth building and progress',
            'learning_forward': 'Educational and skill-building',
            'exciting': 'Engages and captivates readers',
            'unexpected': 'Provides fresh perspectives and surprises',
            'captivating': 'Holds attention and drives engagement',
            'trendsetting': 'Identifies and leads market trends',
            'thought_leading': 'Provides expert-level insights'
        }
        
        # Family-centric mission alignment
        self.mission_criteria = {
            'family_financial_freedom': 'Helps families achieve financial independence',
            'kitchen_table_conversations': 'Sparks family discussions about money',
            'generational_wealth': 'Builds long-term family wealth strategies',
            'real_life_lessons': 'Provides practical, actionable insights',
            'critical_thinking': 'Develops financial reasoning skills',
            'collaborative_learning': 'Encourages family learning together'
        }
        
        self.logger.info("🎯 Editorial Director initialized - Ready to curate world-class content")
    
    def setup_logging(self):
        """Setup editorial logging"""
        self.logger = logging.getLogger(f"{__name__}.EditorialDirector")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - EDITORIAL - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def analyze_daily_transcripts(self, transcripts: List[Dict[str, Any]]) -> List[ContentAnalysis]:
        """
        Analyze all transcripts from the day's automation for editorial potential
        
        Args:
            transcripts: List of transcript data with content and metadata
            
        Returns:
            List of ContentAnalysis objects with editorial assessments
        """
        self.logger.info(f"📊 EDITORIAL ANALYSIS: Reviewing {len(transcripts)} transcripts")
        
        analyses = []
        
        for transcript in transcripts:
            try:
                analysis = self._analyze_single_transcript(transcript)
                analyses.append(analysis)
                
                self.logger.info(f"✅ Analyzed: {analysis.title[:50]}... (Score: {analysis.quality_score:.2f})")
                
            except Exception as e:
                self.logger.error(f"❌ Analysis failed for transcript {transcript.get('id', 'Unknown')}: {str(e)}")
                continue
        
        # Sort by quality score descending
        analyses.sort(key=lambda x: x.quality_score, reverse=True)
        
        self.logger.info(f"🎯 EDITORIAL ANALYSIS COMPLETE: {len(analyses)} transcripts analyzed")
        self._log_top_content(analyses[:5])
        
        return analyses
    
    def _analyze_single_transcript(self, transcript: Dict[str, Any]) -> ContentAnalysis:
        """Analyze a single transcript for editorial potential"""
        
        # Extract transcript content and metadata
        content = transcript.get('transcript_text', '')
        title = transcript.get('title', 'Unknown Episode')
        source = transcript.get('source', {})
        
        # Enhanced metadata extraction with multiple fallback strategies
        podcast_title = source.get('podcast_title', 'Unknown Podcast')
        host_name = source.get('host_name', 'Unknown Host')
        episode_title = source.get('episode_title', title)
        
        # Smart title extraction with multiple fallback strategies
        display_title = None
        
        # Strategy 1: Use episode_title if it's meaningful
        if episode_title and episode_title not in ['Unknown Episode', 'Unknown', '']:
            display_title = episode_title
        
        # Strategy 2: Use title if it's meaningful
        elif title and title not in ['Unknown Episode', 'Unknown', '']:
            display_title = title
        
        # Strategy 3: Extract from transcript content (first meaningful sentence)
        elif content and len(content) > 50:
            # Look for episode titles in transcript content
            import re
            # Common patterns for episode titles in transcripts
            title_patterns = [
                r"(?:Episode|Show|Today|This is)\s+[:\-]?\s*([^.\n]{10,80})",
                r"Welcome to\s+([^.\n]{10,80})",
                r"I'm\s+[\w\s]+\s+and\s+(?:today|this is)\s+([^.\n]{10,80})",
                r"^([^.\n]{20,80})\s*[\.\!]"  # First sentence if substantial
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, content[:500], re.IGNORECASE)
                if match:
                    potential_title = match.group(1).strip()
                    if len(potential_title) > 10 and not potential_title.lower().startswith(('the', 'a ', 'an ')):
                        display_title = potential_title[:80]  # Limit length
                        break
        
        # Strategy 4: Use podcast title with date/context
        if not display_title and podcast_title != 'Unknown Podcast':
            today = datetime.now().strftime("%m/%d/%y")
            display_title = f"{podcast_title} {today}"
        
        # Strategy 5: Final fallback
        if not display_title:
            display_title = f"Financial Content Analysis {datetime.now().strftime('%H:%M')}"
        
        # Perform editorial analysis using AI
        analysis_prompt = self._build_analysis_prompt(content, display_title, source)
        analysis_result = self._call_ai_analysis(analysis_prompt)
        
        # Parse AI response into structured analysis
        return self._parse_analysis_result(transcript.get('id', ''), display_title, source, analysis_result)
    
    def _build_analysis_prompt(self, content: str, title: str, source: Dict[str, Any]) -> str:
        """Build AI prompt for transcript analysis"""
        
        return f"""
EDITORIAL DIRECTOR ANALYSIS
InvestingDojo.co - World-Class Content Curation

MISSION: Help 1 million families become financially free through incisive, inspiring, growth-obsessed content that creates kitchen table conversations about investment strategies.

PROFESSIONAL NEWS STORY QUALITY CRITERIA (Industry Standard):
{json.dumps(self.quality_criteria, indent=2)}

EDITORIAL STANDARDS:
{json.dumps(self.editorial_standards, indent=2)}

FAMILY MISSION CRITERIA:
{json.dumps(self.mission_criteria, indent=2)}

TRANSCRIPT TO ANALYZE:
Title: {title}
Source: {source.get('podcast_title', 'Unknown')} - {source.get('host_name', 'Unknown')}
Content: {content[:3000]}...

ANALYSIS REQUIRED:
Use the 7-point professional news story quality criteria to score this content:

1. Quality Score (0-10): Calculate weighted score using the 7 criteria above
   - Accuracy & Verification (25%): Rate factual correctness, sourcing
   - Editorial Independence (20%): Rate freedom from bias, integrity
   - Fairness & Balance (15%): Rate multiple perspectives, context
   - Relevance & Timeliness (15%): Rate public interest, currency
   - Clarity & Accessibility (10%): Rate communication clarity
   - Entertainment & Engagement (10%): Rate audience appeal
   - Impact & Significance (5%): Rate contribution to discourse

2. Editorial Notes: Specific observations about content quality and potential
3. Suggested Angles: How to frame this content for maximum family impact
4. Belt Level Recommendations: Which InvestingDojo belt levels would benefit most
5. Family Engagement Potential (0-10): Likelihood to spark kitchen table conversations
6. Trending Topics: Key themes and topics that are currently relevant
7. Common Threads: Themes that might connect with other content
8. Urgency Score (0-10): How timely and urgent this content is
9. Viral Potential (0-10): Likelihood to be shared and discussed widely

RESPOND IN JSON FORMAT:
{{
    "quality_score": 8.5,
    "quality_breakdown": {{
        "accuracy_verification": 8.0,
        "editorial_independence": 9.0,
        "fairness_balance": 8.5,
        "relevance_timeliness": 9.0,
        "clarity_accessibility": 8.0,
        "entertainment_engagement": 7.5,
        "impact_significance": 8.0
    }},
    "editorial_notes": ["Provides actionable insights", "Strong family relevance"],
    "suggested_angles": ["Family emergency fund strategy", "Teaching kids about inflation"],
    "belt_level_recommendations": ["White Belt", "Yellow Belt"],
    "family_engagement_potential": 9.2,
    "trending_topics": ["inflation", "emergency funds", "family budgeting"],
    "common_threads": ["financial security", "family planning"],
    "urgency_score": 7.8,
    "viral_potential": 8.1
}}
"""
    
    def _call_ai_analysis(self, prompt: str) -> Dict[str, Any]:
        """Call AI service for content analysis with rate limiting and retry logic"""
        try:
            # Import Gemini AI here to avoid circular imports
            import google.generativeai as genai
            import time
            
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Rate limiting: Wait between requests to avoid 429 errors
            time.sleep(2)  # 2 second delay between requests
            
            response = model.generate_content(prompt)
            
            # Parse JSON response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            return json.loads(response_text)
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"AI analysis failed: {error_msg}")
            
            # Handle rate limiting specifically
            if "429" in error_msg or "quota" in error_msg.lower():
                self.logger.warning("⚠️ Rate limit hit - using fallback analysis")
                # Wait longer for rate limit recovery
                time.sleep(30)
            
            # Return default analysis with professional scoring breakdown
            return {
                "quality_score": 5.0,
                "quality_breakdown": {
                    "accuracy_verification": 5.0,
                    "editorial_independence": 5.0,
                    "fairness_balance": 5.0,
                    "relevance_timeliness": 5.0,
                    "clarity_accessibility": 5.0,
                    "entertainment_engagement": 5.0,
                    "impact_significance": 5.0
                },
                "editorial_notes": ["Analysis failed - manual review required"],
                "suggested_angles": ["General financial education"],
                "belt_level_recommendations": ["White Belt"],
                "family_engagement_potential": 5.0,
                "trending_topics": ["financial education"],
                "common_threads": ["learning"],
                "urgency_score": 5.0,
                "viral_potential": 5.0
            }
    
    def _parse_analysis_result(self, transcript_id: str, title: str, source: Dict[str, Any], 
                             analysis_result: Dict[str, Any]) -> ContentAnalysis:
        """Parse AI analysis result into ContentAnalysis object"""
        
        return ContentAnalysis(
            transcript_id=transcript_id,
            title=title,
            source=source.get('podcast_title', 'Unknown'),
            quality_score=float(analysis_result.get('quality_score', 5.0)),  # ENSURE FLOAT
            editorial_notes=analysis_result.get('editorial_notes', []),
            suggested_angles=analysis_result.get('suggested_angles', []),
            belt_level_recommendations=analysis_result.get('belt_level_recommendations', []),
            family_engagement_potential=float(analysis_result.get('family_engagement_potential', 5.0)),  # ENSURE FLOAT
            trending_topics=analysis_result.get('trending_topics', []),
            common_threads=analysis_result.get('common_threads', []),
            urgency_score=float(analysis_result.get('urgency_score', 5.0)),  # ENSURE FLOAT
            viral_potential=float(analysis_result.get('viral_potential', 5.0))  # ENSURE FLOAT
        )
    
    def identify_common_threads(self, analyses: List[ContentAnalysis]) -> Dict[str, List[ContentAnalysis]]:
        """Identify common threads and themes across all analyzed content"""
        
        self.logger.info("🔍 IDENTIFYING COMMON THREADS across all content")
        
        # Group content by common themes
        theme_groups = {}
        
        for analysis in analyses:
            for thread in analysis.common_threads:
                if thread not in theme_groups:
                    theme_groups[thread] = []
                theme_groups[thread].append(analysis)
        
        # Sort theme groups by potential impact
        sorted_themes = sorted(theme_groups.items(), 
                             key=lambda x: sum(a.quality_score * a.family_engagement_potential for a in x[1]), 
                             reverse=True)
        
        self.logger.info(f"🎯 IDENTIFIED {len(sorted_themes)} common themes:")
        for theme, content_list in sorted_themes[:5]:
            avg_quality = sum(c.quality_score for c in content_list) / len(content_list)
            self.logger.info(f"  📈 {theme}: {len(content_list)} pieces (Avg Quality: {avg_quality:.2f})")
        
        return dict(sorted_themes)
    
    def make_editorial_decisions(self, analyses: List[ContentAnalysis],
                               theme_groups: Dict[str, List[ContentAnalysis]]) -> List[EditorialDecision]:
        """
        ENHANCED Editorial Director Decision Making
        
        This is the core intelligence of the Editorial Director - making strategic decisions
        that align with InvestingDojo's mission to help 1 million families become financially free.
        
        Key Responsibilities:
        1. Filter content based on family-focused criteria from personas.md
        2. Identify golden threads across transcripts
        3. Orchestrate strategic content creation with specific agent instructions
        4. Ensure content serves White Belt to Brown Belt progression
        """
        
        self.logger.info("🎯 MAKING EDITORIAL DECISIONS - Advanced newsroom strategy session")
        
        decisions = []
        
        # ENHANCED FILTERING: Only proceed with content that meets editorial standards
        high_quality_analyses = [a for a in analyses if float(a.quality_score) >= 7.0]  # Raised threshold with type safety
        family_focused_analyses = [a for a in high_quality_analyses if float(a.family_engagement_potential) >= 7.0]
        
        self.logger.info(f"📊 EDITORIAL FILTERING: {len(analyses)} → {len(high_quality_analyses)} high-quality → {len(family_focused_analyses)} family-focused")
        
        if not family_focused_analyses:
            self.logger.warning("⚠️ No content meets Editorial Director standards - lowering threshold")
            family_focused_analyses = high_quality_analyses[:3] if high_quality_analyses else analyses[:2]
        
        # Strategy 1: GOLDEN THREAD IDENTIFICATION - Combine related transcripts
        golden_threads = self._identify_golden_threads(family_focused_analyses, theme_groups)
        for thread_name, thread_content in golden_threads.items():
            if len(thread_content) >= 2:  # Multiple pieces on same theme
                decision = self._create_golden_thread_decision(thread_name, thread_content)
                decisions.append(decision)
                self.logger.info(f"✅ GOLDEN THREAD: {thread_name} - combining {len(thread_content)} transcripts")
        
        # Strategy 2: PREMIUM INDIVIDUAL CONTENT - Top family-focused pieces
        remaining_analyses = [a for a in family_focused_analyses if not self._is_in_golden_threads(a, golden_threads)]
        for analysis in remaining_analyses[:2]:  # Top 2 individual pieces
            decision = self._create_premium_individual_decision(analysis)
            decisions.append(decision)
            self.logger.info(f"✅ PREMIUM CONTENT: {analysis.title[:50]}... (Quality: {analysis.quality_score:.1f})")
        
        # Strategy 3: URGENT FAMILY RESPONSE - Time-sensitive content
        urgent_content = [a for a in family_focused_analyses if a.urgency_score >= 8.5]
        if urgent_content and not self._is_in_golden_threads(urgent_content[0], golden_threads):
            decision = self._create_urgent_family_response_decision(urgent_content[0])
            decisions.append(decision)
            self.logger.info(f"✅ URGENT RESPONSE: {urgent_content[0].title[:50]}...")
        
        # QUALITY GATE: Ensure we have meaningful content to publish
        if not decisions:
            self.logger.warning("⚠️ No content passed Editorial Director standards - creating fallback content")
            if analyses:
                fallback_decision = self._create_fallback_content_decision(analyses[0])
                decisions.append(fallback_decision)
        
        self.logger.info(f"🎉 EDITORIAL DECISIONS COMPLETE: {len(decisions)} strategic content decisions made")
        
        return decisions
    
    def _create_individual_content_decision(self, analysis: ContentAnalysis) -> EditorialDecision:
        """Create editorial decision for high-quality individual content"""
        
        return EditorialDecision(
            selected_transcripts=[analysis.transcript_id],
            content_strategy="Premium Individual Story",
            suggested_story_angle=analysis.suggested_angles[0] if analysis.suggested_angles else "Financial education focus",
            target_belt_levels=analysis.belt_level_recommendations,
            family_discussion_hooks=[
                f"Family discussion: How does this apply to our financial goals?",
                f"Kitchen table question: What would we do in this situation?",
                f"Learning moment: How can we teach this to our kids?"
            ],
            learning_objectives=[
                "Understand key financial concept",
                "Apply insight to family situation",
                "Develop critical thinking about money"
            ],
            expected_outcomes=[
                "Increased family financial awareness",
                "Actionable steps toward financial freedom",
                "Enhanced investment knowledge"
            ],
            priority_level="HIGH",
            editorial_rationale=f"High-quality content (Score: {analysis.quality_score:.2f}) with strong family engagement potential ({analysis.family_engagement_potential:.2f}). {analysis.editorial_notes[0] if analysis.editorial_notes else 'Meets editorial standards.'}"
        )
    
    def _create_thematic_content_decision(self, theme: str, content_list: List[ContentAnalysis]) -> EditorialDecision:
        """Create editorial decision for thematic content cluster"""
        
        avg_quality = sum(c.quality_score for c in content_list) / len(content_list)
        transcript_ids = [c.transcript_id for c in content_list]
        
        # Combine belt level recommendations
        all_belt_levels = []
        for content in content_list:
            all_belt_levels.extend(content.belt_level_recommendations)
        unique_belt_levels = list(set(all_belt_levels))
        
        return EditorialDecision(
            selected_transcripts=transcript_ids,
            content_strategy="Thematic Content Series",
            suggested_story_angle=f"Comprehensive guide to {theme} for families",
            target_belt_levels=unique_belt_levels,
            family_discussion_hooks=[
                f"Family series: Mastering {theme} together",
                f"Weekly family challenge: Implementing {theme} strategies",
                f"Parent-child learning: Understanding {theme} at every age"
            ],
            learning_objectives=[
                f"Master {theme} concepts and applications",
                "Build family expertise in this area",
                "Create actionable family plan"
            ],
            expected_outcomes=[
                f"Family becomes proficient in {theme}",
                "Measurable progress toward financial goals",
                "Increased confidence in financial decisions"
            ],
            priority_level="MEDIUM",
            editorial_rationale=f"Strong thematic content cluster with {len(content_list)} pieces (Avg Quality: {avg_quality:.2f}). Theme '{theme}' shows high family relevance and learning potential."
        )
    
    def _create_urgent_content_decision(self, analysis: ContentAnalysis) -> EditorialDecision:
        """Create editorial decision for urgent/trending content"""
        
        return EditorialDecision(
            selected_transcripts=[analysis.transcript_id],
            content_strategy="Urgent Market Response",
            suggested_story_angle=f"Timely family response to: {analysis.title}",
            target_belt_levels=analysis.belt_level_recommendations,
            family_discussion_hooks=[
                "Breaking: How does this affect our family finances?",
                "Urgent family meeting: What should we do now?",
                "Market update: Teaching moment for the kids"
            ],
            learning_objectives=[
                "Understand current market situation",
                "Make informed family financial decisions",
                "Learn from real-time market events"
            ],
            expected_outcomes=[
                "Timely family financial response",
                "Increased market awareness",
                "Better preparation for future events"
            ],
            priority_level="URGENT",
            editorial_rationale=f"High urgency content (Score: {analysis.urgency_score:.2f}) requiring immediate family attention. Quality score: {analysis.quality_score:.2f}."
        )
    
    def orchestrate_content_creation(self, decisions: List[EditorialDecision]) -> List[Dict[str, Any]]:
        """
        Orchestrate the content creation workflow based on editorial decisions
        
        This method delegates to the content creation agents with strategic guidance
        """
        
        self.logger.info("🎬 ORCHESTRATING CONTENT CREATION - Editorial direction to writers")
        
        content_briefs = []
        
        for i, decision in enumerate(decisions, 1):
            brief = {
                'editorial_decision_id': f"ED_{datetime.now().strftime('%Y%m%d')}_{i:02d}",
                'priority_level': decision.priority_level,
                'content_strategy': decision.content_strategy,
                'selected_transcripts': decision.selected_transcripts,
                'editorial_brief': {
                    'story_angle': decision.suggested_story_angle,
                    'target_belt_levels': decision.target_belt_levels,
                    'family_discussion_hooks': decision.family_discussion_hooks,
                    'learning_objectives': decision.learning_objectives,
                    'expected_outcomes': decision.expected_outcomes,
                    'editorial_rationale': decision.editorial_rationale
                },
                'quality_requirements': {
                    'editorial_standards': self.editorial_standards,
                    'mission_alignment': self.mission_criteria,
                    'family_focus': True,
                    'kitchen_table_ready': True
                },
                'creation_timestamp': datetime.now().isoformat(),
                'editorial_director_notes': f"Content curated for maximum family impact. {decision.editorial_rationale}"
            }
            
            content_briefs.append(brief)
            
            self.logger.info(f"📝 BRIEF {i}: {decision.content_strategy} - {decision.priority_level} priority")
            self.logger.info(f"   📋 Angle: {decision.suggested_story_angle}")
            self.logger.info(f"   🎯 Belts: {', '.join(decision.target_belt_levels)}")
        
        self.logger.info(f"🎉 CONTENT ORCHESTRATION COMPLETE: {len(content_briefs)} editorial briefs created")
        
        return content_briefs
    
    def _log_top_content(self, top_analyses: List[ContentAnalysis]):
        """Log the top content pieces for editorial review"""
        
        self.logger.info("🏆 TOP CONTENT IDENTIFIED:")
        for i, analysis in enumerate(top_analyses, 1):
            self.logger.info(f"  {i}. {analysis.title[:60]}...")
            self.logger.info(f"     📊 Quality: {analysis.quality_score:.2f} | Family: {analysis.family_engagement_potential:.2f} | Viral: {analysis.viral_potential:.2f}")
            self.logger.info(f"     🎯 Angles: {', '.join(analysis.suggested_angles[:2])}")
            self.logger.info(f"     📈 Topics: {', '.join(analysis.trending_topics[:3])}")
    
    def generate_editorial_report(self, analyses: List[ContentAnalysis], 
                                decisions: List[EditorialDecision]) -> Dict[str, Any]:
        """Generate comprehensive editorial report for the day"""
        
        report = {
            'editorial_session': {
                'date': datetime.now().isoformat(),
                'transcripts_analyzed': len(analyses),
                'editorial_decisions_made': len(decisions),
                'editorial_director': 'InvestingDojo Editorial AI'
            },
            'content_quality_overview': {
                'average_quality_score': sum(a.quality_score for a in analyses) / len(analyses) if analyses else 0,
                'high_quality_content_count': len([a for a in analyses if a.quality_score >= 8.0]),
                'family_engagement_average': sum(a.family_engagement_potential for a in analyses) / len(analyses) if analyses else 0,
                'viral_potential_average': sum(a.viral_potential for a in analyses) / len(analyses) if analyses else 0
            },
            'editorial_decisions_summary': [
                {
                    'strategy': d.content_strategy,
                    'priority': d.priority_level,
                    'story_angle': d.suggested_story_angle,
                    'belt_levels': d.target_belt_levels,
                    'rationale': d.editorial_rationale
                }
                for d in decisions
            ],
            'trending_themes': self._extract_trending_themes(analyses),
            'editorial_recommendations': self._generate_editorial_recommendations(analyses, decisions)
        }
        
        return report
    
    def _extract_trending_themes(self, analyses: List[ContentAnalysis]) -> List[Dict[str, Any]]:
        """Extract trending themes from all analyses"""
        
        theme_counts = {}
        for analysis in analyses:
            for topic in analysis.trending_topics:
                if topic not in theme_counts:
                    theme_counts[topic] = {'count': 0, 'total_quality': 0}
                theme_counts[topic]['count'] += 1
                theme_counts[topic]['total_quality'] += analysis.quality_score
        
        trending = []
        for theme, data in theme_counts.items():
            if data['count'] >= 2:  # Only themes appearing in multiple pieces
                trending.append({
                    'theme': theme,
                    'frequency': data['count'],
                    'average_quality': data['total_quality'] / data['count']
                })
        
        return sorted(trending, key=lambda x: x['frequency'] * x['average_quality'], reverse=True)
    
    def _generate_editorial_recommendations(self, analyses: List[ContentAnalysis], 
                                          decisions: List[EditorialDecision]) -> List[str]:
        """Generate editorial recommendations for future content strategy"""
        
        recommendations = []
        
        # Quality recommendations
        high_quality_count = len([a for a in analyses if a.quality_score >= 8.0])
        if len(analyses) > 0 and high_quality_count / len(analyses) < 0.3:
            recommendations.append("Consider raising content quality standards - less than 30% of content meets premium threshold")
        
        # Family engagement recommendations
        if len(analyses) > 0:
            avg_family_engagement = sum(a.family_engagement_potential for a in analyses) / len(analyses)
            if avg_family_engagement < 7.0:
                recommendations.append("Focus on family-centric angles - current content may not be engaging families effectively")
        
        # Content strategy recommendations
        urgent_decisions = len([d for d in decisions if d.priority_level == "URGENT"])
        if urgent_decisions == 0:
            recommendations.append("Consider adding more timely, market-responsive content to stay current")
        
        # Belt level coverage
        all_belt_levels = []
        for decision in decisions:
            all_belt_levels.extend(decision.target_belt_levels)
        
        if "White Belt" not in all_belt_levels:
            recommendations.append("Ensure beginner-friendly content for new families joining InvestingDojo")
        
        return recommendations
    
    def _identify_golden_threads(self, analyses: List[ContentAnalysis],
                               theme_groups: Dict[str, List[ContentAnalysis]]) -> Dict[str, List[ContentAnalysis]]:
        """Identify golden threads - related content that should be combined"""
        golden_threads = {}
        
        # Look for themes with multiple high-quality pieces
        for theme, content_list in theme_groups.items():
            if len(content_list) >= 2:
                avg_quality = sum(c.quality_score for c in content_list) / len(content_list)
                if avg_quality >= 7.0:
                    golden_threads[theme] = content_list
        
        return golden_threads
    
    def _is_in_golden_threads(self, analysis: ContentAnalysis,
                            golden_threads: Dict[str, List[ContentAnalysis]]) -> bool:
        """Check if analysis is already part of a golden thread"""
        for thread_content in golden_threads.values():
            if analysis in thread_content:
                return True
        return False
    
    def _create_golden_thread_decision(self, thread_name: str,
                                     content_list: List[ContentAnalysis]) -> EditorialDecision:
        """Create editorial decision for golden thread content"""
        transcript_ids = [c.transcript_id for c in content_list]
        avg_quality = sum(c.quality_score for c in content_list) / len(content_list)
        
        return EditorialDecision(
            selected_transcripts=transcript_ids,
            content_strategy="Golden Thread Synthesis",
            suggested_story_angle=f"Comprehensive family guide: {thread_name} - combining insights from {len(content_list)} expert sources",
            target_belt_levels=["White Belt", "Yellow Belt", "Green Belt"],
            family_discussion_hooks=[
                f"Family deep-dive: Mastering {thread_name} together",
                f"Multi-source analysis: What {len(content_list)} experts say about {thread_name}",
                f"Strategic family planning: {thread_name} implementation roadmap"
            ],
            learning_objectives=[
                f"Synthesize expert insights on {thread_name}",
                "Compare different approaches and find family-optimal strategy",
                "Create actionable family implementation plan"
            ],
            expected_outcomes=[
                f"Family becomes expert-level in {thread_name}",
                "Confidence to make informed decisions",
                "Clear action steps for immediate implementation"
            ],
            priority_level="HIGH",
            editorial_rationale=f"Golden thread identified: {len(content_list)} high-quality sources (Avg: {avg_quality:.1f}) on critical family topic '{thread_name}'. Synthesis will provide comprehensive, multi-perspective guidance."
        )
    
    def _create_premium_individual_decision(self, analysis: ContentAnalysis) -> EditorialDecision:
        """Create editorial decision for premium individual content"""
        return EditorialDecision(
            selected_transcripts=[analysis.transcript_id],
            content_strategy="Premium Individual Story",
            suggested_story_angle=f"Expert insight: {analysis.suggested_angles[0] if analysis.suggested_angles else 'Financial wisdom for families'}",
            target_belt_levels=analysis.belt_level_recommendations,
            family_discussion_hooks=[
                f"Expert spotlight: Key insights from {analysis.title}",
                f"Family application: How to implement this expert advice",
                f"Discussion starter: What would our family do differently?"
            ],
            learning_objectives=[
                "Understand expert-level financial insight",
                "Adapt professional advice for family context",
                "Build confidence in financial decision-making"
            ],
            expected_outcomes=[
                "Enhanced family financial knowledge",
                "Actionable steps toward financial goals",
                "Increased investment confidence"
            ],
            priority_level="HIGH",
            editorial_rationale=f"Premium content (Quality: {analysis.quality_score:.1f}, Family Engagement: {analysis.family_engagement_potential:.1f}) with strong educational value and family relevance."
        )
    
    def _create_urgent_family_response_decision(self, analysis: ContentAnalysis) -> EditorialDecision:
        """Create editorial decision for urgent family response content"""
        return EditorialDecision(
            selected_transcripts=[analysis.transcript_id],
            content_strategy="Urgent Family Response",
            suggested_story_angle=f"Breaking: Family financial response to {analysis.title}",
            target_belt_levels=["White Belt", "Yellow Belt", "Green Belt"],
            family_discussion_hooks=[
                "Emergency family meeting: How does this affect us?",
                "Immediate action required: What should we do now?",
                "Teaching moment: Explaining current events to kids"
            ],
            learning_objectives=[
                "Understand immediate market/economic implications",
                "Make informed family financial decisions quickly",
                "Learn from real-time financial events"
            ],
            expected_outcomes=[
                "Timely family financial response",
                "Increased market awareness and preparedness",
                "Better family financial resilience"
            ],
            priority_level="URGENT",
            editorial_rationale=f"High urgency content (Urgency: {analysis.urgency_score:.1f}) requiring immediate family attention and response."
        )
    
    def _create_fallback_content_decision(self, analysis: ContentAnalysis) -> EditorialDecision:
        """Create fallback editorial decision when no content meets standards"""
        return EditorialDecision(
            selected_transcripts=[analysis.transcript_id],
            content_strategy="Educational Foundation",
            suggested_story_angle="Building financial literacy foundations for families",
            target_belt_levels=["White Belt"],
            family_discussion_hooks=[
                "Back to basics: Essential financial concepts for families",
                "Foundation building: Core money principles everyone should know",
                "Family learning: Starting your financial education journey"
            ],
            learning_objectives=[
                "Establish fundamental financial concepts",
                "Create foundation for advanced learning",
                "Build family financial vocabulary"
            ],
            expected_outcomes=[
                "Solid financial foundation established",
                "Readiness for more advanced concepts",
                "Increased family financial communication"
            ],
            priority_level="MEDIUM",
            editorial_rationale="Fallback content to ensure consistent publication while maintaining educational value."
        )


def main():
    """Test the Editorial Director agent"""
    
    # Mock configuration
    config = {
        'gemini_api_key': os.getenv('GEMINI_API_KEY'),
        'editorial_standards': 'world_class',
        'family_focus': True
    }
    
    if not config['gemini_api_key']:
        print("❌ GEMINI_API_KEY not found in environment variables")
        return
    
    # Initialize Editorial Director
    director = EditorialDirector(config['gemini_api_key'], config)
    
    # Mock transcript data for testing
    mock_transcripts = [
        {
            'id': 'test_001',
            'title': 'Building Emergency Funds for Families',
            'transcript_text': 'Today we discuss how families can build emergency funds...',
            'source': {
                'podcast_title': 'Family Finance Show',
                'host_name': 'Jane Smith'
            }
        }
    ]
    
    print("🎯 Testing Editorial Director Agent")
    
    # Test analysis
    analyses = director.analyze_daily_transcripts(mock_transcripts)
    print(f"✅ Analyzed {len(analyses)} transcripts")
    
    # Test theme identification
    themes = director.identify_common_threads(analyses)
    print(f"✅ Identified {len(themes)} common themes")
    
    # Test editorial decisions
    decisions = director.make_editorial_decisions(analyses, themes)
    print(f"✅ Made {len(decisions)} editorial decisions")
    
    # Test content orchestration
    briefs = director.orchestrate_content_creation(decisions)
    print(f"✅ Created {len(briefs)} content briefs")
    
    # Generate report
    report = director.generate_editorial_report(analyses, decisions)
    print(f"✅ Generated editorial report")
    
    print("🎉 Editorial Director test complete!")


if __name__ == "__main__":
    main()