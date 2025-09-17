#!/usr/bin/env python3
"""
CREWAI INTEGRATION LAYER
Non-intrusive integration of CrewAI multi-agent system with existing automation
Maintains 100% backward compatibility with COMPLETE_DAILY_AUTOMATION.py

This module provides:
- Factory pattern for story generator selection
- Configuration-driven workflow switching
- Gradual rollout and A/B testing capabilities
- Performance monitoring and quality comparison
- Automatic fallback on any issues
"""

import os
import json
import time
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import traceback

# Import existing components
from story_generator import StoryGenerator

# Import CrewAI components with fallback
try:
    from crew_ai_story_generator import CrewAIStoryGenerator, is_crewai_available
    from crewai_config import CrewAIConfig
    CREWAI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"CrewAI components not available: {str(e)}")
    CREWAI_AVAILABLE = False
    CrewAIStoryGenerator = None
    CrewAIConfig = None

logger = logging.getLogger(__name__)

class StoryGeneratorFactory:
    """Factory for creating appropriate story generator based on configuration"""
    
    @staticmethod
    def create_story_generator(
        api_key: str, 
        superprompt_path: Path,
        config: Optional[Dict[str, Any]] = None
    ) -> Union[StoryGenerator, 'CrewAIStoryGenerator']:
        """
        Create appropriate story generator based on configuration
        
        Args:
            api_key: Gemini API key
            superprompt_path: Path to SuperPrompt.md
            config: Integration configuration
            
        Returns:
            StoryGenerator or CrewAIStoryGenerator instance
        """
        integration_config = IntegrationConfig(config or {})
        
        # Check if CrewAI should be used
        if integration_config.should_use_crewai():
            try:
                if CREWAI_AVAILABLE and CrewAIStoryGenerator:
                    logger.info("🤖 Creating CrewAI StoryGenerator")
                    return CrewAIStoryGenerator(api_key, superprompt_path)
                else:
                    logger.warning("⚠️ CrewAI requested but not available, using standard generator")
            except Exception as e:
                logger.error(f"❌ Failed to create CrewAI generator: {str(e)}")
                logger.info("🔄 Falling back to standard StoryGenerator")
        
        # Default to standard generator
        logger.info("📝 Creating standard StoryGenerator")
        return StoryGenerator(api_key, superprompt_path)


