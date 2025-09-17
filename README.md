# InvestingDojo Automation System

## Overview

This automation system provides end-to-end content generation for InvestingDojo.co using advanced AI agents and workflow orchestration. The system has been completely reorganized for better maintainability and includes both traditional AI processing and a sophisticated CrewAI 9-agent system.

### Key Features

1. **RSS Feed Scanning** - Monitors 250+ financial podcast feeds daily
2. **MP3 Processing** - Downloads and compresses audio files to <20MB
3. **AI Transcription** - Uses Gemini AI to transcribe audio content
4. **Dual Story Generation** - Traditional AI + CrewAI 9-agent system
5. **Database Import** - Imports generated content into the InvestingDojo database
6. **Editorial Curation** - AI-powered content quality control

## 📁 Folder Structure

```
automation/
├── 📄 Active Production Files
│   ├── COMPLETE_DAILY_AUTOMATION.py     # Main automation orchestrator
│   ├── crew_ai_story_generator.py       # CrewAI 9-agent system
│   ├── crewai_config.py                 # CrewAI configuration
│   ├── crewai_integration.py            # CrewAI integration layer
│   ├── editorial_director.py            # Content curation system
│   ├── story_generator.py               # Fallback story generator
│   ├── podcast_harvester.py             # RSS harvesting engine
│   ├── database_importer.py             # Database operations
│   ├── requirements.txt                 # Python dependencies
│   ├── run_daily_automation.bat         # Windows scheduler script
│   ├── setup_windows_scheduler.py       # Scheduler setup utility
│   ├── scheduler_config.json            # Scheduler configuration
│   ├── SuperPrompt_Optimized.md         # Main prompt template
│   ├── SuperPrompt.md                   # Compatibility fallback
│   └── .env.crewai.example              # Configuration template
│
├── 📁 archive/                          # Unused/test files
│   ├── test_*.py                        # All test files
│   ├── old automation scripts           # Legacy automation files
│   ├── comparison scripts               # Validation utilities
│   └── temp_processing/                 # Old processing folders
│
└── 📁 docs/                             # Technical documentation
    ├── AUTOMATION_FIXES_SUMMARY.md      # System fixes documentation
    ├── CREWAI_INTEGRATION_GUIDE.md      # CrewAI setup guide
    ├── CREWAI_SYSTEM_TEST_GUIDE.md      # Testing procedures
    └── [other technical docs]           # Additional documentation
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy and configure the environment template:
```bash
copy .env.crewai.example .env.crewai
```

Edit `.env.crewai` with your API keys:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # For CrewAI agents
```

### 3. Run Manual Automation

```bash
python COMPLETE_DAILY_AUTOMATION.py
```

### 4. Setup Daily Automation

```bash
python setup_windows_scheduler.py
```

## 🏗️ System Architecture

### Core Production Components

#### 1. COMPLETE_DAILY_AUTOMATION.py
**Main orchestrator** that coordinates the entire workflow:
- RSS feed scanning and episode discovery
- MP3 download and compression
- Dual AI processing (traditional + CrewAI)
- Database import and reporting
- Comprehensive error handling and logging

#### 2. crew_ai_story_generator.py
**CrewAI 9-Agent System** with specialized roles:
- **Research Analyst** - Market data analysis
- **Content Strategist** - Story structure planning
- **Financial Writer** - Professional content creation
- **Editor** - Quality control and refinement
- **SEO Specialist** - Search optimization
- **Fact Checker** - Accuracy verification
- **Engagement Expert** - Reader engagement optimization
- **Technical Analyst** - Chart and data analysis
- **Publishing Coordinator** - Final content preparation

#### 3. editorial_director.py
**Content Curation System** that:
- Evaluates story quality and relevance
- Filters content based on engagement potential
- Ensures editorial standards compliance
- Manages content approval workflow

#### 4. podcast_harvester.py
**RSS Processing Engine** that:
- Scans 250+ financial podcast feeds
- Downloads and compresses MP3 files
- Manages batch processing efficiently
- Handles retry logic and error recovery

#### 5. story_generator.py
**Fallback AI Generator** that:
- Provides traditional AI story generation
- Acts as backup when CrewAI is unavailable
- Uses optimized SuperPrompt templates
- Implements rate limiting and validation

#### 6. database_importer.py
**Database Operations Manager** that:
- Converts AI stories to database format
- Handles duplicate detection and updates
- Manages transactions and error handling
- Provides detailed import statistics

### Configuration Files

#### SuperPrompt_Optimized.md
Main prompt template optimized for financial content generation with:
- Structured story format requirements
- Financial terminology guidelines
- SEO optimization instructions
- Engagement enhancement techniques

#### scheduler_config.json
Windows Task Scheduler configuration for automated daily runs.

## 🔧 Configuration

### Rate Limits
- **Gemini API**: 10 requests per minute, 150 per day
- **OpenAI API**: Varies by plan (for CrewAI agents)
- **Batch Processing**: 3 episodes per AI batch
- **RSS Scanning**: 50 episodes per batch

