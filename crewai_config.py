#!/usr/bin/env python3
"""
CREWAI CONFIGURATION MODULE
Handles CrewAI framework configuration with Gemini AI integration
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import google.generativeai as genai
from crewai import LLM
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CrewAIConfig:
    """CrewAI configuration with Gemini AI backend and rate limiting"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for CrewAI configuration")
        
        # Feature flag for enabling/disabling CrewAI
        self.crewai_enabled = os.getenv('CREWAI_ENABLED', 'false').lower() == 'true'
        
        # Rate limiting configuration (updated limits)
        self.rate_limits = {
            'requests_per_minute': 10,
            'requests_per_day': 500
        }
        
        # Request tracking for rate limiting
        self.request_times = []
        self.daily_request_count = 0
        self.last_reset_date = datetime.now().date()
        
        # Initialize Gemini AI
        genai.configure(api_key=self.api_key)
        
        # CrewAI LLM configuration for Gemini
        self.llm_config = self._setup_gemini_llm()
        
        logger.info(f"CrewAI configuration initialized (enabled: {self.crewai_enabled})")
    
    def _setup_gemini_llm(self) -> LLM:
        """Setup CrewAI LLM with Gemini backend"""
        try:
            # Configure CrewAI to use Gemini
            llm = LLM(
                model="gemini/gemini-2.5-flash",
                api_key=self.api_key,
                temperature=0.7,
                max_tokens=8192,
                timeout=60
            )
            
            logger.info("✅ CrewAI LLM configured with Gemini backend")
            return llm
            
        except Exception as e:
            logger.error(f"❌ Failed to configure CrewAI LLM: {str(e)}")
            raise
    
    def get_llm(self) -> LLM:
        """Get configured LLM instance"""
        return self.llm_config
    
    def is_enabled(self) -> bool:
        """Check if CrewAI is enabled via feature flag"""
        return self.crewai_enabled
    
    def enable_crewai(self):
        """Enable CrewAI functionality"""
        self.crewai_enabled = True
        logger.info("✅ CrewAI enabled")
    
    def disable_crewai(self):
        """Disable CrewAI functionality"""
        self.crewai_enabled = False
        logger.info("⏸️ CrewAI disabled")
    
    def check_rate_limits(self) -> bool:
        """Check if we can make another API request (matching existing pattern)"""
        now = datetime.now()
        current_date = now.date()
        
        # Reset daily counter if new day
        if current_date != self.last_reset_date:
            self.daily_request_count = 0
            self.last_reset_date = current_date
            logger.info("Daily rate limit counter reset")
        
        # Check daily limit
        if self.daily_request_count >= self.rate_limits['requests_per_day']:
            logger.warning(f"Daily rate limit reached: {self.daily_request_count}/{self.rate_limits['requests_per_day']}")
            return False
        
        # Check per-minute limit
        one_minute_ago = now - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > one_minute_ago]
        
        if len(self.request_times) >= self.rate_limits['requests_per_minute']:
            logger.warning(f"Per-minute rate limit reached: {len(self.request_times)}/{self.rate_limits['requests_per_minute']}")
            return False
        
        return True
    
    def record_api_request(self):
        """Record an API request for rate limiting"""
        now = datetime.now()
        self.request_times.append(now)
        self.daily_request_count += 1
        logger.debug(f"API request recorded ({self.daily_request_count}/{self.rate_limits['requests_per_day']} today)")
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get standard agent configuration"""
        return {
            'llm': self.llm_config,
            'verbose': True,
            'memory': False,  # Disable memory to avoid Chroma dependency
            'max_iter': 3,
            'max_execution_time': 300,  # 5 minutes timeout
            'allow_delegation': False
        }
    
    def get_task_config(self) -> Dict[str, Any]:
        """Get standard task configuration"""
        return {
            'verbose': True,
            'async_execution': False,
            'human_input': False
        }
    
    def get_crew_config(self) -> Dict[str, Any]:
        """Get standard crew configuration"""
        return {
            'verbose': True,
            'memory': False,  # Disable memory to avoid Chroma dependency
            'cache': False,   # Disable cache to avoid vector database dependency
            'max_rpm': self.rate_limits['requests_per_minute'],
            'share_crew': False,
            'step_callback': self._step_callback
        }
    
    def _step_callback(self, step_output):
        """Callback for crew execution steps"""
        logger.debug(f"CrewAI step completed: {step_output}")
        self.record_api_request()
    
    def load_superprompt(self, superprompt_path = None) -> str:
        """Load SuperPrompt.md content for agent instructions"""
        if not superprompt_path:
            superprompt_path = Path("automation/SuperPrompt.md")
        elif isinstance(superprompt_path, str):
            superprompt_path = Path(superprompt_path)
        
        try:
            with open(superprompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"SuperPrompt loaded: {len(content)} characters")
            return content
        except Exception as e:
            logger.error(f"Failed to load SuperPrompt: {str(e)}")
            raise
    
    def get_story_generation_tools(self) -> list:
        """Get tools for story generation agents"""
        # Import CrewAI tools (optional)
        try:
            from crewai_tools import (
                FileReadTool,
                DirectoryReadTool,
                WebsiteSearchTool
            )
            
            tools = [
                FileReadTool(),
                DirectoryReadTool(),
            ]
            
            logger.info(f"✅ Loaded {len(tools)} CrewAI tools")
            return tools
            
        except ImportError as e:
            logger.info(f"📝 CrewAI tools not available, using basic setup: {str(e)}")
            return []  # Return empty list, agents will work without tools
    
    def validate_configuration(self) -> bool:
        """Validate CrewAI configuration"""
        try:
            # Test LLM connection
            test_response = self.llm_config.call("Test connection")
            if test_response:
                logger.info("✅ CrewAI configuration validation passed")
                return True
            else:
                logger.error("❌ CrewAI LLM test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ CrewAI configuration validation failed: {str(e)}")
            return False
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment information for debugging"""
        return {
            'crewai_enabled': self.crewai_enabled,
            'api_key_configured': bool(self.api_key),
            'rate_limits': self.rate_limits,
            'daily_requests_used': self.daily_request_count,
            'requests_in_last_minute': len(self.request_times),
            'last_reset_date': self.last_reset_date.isoformat()
        }


def create_crewai_config(api_key: Optional[str] = None) -> CrewAIConfig:
    """Factory function to create CrewAI configuration"""
    return CrewAIConfig(api_key=api_key)


def is_crewai_available() -> bool:
    """Check if CrewAI is available and properly configured"""
    try:
        import crewai
        # Note: crewai_tools is optional
        
        # Check if API key is available
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.warning("GEMINI_API_KEY not found - CrewAI unavailable")
            return False
        
        # Check feature flag
        enabled = os.getenv('CREWAI_ENABLED', 'false').lower() == 'true'
        if not enabled:
            logger.info("CrewAI disabled via CREWAI_ENABLED flag")
            return False
        
        logger.info("✅ CrewAI is available and enabled")
        return True
        
    except ImportError as e:
        logger.warning(f"CrewAI not available: {str(e)}")
        return False


if __name__ == "__main__":
    # Test configuration
    print("🧪 Testing CrewAI Configuration")
    print("=" * 40)
    
    try:
        config = create_crewai_config()
        print(f"✅ Configuration created successfully")
        print(f"📊 Environment info: {config.get_environment_info()}")
        
        if config.validate_configuration():
            print("✅ Configuration validation passed")
        else:
            print("❌ Configuration validation failed")
            
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")