class IntegrationConfig:
    """Configuration manager for CrewAI integration"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.load_environment_config()
        self.setup_logging()
    
    def load_environment_config(self):
        """Load configuration from environment variables"""
        # Primary feature flag
        self.crewai_enabled = os.getenv('CREWAI_ENABLED', 'false').lower() == 'true'
        
        # Rollout percentage (0-100)
        self.rollout_percentage = int(os.getenv('CREWAI_ROLLOUT_PERCENTAGE', '0'))
        
        # A/B testing configuration
        self.ab_testing_enabled = os.getenv('CREWAI_AB_TESTING', 'false').lower() == 'true'
        self.ab_testing_seed = os.getenv('CREWAI_AB_TESTING_SEED', 'investingdojo')
        
        # Quality thresholds for automatic rollback (lowered for realistic expectations)
        self.quality_threshold = float(os.getenv('CREWAI_QUALITY_THRESHOLD', '5.5'))
        self.error_threshold = float(os.getenv('CREWAI_ERROR_THRESHOLD', '15.0'))  # Percentage
        
        # Performance monitoring
        self.monitoring_enabled = os.getenv('CREWAI_MONITORING', 'true').lower() == 'true'
        self.metrics_retention_days = int(os.getenv('CREWAI_METRICS_RETENTION', '30'))
        
        # Fallback configuration
        self.auto_fallback = os.getenv('CREWAI_AUTO_FALLBACK', 'true').lower() == 'true'
        self.fallback_on_timeout = int(os.getenv('CREWAI_FALLBACK_TIMEOUT', '300'))  # 5 minutes
        
        logger.info(f"🔧 Integration config loaded: enabled={self.crewai_enabled}, rollout={self.rollout_percentage}%")
    
    def setup_logging(self):
        """Setup integration-specific logging"""
        if self.monitoring_enabled:
            log_dir = Path("logs/crewai_integration")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Create integration log handler
            log_file = log_dir / f"integration_{datetime.now().strftime('%Y%m%d')}.log"
            handler = logging.FileHandler(log_file, encoding='utf-8')
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            
            integration_logger = logging.getLogger('crewai_integration')
            integration_logger.addHandler(handler)
            integration_logger.setLevel(logging.INFO)
    
    def should_use_crewai(self, episode_id: Optional[str] = None) -> bool:
        """
        Determine if CrewAI should be used for this request
        
        Args:
            episode_id: Optional episode ID for consistent A/B testing
            
        Returns:
            True if CrewAI should be used, False for standard generator
        """
        # Check if CrewAI is enabled
        if not self.crewai_enabled:
            return False
        
        # Check if CrewAI is available
        if not CREWAI_AVAILABLE:
            logger.warning("⚠️ CrewAI enabled but not available")
            return False
        
        # Check rollout percentage
        if self.rollout_percentage <= 0:
            return False
        
        if self.rollout_percentage >= 100:
            return True
        
        # A/B testing logic - consistent selection based on episode ID
        if episode_id and self.ab_testing_enabled:
            # Create deterministic hash for consistent A/B assignment
            hash_input = f"{self.ab_testing_seed}_{episode_id}"
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
            selection_percentage = hash_value % 100
            
            use_crewai = selection_percentage < self.rollout_percentage
            logger.debug(f"A/B testing: episode {episode_id} -> {selection_percentage}% -> {'CrewAI' if use_crewai else 'Standard'}")
            return use_crewai
        
        # Random rollout for requests without episode ID
        import random
        return random.randint(1, 100) <= self.rollout_percentage
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for logging"""
        return {
            'crewai_enabled': self.crewai_enabled,
            'crewai_available': CREWAI_AVAILABLE,
            'rollout_percentage': self.rollout_percentage,
            'ab_testing_enabled': self.ab_testing_enabled,
            'monitoring_enabled': self.monitoring_enabled,
            'auto_fallback': self.auto_fallback,
            'quality_threshold': self.quality_threshold,
            'error_threshold': self.error_threshold
        }


