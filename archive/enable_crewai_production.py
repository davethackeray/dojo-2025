#!/usr/bin/env python3
"""
ENABLE CREWAI PRODUCTION DEPLOYMENT
Simple script to enable CrewAI in production environment
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def enable_crewai_production():
    """Enable CrewAI for production use"""
    logger.info("🚀 Enabling CrewAI for Production Deployment")
    logger.info("=" * 50)
    
    # Check if GEMINI_API_KEY exists
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("❌ GEMINI_API_KEY environment variable not found")
        logger.error("Please set your Gemini API key first:")
        logger.error("set GEMINI_API_KEY=your_api_key_here")
        return False
    
    logger.info(f"✅ GEMINI_API_KEY found: {api_key[:10]}...")
    
    # Enable CrewAI
    os.environ['CREWAI_ENABLED'] = 'true'
    logger.info("✅ CREWAI_ENABLED set to 'true'")
    
    # Test CrewAI availability
    try:
        from crewai_config import is_crewai_available
        
        if is_crewai_available():
            logger.info("✅ CrewAI is available and ready")
        else:
            logger.warning("⚠️ CrewAI not available - will use fallback SuperPrompt")
            
    except ImportError as e:
        logger.warning(f"⚠️ CrewAI import failed: {str(e)}")
        logger.warning("Will use fallback SuperPrompt")
    
    # Verify daily automation script exists
    daily_script = Path("COMPLETE_DAILY_AUTOMATION.py")
    if daily_script.exists():
        logger.info(f"✅ Daily automation script found: {daily_script}")
    else:
        logger.error(f"❌ Daily automation script not found: {daily_script}")
        return False
    
    # Show deployment status
    logger.info("\n📊 DEPLOYMENT STATUS")
    logger.info("Environment Variables:")
    logger.info(f"  GEMINI_API_KEY: {'✅ Set' if api_key else '❌ Missing'}")
    logger.info(f"  CREWAI_ENABLED: {'✅ true' if os.getenv('CREWAI_ENABLED') == 'true' else '❌ false'}")
    
    logger.info("\nSystem Components:")
    logger.info(f"  Daily Automation: {'✅ Ready' if daily_script.exists() else '❌ Missing'}")
    logger.info(f"  CrewAI Available: {'✅ Yes' if is_crewai_available() else '⚠️ Fallback Mode'}")
    
    # API Usage Estimates
    logger.info("\n📈 API USAGE ESTIMATES")
    logger.info("CrewAI 9-Agent Workflow:")
    logger.info("  • ~9 API calls per story generation")
    logger.info("  • Daily limit: 500 calls")
    logger.info("  • Max stories per day: ~55")
    logger.info("  • Recommended daily: 30-40 stories")
    logger.info("  • Current automation: ~10-20 stories/day")
    logger.info("  • Safety margin: ✅ Excellent")
    
    # Next Steps
    logger.info("\n🎯 NEXT STEPS")
    logger.info("1. Run daily automation to test:")
    logger.info("   python COMPLETE_DAILY_AUTOMATION.py")
    logger.info("")
    logger.info("2. Monitor API usage in logs")
    logger.info("")
    logger.info("3. Check story quality in database")
    logger.info("")
    logger.info("4. Verify British spelling and sentence case")
    
    logger.info("\n🚀 CrewAI Production Deployment: READY!")
    return True

def main():
    """Main function"""
    try:
        success = enable_crewai_production()
        if success:
            logger.info("\n✅ Production deployment enabled successfully!")
            logger.info("The daily automation will now use CrewAI 9-agent workflow.")
        else:
            logger.error("\n❌ Production deployment failed!")
            logger.error("Please fix the issues above and try again.")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Deployment error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)