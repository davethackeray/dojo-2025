# CrewAI System Test Suite - Comprehensive Guide

## Overview

The **CrewAI System Test Suite** (`test_crewai_complete_system.py`) is a comprehensive testing framework designed to validate the multi-agent CrewAI system integration and ensure production readiness. This test suite provides end-to-end validation of JSON output compatibility, A/B testing framework, database schema validation, performance metrics, and integration layer functionality.

## Features

### 🔍 **JSON Output Compatibility Testing**
- Validates JSON schema compatibility between SuperPrompt and CrewAI workflows
- Ensures both workflows produce identical JSON structure
- Tests ENUM field validation against database constraints
- Validates all required fields are present and properly formatted

### 🔄 **A/B Testing Framework Validation**
- Tests consistent episode assignment for reliable comparison
- Validates rollout percentage functionality (5%, 25%, 50%, 100%)
- Tests quality scoring and performance metrics collection
- Validates automatic fallback triggers and rollback mechanisms

### 💾 **Database Schema Validation**
- Tests JSON output against existing database import logic
- Validates all ENUM fields match database constraints
- Tests relationship data import compatibility
- Verifies time normalization and field mapping works correctly

### ⚡ **Performance and Quality Testing**
- Compares processing time between SuperPrompt and CrewAI workflows
- Tests rate limiting compliance (10 RPM, 150/day)
- Validates quality scoring accuracy and consistency
- Tests error handling and recovery mechanisms

### 🔗 **Integration Layer Testing**
- Tests drop-in replacement functionality
- Validates existing automation scripts work unchanged
- Tests environment variable configuration and feature flags
- Validates logging and monitoring capabilities

### 📊 **eToro Data Testing**
- Uses real eToro test data from `temp_processing/etoro_test/`
- Tests complete workflow with authentic podcast data
- Validates production-ready performance with real data

### 📋 **Production Readiness Assessment**
- Generates comprehensive production readiness report
- Provides safety mechanism recommendations
- Validates system capabilities and compatibility
- Creates detailed metrics and performance analysis

## Installation & Setup

### Prerequisites

1. **Environment Variables Required:**
   ```bash
   GEMINI_API_KEY=your_gemini_api_key
   DB_LOCAL_HOST=localhost
   DB_LOCAL_DATABASE=u219832816_investing_dojo
   DB_LOCAL_USER=u219832816_davethackeray
   DB_LOCAL_PASSWORD=your_password
   ```

2. **CrewAI Dependencies:**
   ```bash
   pip install crewai crewai-tools
   ```

3. **Existing Automation Components:**
   - `automation/story_generator.py` (SuperPrompt workflow)
   - `automation/crew_ai_story_generator.py` (CrewAI workflow)
   - `automation/crewai_integration.py` (Integration layer)
   - `automation/database_importer.py` (Database operations)

## Usage

### Basic Usage

```bash
# Run all tests
python automation/test_crewai_complete_system.py

# Run specific test type
python automation/test_crewai_complete_system.py --test-type=compatibility
python automation/test_crewai_complete_system.py --test-type=performance
python automation/test_crewai_complete_system.py --test-type=integration

# Enable verbose logging
python automation/test_crewai_complete_system.py --verbose
```

### Test Types Available

| Test Type | Description |
|-----------|-------------|
| `all` | Run all test suites (default) |
| `compatibility` | JSON output compatibility testing |
| `ab_testing` | A/B testing framework validation |
| `database` | Database schema validation |
| `performance` | Performance and quality testing |
| `integration` | Integration layer testing |
| `etoro` | eToro data testing |

### Advanced Configuration

```bash
# Use custom configuration file
python automation/test_crewai_complete_system.py --config=custom_test_config.json
```

## Test Configuration

The test suite uses the following default configuration:

```python
{
    'api_key': os.getenv('GEMINI_API_KEY'),
    'superprompt_path': Path("automation/SuperPrompt.md"),
    'test_episodes_limit': 3,
    'timeout_seconds': 300,
    'quality_threshold': 7.0,
    'performance_tolerance': 0.2,  # 20% performance difference tolerance
    'required_fields': [
        'id', 'title', 'summary', 'full_content', 'content_type',
        'belt_levels', 'difficulty_level', 'time_required'
    ],
    'enum_fields': {
        'belt_levels': ['white-belt', 'yellow-belt', 'orange-belt', 'green-belt', 
                       'blue-belt', 'brown-belt', 'black-belt'],
        'content_type': ['curriculum-war-story', 'ai-breakthrough', 'systematic-strategy',
                       'family-wealth-builder', 'mastery-technique', 'mindset-hack',
                       'research-method', 'risk-lesson', 'epic-curriculum-fail',
                       'belt-progression-moment', 'ai-integration-guide', 'generational-wealth-wisdom'],
        'difficulty_level': ['foundational', 'intermediate-skill', 'advanced-mastery'],
        'time_required': ['5-minutes', '10-minutes', '15-minutes', '30-minutes',
                        '1-hour', '2-hours', 'ongoing', 'varies']
    },
    'integration_config': {
        'crewai_enabled': True,
        'rollout_percentage': 50,
        'ab_testing_enabled': True,
        'monitoring_enabled': True,
        'auto_fallback': True
    }
}
```

