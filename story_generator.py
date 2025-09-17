#!/usr/bin/env python3
"""
STORY GENERATOR MODULE
Handles Gemini AI transcription and story generation using SuperPrompt.md
"""

import google.generativeai as genai
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)

class StoryGenerator:
    """Handles AI transcription and story generation with rate limiting"""
    
    def __init__(self, api_key: str, superprompt_path: Path):
        self.api_key = api_key
        self.superprompt_path = superprompt_path
        
        # Configure Gemini AI
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Rate limiting (10 RPM, 150/day)
        self.requests_per_minute = 10
        self.requests_per_day = 150
        self.request_times = []
        self.daily_request_count = 0
        self.last_reset_date = datetime.now().date()
        
        # Load SuperPrompt
        self.superprompt = self._load_superprompt()
        
        logger.info(f"StoryGenerator initialized")
    
    def _load_superprompt(self) -> str:
        """Load SuperPrompt.md content"""
        try:
            with open(self.superprompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"SuperPrompt loaded: {len(content)} characters")
            return content
        except Exception as e:
            logger.error(f"Failed to load SuperPrompt: {str(e)}")
            raise

    def _check_rate_limits(self) -> bool:
        """Check if we can make another API request"""
        now = datetime.now()
        current_date = now.date()
        
        # Reset daily counter if new day
        if current_date != self.last_reset_date:
            self.daily_request_count = 0
            self.last_reset_date = current_date
            logger.info("Daily rate limit counter reset")
        
        # Check daily limit
        if self.daily_request_count >= self.requests_per_day:
            logger.warning(f"Daily rate limit reached: {self.daily_request_count}/{self.requests_per_day}")
            return False
        
        # Check per-minute limit
        one_minute_ago = now - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > one_minute_ago]
        
        if len(self.request_times) >= self.requests_per_minute:
            logger.warning(f"Per-minute rate limit reached: {len(self.request_times)}/{self.requests_per_minute}")
            return False
        
        return True

    def _wait_for_rate_limit(self):
        """Wait until we can make another request"""
        while not self._check_rate_limits():
            logger.info("Waiting for rate limit reset...")
            time.sleep(10)

    def _make_api_request(self, prompt: str) -> Optional[str]:
        """Make rate-limited API request to Gemini"""
        self._wait_for_rate_limit()
        
        try:
            # Record request time
            now = datetime.now()
            self.request_times.append(now)
            self.daily_request_count += 1
            
            logger.debug(f"Making API request ({self.daily_request_count}/{self.requests_per_day} today)")
            
            # Make request
            response = self.model.generate_content(prompt)
            
            if response.text:
                logger.debug(f"API response received: {len(response.text)} characters")
                return response.text
            else:
                logger.warning("Empty response from Gemini API")
                return None
                
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            return None

    def _transcribe_audio_file(self, audio_path: Path) -> Optional[str]:
        """Private method for internal use - transcribe audio file using Gemini AI"""
        return self.transcribe_audio_file(audio_path)
    
    def transcribe_audio_file(self, audio_path: Path) -> Optional[str]:
        """Transcribe audio file using Gemini AI"""
        try:
            logger.info(f"Transcribing audio file: {audio_path.name}")
            
            # Upload audio file
            audio_file = genai.upload_file(str(audio_path))
            
            # Create transcription prompt
            prompt = "Please transcribe this audio file. Provide only the transcript text without any additional commentary or formatting."
            
            # Make API request with audio
            response = self._make_api_request_with_file(audio_file, prompt)
            
            if response:
                logger.info(f"✅ Transcription completed: {len(response)} characters")
                return response
            else:
                logger.error(f"❌ Transcription failed for {audio_path.name}")
                return None
                
        except Exception as e:
            logger.error(f"Transcription error for {audio_path.name}: {str(e)}")
            return None

    def _make_api_request_with_file(self, file, prompt: str) -> Optional[str]:
        """Make API request with uploaded file"""
        self._wait_for_rate_limit()
        
        try:
            # Record request time
            now = datetime.now()
            self.request_times.append(now)
            self.daily_request_count += 1
            
            logger.debug(f"Making API request with file ({self.daily_request_count}/{self.requests_per_day} today)")
            
            # Make request with file
            response = self.model.generate_content([file, prompt])
            
            if response.text:
                logger.debug(f"API response received: {len(response.text)} characters")
                return response.text
            else:
                logger.warning("Empty response from Gemini API")
                return None
                
        except Exception as e:
            logger.error(f"API request with file failed: {str(e)}")
            return None

    def generate_stories_from_transcript(self, transcript: str, episode_metadata: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Generate stories from transcript using SuperPrompt"""
        try:
            logger.info(f"Generating stories from transcript ({len(transcript)} chars)")
            
            # Create full prompt with SuperPrompt + transcript
            full_prompt = f"""{self.superprompt}

TRANSCRIPT TO PROCESS:
Podcast: {episode_metadata.get('podcast_title', 'Unknown')}
Episode: {episode_metadata.get('episode_title', 'Unknown')}
Published: {episode_metadata.get('published_date', 'Unknown')}

{transcript}

CRITICAL: You MUST return your response as valid JSON using EXACTLY this structure:
{{
  "investing-dojo-stories": [
    {{ ... your stories here ... }}
  ],
  "episode_summary": {{ ... }}
}}

Do NOT use any other root key like "stories", "newsletter_content", or "content". Use "investing-dojo-stories" exactly as shown above."""
            
            # Make API request
            response = self._make_api_request(full_prompt)
            
            if not response:
                return None
            
            # Parse JSON response
            try:
                # Clean response (remove markdown formatting if present)
                cleaned_response = self._clean_json_response(response)
                
                # Debug: Save raw response for analysis
                debug_file = Path("logs") / f"gemini_response_{int(time.time())}.txt"
                debug_file.parent.mkdir(exist_ok=True)
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(f"=== RAW RESPONSE ===\n{response}\n\n")
                    f.write(f"=== CLEANED RESPONSE ===\n{cleaned_response}\n\n")
                
                stories_data = json.loads(cleaned_response)
                
                # Debug: Log the structure we received
                logger.debug(f"Received JSON structure with keys: {list(stories_data.keys()) if isinstance(stories_data, dict) else 'Not a dict'}")
                
                # Validate and enhance stories
                stories = self._validate_and_enhance_stories(stories_data, episode_metadata)
                
                logger.info(f"✅ Generated {len(stories)} stories from transcript")
                return stories
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.debug(f"Raw response: {response[:500]}...")
                
                # Save failed response for debugging
                debug_file = Path("logs") / f"failed_response_{int(time.time())}.txt"
                debug_file.parent.mkdir(exist_ok=True)
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(f"=== FAILED JSON PARSING ===\n")
                    f.write(f"Error: {str(e)}\n\n")
                    f.write(f"Raw response:\n{response}\n\n")
                    f.write(f"Cleaned response:\n{self._clean_json_response(response)}\n")
                
                return None
                
        except Exception as e:
            logger.error(f"Story generation error: {str(e)}")
            return None

    def _clean_json_response(self, response: str) -> str:
        """Clean JSON response from potential markdown formatting"""
        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*$', '', response)
        
        # Remove any leading/trailing whitespace
        response = response.strip()
        
        return response

    def _validate_and_enhance_stories(self, stories_data: Any, episode_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate and enhance generated stories"""
        # Check for various possible JSON formats the AI might return
        stories = None
        if isinstance(stories_data, dict):
            # Try different possible keys the AI might use
            possible_keys = ['investing-dojo-stories', 'stories', 'newsletter_content', 'content', 'articles']
            
            for key in possible_keys:
                if key in stories_data:
                    stories = stories_data[key]
                    logger.info(f"Found stories under key: '{key}'")
                    break
            
            if stories is None:
                logger.warning(f"Invalid stories format - expected dict with one of {possible_keys}")
                logger.debug(f"Available keys: {list(stories_data.keys())}")
                return []
        else:
            logger.warning("Invalid stories format - expected dict")
            return []
        if not isinstance(stories, list):
            logger.warning("Invalid stories format - 'stories' should be a list")
            return []
        
        enhanced_stories = []
        
        for i, story in enumerate(stories):
            try:
                # Validate required fields
                if not isinstance(story, dict):
                    logger.warning(f"Story {i+1}: Invalid format - should be dict")
                    continue
                
                # Check for required fields that match the enhanced importer validation
                required_fields = ['id', 'title', 'summary', 'full_content', 'content_type']
                missing_fields = [field for field in required_fields if field not in story]
                
                if missing_fields:
                    logger.warning(f"Story {i+1}: Missing required fields: {missing_fields}")
                    continue
                
                # Enhance story with episode metadata
                enhanced_story = {
                    **story,
                    'source_type': 'podcast',
                    'source_podcast': episode_metadata.get('podcast_title', 'Unknown'),
                    'source_episode': episode_metadata.get('episode_title', 'Unknown'),
                    'source_url': episode_metadata.get('episode_url', ''),
                    'published_date': episode_metadata.get('published_date', ''),
                    'processed_date': datetime.now().isoformat(),
                    'ai_generated': True,
                    'generation_method': 'gemini_superprompt'
                }
                
                enhanced_stories.append(enhanced_story)
                
            except Exception as e:
                logger.error(f"Error processing story {i+1}: {str(e)}")
                continue
        
        return enhanced_stories

    def process_episodes_batch(self, episodes: List[Dict[str, Any]], batch_size: int = 3) -> List[Dict[str, Any]]:
        """Process episodes in batches with rate limiting"""
        logger.info(f"Processing {len(episodes)} episodes in batches of {batch_size}")
        
        all_stories = []
        
        # Process in batches
        for i in range(0, len(episodes), batch_size):
            batch = episodes[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(episodes) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} episodes)")
            
            batch_stories = []
            
            for episode in batch:
                try:
                    # Check if episode has compressed audio file
                    if not episode.get('compressed_filepath'):
                        logger.warning(f"Episode {episode['id']}: No compressed audio file")
                        continue
                    
                    audio_path = Path(episode['compressed_filepath'])
                    if not audio_path.exists():
                        logger.warning(f"Episode {episode['id']}: Audio file not found: {audio_path}")
                        continue
                    
                    # Transcribe audio
                    transcript = self.transcribe_audio_file(audio_path)
                    if not transcript:
                        logger.error(f"Episode {episode['id']}: Transcription failed")
                        continue
                    
                    # Generate stories from transcript
                    stories = self.generate_stories_from_transcript(transcript, episode)
                    if stories:
                        # Add episode reference to each story
                        for story in stories:
                            story['episode_id'] = episode['id']
                            story['transcript'] = transcript
                        
                        batch_stories.extend(stories)
                        logger.info(f"Episode {episode['id']}: Generated {len(stories)} stories")
                    else:
                        logger.error(f"Episode {episode['id']}: Story generation failed")
                
                except Exception as e:
                    logger.error(f"Episode {episode['id']}: Processing error - {str(e)}")
                    continue
            
            all_stories.extend(batch_stories)
            logger.info(f"Batch {batch_num} completed: {len(batch_stories)} stories generated")
            
            # Brief pause between batches
            if i + batch_size < len(episodes):
                logger.info("Pausing between batches...")
                time.sleep(5)
        
        logger.info(f"All batches completed: {len(all_stories)} total stories generated")
        return all_stories
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status and configuration for backward compatibility"""
        return {
            'generator_type': 'standard',
            'api_key_configured': bool(self.api_key),
            'superprompt_loaded': bool(self.superprompt),
            'rate_limits': {
                'requests_per_minute': self.requests_per_minute,
                'requests_per_day': self.requests_per_day
            },
            'daily_requests_used': self.daily_request_count,
            'requests_in_last_minute': len(self.request_times),
            'last_reset_date': self.last_reset_date.isoformat()
        }