### CrewAI Configuration
The CrewAI system can be configured in [`crewai_config.py`](crewai_config.py):
- Agent roles and responsibilities
- Task definitions and workflows
- Model selection and parameters
- Output formatting requirements

### Database Configuration
```python
{
    'host': 'localhost',
    'database': 'u219832816_investing_dojo',
    'user': 'u219832816_davethackeray',
    'charset': 'utf8mb4'
}
```

## 📊 Monitoring and Logs

### Log Files
- `logs/daily_automation_YYYYMMDD_HHMMSS.log` - Main automation log
- `logs/automation_report_YYYYMMDD_HHMMSS.json` - Detailed report
- `logs/scheduler_log.txt` - Windows Task Scheduler log
- `logs/crewai_YYYYMMDD_HHMMSS.log` - CrewAI agent logs

### Key Metrics
- RSS feeds processed
- Episodes found and downloaded
- Stories generated (traditional vs CrewAI)
- Database imports and updates
- API requests used across services
- Processing time and error rates
- Content quality scores

## 🔍 Troubleshooting

### Common Issues

#### 1. API Keys Not Set
```
Error: GEMINI_API_KEY or OPENAI_API_KEY is required
```
**Solution**: Configure `.env.crewai` with valid API keys

#### 2. CrewAI Agent Failures
```
Error: CrewAI agent execution failed
```
**Solution**: Check agent configurations and API quotas, system will fallback to traditional AI

#### 3. Database Connection Issues
```
Error: Database connection error
```
**Solution**: Verify database credentials and network connectivity

#### 4. Rate Limit Exceeded
```
Warning: Daily rate limit reached
```
**Solution**: Wait for quota reset or adjust batch processing intervals

### Debug Mode
```bash
# Run with comprehensive debugging
python COMPLETE_DAILY_AUTOMATION.py --debug

# Test individual components
python -c "from crew_ai_story_generator import CrewAIStoryGenerator; print('CrewAI OK')"
python -c "from editorial_director import EditorialDirector; print('Editorial OK')"
```

## 📚 Documentation

### Technical Documentation
All technical documentation has been moved to the [`docs/`](docs/) folder:

- **[CREWAI_INTEGRATION_GUIDE.md](docs/CREWAI_INTEGRATION_GUIDE.md)** - Complete CrewAI setup guide
- **[CREWAI_SYSTEM_TEST_GUIDE.md](docs/CREWAI_SYSTEM_TEST_GUIDE.md)** - Testing procedures
- **[AUTOMATION_FIXES_SUMMARY.md](docs/AUTOMATION_FIXES_SUMMARY.md)** - System fixes and improvements
- **[Additional technical docs](docs/)** - Various system documentation

### Archived Files
Historical files and tests have been moved to the [`archive/`](archive/) folder:
- All test files (`test_*.py`)
- Legacy automation scripts
- Comparison and validation utilities
- Old processing folders and data

## 🚀 Production Deployment

### Current Setup (Windows)
- Automated daily execution via Windows Task Scheduler
- Local database integration
- Comprehensive logging and monitoring
- Error recovery and retry mechanisms

### Future VPS Migration
1. Transfer production files to VPS
2. Configure cron jobs for Linux scheduling
3. Update database configuration for production
4. Implement monitoring and alerting
5. Set up backup and recovery procedures

## 🔒 Security Considerations

- Store API keys in environment variables only
- Use `.env.crewai` for sensitive configuration
- Implement proper error handling to prevent data leaks
- Monitor API usage and costs
- Regular security audits of automation processes

## 📈 Performance Optimization

### CrewAI vs Traditional AI
- **CrewAI**: Higher quality, more comprehensive analysis, slower processing
- **Traditional AI**: Faster processing, good quality, fallback option
- **Hybrid Approach**: System automatically chooses based on availability and requirements

### Batch Processing
- Episodes processed in batches of 3 for optimal API usage
- RSS feeds scanned in batches of 50 for efficiency
- Intelligent retry logic for failed operations

## 🆘 Support

For issues or questions:

1. **Check Logs**: Review logs in the `logs/` directory
2. **Documentation**: Consult technical docs in the [`docs/`](docs/) folder
3. **Test System**: Run component tests to isolate issues
4. **Review Reports**: Check automation report JSON files for metrics

## 📋 Version History

- **v1.0** - Initial automation system with RSS scanning and AI processing
- **v1.1** - Added Windows Task Scheduler integration
- **v1.2** - Enhanced error handling and rate limiting
- **v2.0** - **MAJOR UPDATE**: Added CrewAI 9-agent system and editorial curation
- **v2.1** - **CURRENT**: Reorganized folder structure, improved documentation, enhanced monitoring

---

## 🎯 Current Status

✅ **Production Ready** - System is fully operational with dual AI processing  
✅ **Well Organized** - Clean folder structure with proper documentation  
✅ **Monitored** - Comprehensive logging and reporting  
✅ **Scalable** - Ready for VPS deployment and expansion  

**Last Updated**: July 30, 2025  
**Maintainer**: InvestingDojo Development Team