## Test Results & Reports

### Log Files

All test runs generate detailed log files in `logs/crewai_tests/`:
- `crewai_system_test_YYYYMMDD_HHMMSS.log` - Detailed test execution log
- `production_readiness_report_YYYYMMDD_HHMMSS.json` - Comprehensive assessment report

### Production Readiness Report

The final report includes:

```json
{
    "assessment_timestamp": "2025-07-30T08:23:51.696Z",
    "test_duration_seconds": 120.5,
    "production_ready": true,
    "overall_success_rate": 1.0,
    "test_summary": {
        "total_tests": 6,
        "successful_tests": 6,
        "failed_tests": 0
    },
    "aggregated_metrics": {
        "total_stories_tested": 12,
        "compatibility_score": 0.95,
        "enum_compliance_rate": 1.0,
        "average_quality_score": 8.2
    },
    "critical_errors": [],
    "warnings": [],
    "recommendations": [
        "System appears ready for production deployment with monitoring"
    ],
    "system_capabilities": {
        "crewai_available": true,
        "integration_layer_functional": true,
        "database_compatible": true,
        "performance_acceptable": true
    }
}
```

## Production Readiness Criteria

The system is considered **production ready** when:

1. **Overall Success Rate ≥ 80%** - At least 80% of tests pass
2. **Zero Critical Errors** - No blocking issues found
3. **High Compatibility Score ≥ 90%** - JSON schemas are highly compatible
4. **Quality Threshold Met** - Average quality score ≥ 7.0
5. **Performance Acceptable** - Processing time difference within tolerance
6. **Database Compatible** - All imports work without errors
7. **Integration Functional** - All integration features working

## Troubleshooting

### Common Issues

1. **GEMINI_API_KEY not found**
   ```bash
   export GEMINI_API_KEY=your_api_key
   ```

2. **CrewAI not available**
   ```bash
   pip install crewai crewai-tools
   ```

3. **Database connection failed**
   - Check database credentials in environment variables
   - Ensure database server is running
   - Verify network connectivity

4. **SuperPrompt.md not found**
   - Ensure `automation/SuperPrompt.md` exists
   - Check file path in configuration

### Debug Mode

Enable verbose logging for detailed debugging:

```bash
python automation/test_crewai_complete_system.py --verbose
```

## Integration with Existing Workflow

The test suite is designed to work seamlessly with the existing automation workflow:

1. **Non-intrusive Testing** - Does not modify existing automation scripts
2. **Backward Compatibility** - Validates existing functionality continues to work
3. **Drop-in Replacement** - Tests that CrewAI can replace SuperPrompt without changes
4. **Safety Mechanisms** - Validates fallback and error handling

## Continuous Integration

For CI/CD integration:

```bash
# Exit code 0 = production ready, 1 = needs work
python automation/test_crewai_complete_system.py
if [ $? -eq 0 ]; then
    echo "✅ System is production ready!"
    # Deploy to production
else
    echo "❌ System needs additional work"
    # Block deployment
fi
```

## Test Data

### Test Transcripts
- Uses real transcripts from `automation/test-transcripts/`
- Falls back to sample transcript if no real data available

### eToro Test Data
- Uses real eToro podcast data from `temp_processing/etoro_test/`
- Validates with authentic financial content
- Tests complete workflow with production-like data

## Quality Scoring

Stories are scored on a 10-point scale based on:

- **Required Fields (3 points)** - All mandatory fields present
- **Content Length (2 points)** - Adequate content depth
- **Enhanced Fields (2 points)** - Advanced features present
- **Family Focus (2 points)** - Family-oriented content
- **Completeness (1 point)** - Overall completeness

## Performance Metrics

The test suite measures:

- **Processing Time** - Time to generate stories
- **Quality Scores** - Average quality of generated content
- **API Usage** - Rate limiting compliance
- **Success Rates** - Percentage of successful operations
- **Error Rates** - Frequency of failures

## Safety & Validation

### Automatic Fallback Testing
- Tests that system falls back to SuperPrompt if CrewAI fails
- Validates error handling and recovery mechanisms
- Ensures no data loss during failures

### Rate Limiting Compliance
- Validates API usage stays within limits (10 RPM, 150/day)
- Tests rate limiting logic and queuing
- Ensures sustainable production usage

### Database Safety
- Tests import operations without affecting production data
- Validates schema compatibility before deployment
- Ensures data integrity and consistency

## Conclusion

The CrewAI System Test Suite provides comprehensive validation of the multi-agent system integration, ensuring production readiness while maintaining backward compatibility and safety. The test suite validates all critical aspects of the system and provides detailed reporting for informed deployment decisions.

For questions or issues, refer to the detailed logs and reports generated by the test suite.