class PerformanceMonitor:
    """Monitor and compare performance between CrewAI and standard generators"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.metrics_dir = Path("logs/crewai_metrics")
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Load historical metrics
        self.metrics_file = self.metrics_dir / "performance_metrics.json"
        self.metrics = self.load_metrics()
    
    def load_metrics(self) -> Dict[str, Any]:
        """Load historical performance metrics"""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    metrics = json.load(f)
                logger.info(f"📊 Loaded {len(metrics.get('sessions', []))} historical metric sessions")
                return metrics
        except Exception as e:
            logger.warning(f"Failed to load metrics: {str(e)}")
        
        return {
            'sessions': [],
            'summary': {
                'crewai': {'count': 0, 'avg_quality': 0, 'avg_time': 0, 'error_rate': 0},
                'standard': {'count': 0, 'avg_quality': 0, 'avg_time': 0, 'error_rate': 0}
            }
        }
    
    def save_metrics(self):
        """Save metrics to file"""
        try:
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(self.metrics, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save metrics: {str(e)}")
    
    def record_session(
        self, 
        generator_type: str, 
        processing_time: float, 
        stories_generated: int,
        quality_scores: List[float],
        error_occurred: bool = False,
        episode_metadata: Dict[str, Any] = None
    ):
        """Record a generation session for performance analysis"""
        if not self.config.monitoring_enabled:
            return
        
        session = {
            'timestamp': datetime.now().isoformat(),
            'generator_type': generator_type,
            'processing_time': processing_time,
            'stories_generated': stories_generated,
            'quality_scores': quality_scores,
            'avg_quality': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'error_occurred': error_occurred,
            'episode_id': episode_metadata.get('id') if episode_metadata else None,
            'episode_title': episode_metadata.get('episode_title') if episode_metadata else None
        }
        
        self.metrics['sessions'].append(session)
        self.update_summary()
        self.save_metrics()
        
        logger.info(f"📊 Recorded {generator_type} session: {stories_generated} stories, {processing_time:.2f}s, avg quality {session['avg_quality']:.1f}")
    
    def update_summary(self):
        """Update performance summary statistics"""
        crewai_sessions = [s for s in self.metrics['sessions'] if s['generator_type'] == 'crewai']
        standard_sessions = [s for s in self.metrics['sessions'] if s['generator_type'] == 'standard']
        
        def calculate_stats(sessions):
            if not sessions:
                return {'count': 0, 'avg_quality': 0, 'avg_time': 0, 'error_rate': 0}
            
            return {
                'count': len(sessions),
                'avg_quality': sum(s['avg_quality'] for s in sessions) / len(sessions),
                'avg_time': sum(s['processing_time'] for s in sessions) / len(sessions),
                'error_rate': (sum(1 for s in sessions if s['error_occurred']) / len(sessions)) * 100
            }
        
        self.metrics['summary'] = {
            'crewai': calculate_stats(crewai_sessions),
            'standard': calculate_stats(standard_sessions),
            'last_updated': datetime.now().isoformat()
        }
    
    def get_performance_comparison(self) -> Dict[str, Any]:
        """Get performance comparison between generators"""
        summary = self.metrics['summary']
        
        comparison = {
            'crewai_sessions': summary['crewai']['count'],
            'standard_sessions': summary['standard']['count'],
            'quality_improvement': 0,
            'time_difference': 0,
            'error_rate_difference': 0,
            'recommendation': 'insufficient_data'
        }
        
        if summary['crewai']['count'] > 0 and summary['standard']['count'] > 0:
            comparison.update({
                'quality_improvement': summary['crewai']['avg_quality'] - summary['standard']['avg_quality'],
                'time_difference': summary['crewai']['avg_time'] - summary['standard']['avg_time'],
                'error_rate_difference': summary['crewai']['error_rate'] - summary['standard']['error_rate']
            })
            
            # Generate recommendation
            if (comparison['quality_improvement'] > 1.0 and 
                comparison['error_rate_difference'] < 5.0):
                comparison['recommendation'] = 'increase_rollout'
            elif (comparison['quality_improvement'] < -1.0 or 
                  comparison['error_rate_difference'] > 10.0):
                comparison['recommendation'] = 'decrease_rollout'
            else:
                comparison['recommendation'] = 'maintain_current'
        
        return comparison
    
    def should_trigger_rollback(self) -> bool:
        """Check if automatic rollback should be triggered"""
        if not self.config.auto_fallback:
            return False
        
        summary = self.metrics['summary']
        crewai_stats = summary.get('crewai', {})
        
        # Check if we have enough data
        if crewai_stats.get('count', 0) < 5:
            return False
        
        # Check quality threshold
        if crewai_stats.get('avg_quality', 0) < self.config.quality_threshold:
            logger.warning(f"⚠️ CrewAI quality below threshold: {crewai_stats['avg_quality']:.1f} < {self.config.quality_threshold}")
            return True
        
        # Check error rate threshold
        if crewai_stats.get('error_rate', 0) > self.config.error_threshold:
            logger.warning(f"⚠️ CrewAI error rate above threshold: {crewai_stats['error_rate']:.1f}% > {self.config.error_threshold}%")
            return True
        
        return False


class IntegratedStoryGenerator:
    """
    Integrated story generator that seamlessly switches between CrewAI and standard generators
    Maintains identical interface to existing StoryGenerator for backward compatibility
    """
    
    def __init__(self, api_key: str, superprompt_path: Path, config: Dict[str, Any] = None):
        self.api_key = api_key
        self.superprompt_path = superprompt_path
        
        # Initialize configuration and monitoring
        self.integration_config = IntegrationConfig(config or {})
        self.performance_monitor = PerformanceMonitor(self.integration_config)
        
        # Create generators
        self.standard_generator = StoryGenerator(api_key, superprompt_path)
        self.crewai_generator = None
        
        # Initialize CrewAI generator if available
        if CREWAI_AVAILABLE and self.integration_config.crewai_enabled:
            try:
                self.crewai_generator = CrewAIStoryGenerator(api_key, superprompt_path)
                logger.info("✅ CrewAI generator initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize CrewAI generator: {str(e)}")
                self.crewai_generator = None
        
        logger.info(f"🔧 IntegratedStoryGenerator initialized: {self.get_status()}")
    
    def _select_generator(self, episode_metadata: Dict[str, Any] = None) -> tuple:
        """
        Select appropriate generator based on configuration and episode
        
        Returns:
            (generator, generator_type)
        """
        episode_id = episode_metadata.get('id') if episode_metadata else None
        
        # Check for automatic rollback
        if self.performance_monitor.should_trigger_rollback():
            logger.warning("🚨 Automatic rollback triggered - using standard generator")
            return self.standard_generator, 'standard'
        
        # Determine if CrewAI should be used
        if (self.crewai_generator and 
            self.integration_config.should_use_crewai(episode_id)):
            logger.info(f"🤖 Selected CrewAI generator for episode {episode_id}")
            return self.crewai_generator, 'crewai'
        else:
            logger.info(f"📝 Selected standard generator for episode {episode_id}")
            return self.standard_generator, 'standard'
    
    def generate_stories_from_transcript(
        self, 
        transcript: str, 
        episode_metadata: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Generate stories from transcript using selected generator
        Maintains identical interface to existing StoryGenerator
        """
        start_time = time.time()
        generator, generator_type = self._select_generator(episode_metadata)
        
        try:
            logger.info(f"🎯 Generating stories using {generator_type} generator")
            logger.info(f"📊 Episode: {episode_metadata.get('episode_title', 'Unknown')}")
            
            # Generate stories
            stories = generator.generate_stories_from_transcript(transcript, episode_metadata)
            processing_time = time.time() - start_time
            
            if stories:
                # Calculate quality scores
                quality_scores = []
                for story in stories:
                    if hasattr(generator, '_calculate_quality_score'):
                        quality_scores.append(generator._calculate_quality_score(story))
                    else:
                        # Basic quality estimation for standard generator
                        quality_scores.append(self._estimate_quality_score(story))
                
                # Record performance metrics
                self.performance_monitor.record_session(
                    generator_type=generator_type,
                    processing_time=processing_time,
                    stories_generated=len(stories),
                    quality_scores=quality_scores,
                    error_occurred=False,
                    episode_metadata=episode_metadata
                )
                
                # Add integration metadata
                for story in stories:
                    story['integration_metadata'] = {
                        'generator_used': generator_type,
                        'processing_time': processing_time,
                        'integration_version': '1.0',
                        'quality_score': quality_scores[stories.index(story)] if quality_scores else 0
                    }
                
                logger.info(f"✅ Generated {len(stories)} stories in {processing_time:.2f}s using {generator_type}")
                return stories
            
            else:
                # Record failed generation
                self.performance_monitor.record_session(
                    generator_type=generator_type,
                    processing_time=processing_time,
                    stories_generated=0,
                    quality_scores=[],
                    error_occurred=True,
                    episode_metadata=episode_metadata
                )
                
                # Try fallback if CrewAI failed
                if generator_type == 'crewai' and self.integration_config.auto_fallback:
                    logger.warning("🔄 CrewAI failed, attempting fallback to standard generator")
                    return self._fallback_generation(transcript, episode_metadata, start_time)
                
                return None
        
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Story generation failed with {generator_type}: {str(e)}")
            
            # Record error
            self.performance_monitor.record_session(
                generator_type=generator_type,
                processing_time=processing_time,
                stories_generated=0,
                quality_scores=[],
                error_occurred=True,
                episode_metadata=episode_metadata
            )
            
            # Try fallback if CrewAI failed
            if generator_type == 'crewai' and self.integration_config.auto_fallback:
                logger.info("🔄 Attempting fallback to standard generator")
                return self._fallback_generation(transcript, episode_metadata, start_time)
            
            return None
    
    def _fallback_generation(
        self, 
        transcript: str, 
        episode_metadata: Dict[str, Any], 
        original_start_time: float
    ) -> Optional[List[Dict[str, Any]]]:
        """Fallback to standard generator when CrewAI fails"""
        try:
            fallback_start = time.time()
            stories = self.standard_generator.generate_stories_from_transcript(transcript, episode_metadata)
            fallback_time = time.time() - fallback_start
            total_time = time.time() - original_start_time
            
            if stories:
                # Calculate quality scores for fallback
                quality_scores = [self._estimate_quality_score(story) for story in stories]
                
                # Record fallback success
                self.performance_monitor.record_session(
                    generator_type='standard_fallback',
                    processing_time=fallback_time,
                    stories_generated=len(stories),
                    quality_scores=quality_scores,
                    error_occurred=False,
                    episode_metadata=episode_metadata
                )
                
                # Add fallback metadata
                for story in stories:
                    story['integration_metadata'] = {
                        'generator_used': 'standard_fallback',
                        'processing_time': fallback_time,
                        'total_time': total_time,
                        'integration_version': '1.0',
                        'fallback_reason': 'crewai_failure'
                    }
                
                logger.info(f"✅ Fallback successful: {len(stories)} stories in {fallback_time:.2f}s")
                return stories
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Fallback generation also failed: {str(e)}")
            return None
    
    def _estimate_quality_score(self, story: Dict[str, Any]) -> float:
        """Estimate quality score for standard generator stories"""
        score = 0.0
        max_score = 10.0
        
        # Check for required fields (3 points)
        required_fields = ['id', 'title', 'summary', 'full_content', 'content_type']
        if all(field in story and story[field] for field in required_fields):
            score += 3.0
        
        # Check content length (2 points)
        if 'full_content' in story:
            content_length = len(story['full_content'])
            if content_length > 1000:
                score += 2.0
            elif content_length > 500:
                score += 1.0
        
        # Check for enhanced fields (2 points)
        enhanced_fields = ['actionable_practices', 'discussion_prompts', 'belt_levels']
        present_enhanced = sum(1 for field in enhanced_fields if field in story and story[field])
        score += (present_enhanced / len(enhanced_fields)) * 2.0
        
        # Check for family focus (2 points)
        family_fields = ['family_security_relevance', 'children_education_angle']
        present_family = sum(1 for field in family_fields if field in story and story[field])
        score += (present_family / len(family_fields)) * 2.0
        
        # Basic completeness bonus (1 point)
        if len(story.keys()) > 10:
            score += 1.0
        
        return min(score, max_score)
    
    def transcribe_audio_file(self, audio_path: Path) -> Optional[str]:
        """Transcribe audio file - delegate to standard generator"""
        return self.standard_generator.transcribe_audio_file(audio_path)
    
    def process_episodes_batch(
        self, 
        episodes: List[Dict[str, Any]], 
        batch_size: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Process episodes in batches using integrated generator selection
        Maintains identical interface to existing StoryGenerator
        """
        logger.info(f"🔄 Processing {len(episodes)} episodes with integrated generator (batch size: {batch_size})")
        
        all_stories = []
        batch_stats = {'crewai': 0, 'standard': 0, 'fallback': 0}
        
        # Process in batches
        for i in range(0, len(episodes), batch_size):
            batch = episodes[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(episodes) + batch_size - 1) // batch_size
            
            logger.info(f"🔄 Processing integrated batch {batch_num}/{total_batches} ({len(batch)} episodes)")
            
            batch_stories = []
            
            for episode in batch:
                try:
                    # Check if episode has transcript or audio file
                    transcript = episode.get('transcript')
                    if not transcript and episode.get('compressed_filepath'):
                        # Transcribe first
                        audio_path = Path(episode['compressed_filepath'])
                        if audio_path.exists():
                            transcript = self.transcribe_audio_file(audio_path)
                    
                    if not transcript:
                        logger.warning(f"Episode {episode['id']}: No transcript available")
                        continue
                    
                    # Generate stories using integrated selection
                    stories = self.generate_stories_from_transcript(transcript, episode)
                    if stories:
                        # Track which generator was used
                        generator_used = stories[0].get('integration_metadata', {}).get('generator_used', 'unknown')
                        if 'fallback' in generator_used:
                            batch_stats['fallback'] += 1
                        elif generator_used == 'crewai':
                            batch_stats['crewai'] += 1
                        else:
                            batch_stats['standard'] += 1
                        
                        # Add episode reference to each story
                        for story in stories:
                            story['episode_id'] = episode['id']
                            story['transcript'] = transcript
                        
                        batch_stories.extend(stories)
                        logger.info(f"✅ Episode {episode['id']}: Generated {len(stories)} stories using {generator_used}")
                    else:
                        logger.error(f"❌ Episode {episode['id']}: Generation failed")
                
                except Exception as e:
                    logger.error(f"❌ Episode {episode['id']}: Processing error - {str(e)}")
                    continue
            
            all_stories.extend(batch_stories)
            logger.info(f"✅ Batch {batch_num} completed: {len(batch_stories)} stories generated")
            
            # Brief pause between batches
            if i + batch_size < len(episodes):
                logger.info("⏸️ Pausing between batches...")
                time.sleep(5)
        
        # Log final statistics
        logger.info(f"🎉 All integrated batches completed: {len(all_stories)} total stories generated")
        logger.info(f"📊 Generator usage: CrewAI={batch_stats['crewai']}, Standard={batch_stats['standard']}, Fallback={batch_stats['fallback']}")
        
        return all_stories
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status including integration metrics"""
        standard_status = self.standard_generator.get_status()
        crewai_status = self.crewai_generator.get_status() if self.crewai_generator else {'crewai_enabled': False}
        
        return {
            'integration_enabled': True,
            'integration_version': '1.0',
            'config': self.integration_config.get_config_summary(),
            'performance_comparison': self.performance_monitor.get_performance_comparison(),
            'standard_generator': standard_status,
            'crewai_generator': crewai_status,
            'generators_available': {
                'standard': True,
                'crewai': self.crewai_generator is not None
            }
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report for analysis"""
        return {
            'timestamp': datetime.now().isoformat(),
            'config': self.integration_config.get_config_summary(),
            'performance_comparison': self.performance_monitor.get_performance_comparison(),
            'recent_sessions': self.performance_monitor.metrics['sessions'][-10:],  # Last 10 sessions
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on performance data"""
        recommendations = []
        comparison = self.performance_monitor.get_performance_comparison()
        
        if comparison['recommendation'] == 'increase_rollout':
            recommendations.append("Consider increasing CrewAI rollout percentage - showing quality improvements")
        elif comparison['recommendation'] == 'decrease_rollout':
            recommendations.append("Consider decreasing CrewAI rollout percentage - quality or reliability concerns")
        elif comparison['recommendation'] == 'insufficient_data':
            recommendations.append("Insufficient data for recommendations - continue current rollout to gather metrics")
        
        # Check error rates
        if comparison.get('error_rate_difference', 0) > 5:
            recommendations.append("CrewAI showing higher error rates - monitor closely")
        
        # Check performance
        if comparison.get('time_difference', 0) > 60:
            recommendations.append("CrewAI taking significantly longer - consider optimization")
        
        return recommendations


# Convenience function for backward compatibility
def create_integrated_story_generator(
    api_key: str, 
    superprompt_path: Path, 
    config: Dict[str, Any] = None
) -> IntegratedStoryGenerator:
    """
    Create integrated story generator with CrewAI capabilities
    Drop-in replacement for StoryGenerator with enhanced functionality
    """
    return IntegratedStoryGenerator(api_key, superprompt_path, config)


if __name__ == "__main__":
    # Test integration
    import os
    
    print("🧪 Testing CrewAI Integration Layer")
    print("=" * 50)
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        exit(1)
    
    superprompt_path = Path("automation/SuperPrompt.md")
    if not superprompt_path.exists():
        print("❌ SuperPrompt.md not found")
        exit(1)
    
    try:
        # Test configuration
        config = IntegrationConfig()
        print(f"✅ Configuration loaded: {config.get_config_summary()}")
        
        # Test factory
        generator = StoryGeneratorFactory.create_story_generator(api_key, superprompt_path)
        print(f"✅ Generator created: {type(generator).__name__}")
        
        # Test integrated generator
        integrated = IntegratedStoryGenerator(api_key, superprompt_path)
        status = integrated.get_status()
        print(f"✅ Integrated generator created: {status['generators_available']}")
        
        # Test performance monitoring
        monitor = PerformanceMonitor(config)
        print(f"✅ Performance monitor initialized")
        
        print("\n📊 Integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        traceback.print_exc()