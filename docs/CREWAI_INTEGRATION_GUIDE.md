# CrewAI Integration Guide

## Overview

This guide documents the seamless integration of the CrewAI multi-agent system with the existing InvestingDojo automation pipeline. The integration maintains **100% backward compatibility** while adding enhanced story generation capabilities through a 9-agent workflow.

## 🎯 Integration Objectives

- **Non-intrusive**: No modifications to existing `COMPLETE_DAILY_AUTOMATION.py`
- **Backward Compatible**: Existing automation continues working unchanged
- **Gradual Rollout**: Configurable percentage-based deployment
- **A/B Testing**: Compare quality between SuperPrompt and CrewAI workflows
- **Automatic Fallback**: Seamless fallback on any issues
- **Performance Monitoring**: Comprehensive metrics and quality comparison

## 🏗️ Architecture Overview

```
COMPLETE_DAILY_AUTOMATION.py (unchanged)
    ↓
StoryGenerator (existing interface)
    ↓
crewai_integration.py (new integration layer)
    ↓
┌─────────────────┬─────────────────┐
│  StoryGenerator │ CrewAIStoryGen  │
│   (SuperPrompt) │   (9 Agents)    │
└─────────────────┴─────────────────┘
```

### Key Components

1. **IntegratedStoryGenerator**: Drop-in replacement for StoryGenerator
2. **StoryGeneratorFactory**: Creates appropriate generator based on configuration
3. **IntegrationConfig**: Manages environment variables and feature flags
4. **PerformanceMonitor**: Tracks quality metrics and performance comparison
5. **Automatic Fallback**: Ensures reliability with seamless fallback

## 🔧 Configuration System

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CREWAI_ENABLED` | `false` | Master switch for CrewAI functionality |
| `CREWAI_ROLLOUT_PERCENTAGE` | `0` | Percentage of episodes using CrewAI (0-100) |
| `CREWAI_AB_TESTING` | `false` | Enable consistent A/B testing per episode |
| `CREWAI_AB_TESTING_SEED` | `investingdojo` | Seed for deterministic A/B assignment |
| `CREWAI_QUALITY_THRESHOLD` | `7.0` | Minimum quality score before rollback |
| `CREWAI_ERROR_THRESHOLD` | `10.0` | Maximum error rate % before rollback |
| `CREWAI_MONITORING` | `true` | Enable performance monitoring |
| `CREWAI_AUTO_FALLBACK` | `true` | Enable automatic fallback on failures |
| `CREWAI_FALLBACK_TIMEOUT` | `300` | Timeout in seconds before fallback |
| `CREWAI_METRICS_RETENTION` | `30` | Days to retain performance metrics |

### Configuration Examples

#### Development Testing (5% rollout)
```bash
export CREWAI_ENABLED=true
export CREWAI_ROLLOUT_PERCENTAGE=5
export CREWAI_AB_TESTING=true
export CREWAI_MONITORING=true
```

#### Production Gradual Rollout (25% rollout)
```bash
export CREWAI_ENABLED=true
export CREWAI_ROLLOUT_PERCENTAGE=25
export CREWAI_AB_TESTING=true
export CREWAI_QUALITY_THRESHOLD=8.0
export CREWAI_AUTO_FALLBACK=true
```

#### Full CrewAI Deployment (100% rollout)
```bash
export CREWAI_ENABLED=true
export CREWAI_ROLLOUT_PERCENTAGE=100
export CREWAI_MONITORING=true
```

## 🚀 Deployment Strategy

### Phase 1: Initial Testing (Week 1)
- Set `CREWAI_ROLLOUT_PERCENTAGE=5`
- Monitor quality metrics and error rates
- Validate A/B testing consistency
- Ensure fallback mechanisms work

### Phase 2: Gradual Increase (Weeks 2-4)
- Increase rollout: 5% → 10% → 25% → 50%
- Monitor performance comparison metrics
- Adjust quality thresholds based on data
- Document any issues and resolutions

### Phase 3: Full Deployment (Week 5+)
- Increase to 75% → 90% → 100%
- Maintain monitoring for ongoing optimization
- Consider disabling fallback once stable
- Archive performance comparison data

## 📊 Performance Monitoring

### Metrics Tracked

1. **Quality Scores**: Average story quality (0-10 scale)
2. **Processing Time**: Generation time per episode
3. **Success Rate**: Percentage of successful generations
4. **Error Rate**: Percentage of failed generations
5. **Story Count**: Number of stories generated per episode

### Quality Score Calculation

```python
# Quality factors (max 10 points):
# - Required fields present (3 points)
# - Content length adequate (2 points)
# - Enhanced fields populated (2 points)
# - Family focus elements (2 points)
# - Overall completeness (1 point)
```

### Automatic Rollback Triggers

- Quality score below threshold (default: 7.0)
- Error rate above threshold (default: 10%)
- Minimum 5 sessions required for rollback decision

## 🔄 A/B Testing Framework

### Consistent Assignment
- Uses MD5 hash of `{seed}_{episode_id}` for deterministic assignment
- Same episode always gets same generator (CrewAI vs SuperPrompt)
- Enables reliable performance comparison

### Testing Scenarios
```python
# Episode "abc123" with 50% rollout
hash_input = "investingdojo_abc123"
hash_value = md5(hash_input) % 100
use_crewai = hash_value < 50  # Consistent result
```

## 🛠️ Integration Usage

### Drop-in Replacement
```python
# Before (existing code)
from automation.story_generator import StoryGenerator
generator = StoryGenerator(api_key, superprompt_path)

# After (with integration)
from automation.crewai_integration import create_integrated_story_generator
generator = create_integrated_story_generator(api_key, superprompt_path)

# Interface remains identical - no code changes needed!
stories = generator.generate_stories_from_transcript(transcript, metadata)
```

### Factory Pattern Usage
```python
from automation.crewai_integration import StoryGeneratorFactory

# Create generator based on configuration
generator = StoryGeneratorFactory.create_story_generator(
    api_key=api_key,
    superprompt_path=superprompt_path,
    config={'crewai_enabled': True, 'rollout_percentage': 25}
)
```

### Advanced Configuration
```python
from automation.crewai_integration import IntegratedStoryGenerator

config = {
    'crewai_enabled': True,
    'rollout_percentage': 50,
    'ab_testing_enabled': True,
    'quality_threshold': 8.0,
    'auto_fallback': True,
    'monitoring_enabled': True
}

generator = IntegratedStoryGenerator(api_key, superprompt_path, config)
```

## 📈 Monitoring and Analytics

### Performance Reports
```python
# Get comprehensive performance report
report = generator.get_performance_report()

# Key metrics:
# - Quality improvement: CrewAI vs SuperPrompt
# - Time difference: Processing speed comparison
# - Error rate difference: Reliability comparison
# - Recommendations: Automated suggestions
```

### Log Files
- `logs/crewai_integration/integration_YYYYMMDD.log`: Daily integration logs
- `logs/crewai_metrics/performance_metrics.json`: Historical performance data
- `logs/crewai_debug/`: Detailed CrewAI workflow outputs

### Metrics Dashboard Data
```json
{
  "summary": {
    "crewai": {
      "count": 150,
      "avg_quality": 8.7,
      "avg_time": 45.2,
      "error_rate": 2.1
    },
    "standard": {
      "count": 850,
      "avg_quality": 7.8,
      "avg_time": 18.5,
      "error_rate": 1.8
    }
  },
  "recommendation": "increase_rollout"
}
```

## 🔧 Troubleshooting

### Common Issues

#### CrewAI Not Available
```
⚠️ CrewAI enabled but not available
```
**Solution**: Install CrewAI dependencies or disable with `CREWAI_ENABLED=false`

#### High Error Rate
```
⚠️ CrewAI error rate above threshold: 15.2% > 10.0%
```
**Solution**: Check API limits, reduce rollout percentage, or investigate specific errors

#### Quality Below Threshold
```
⚠️ CrewAI quality below threshold: 6.5 < 7.0
```
**Solution**: Review agent prompts, adjust quality threshold, or reduce rollout

### Debug Mode
```bash
export CREWAI_MONITORING=true
export PYTHONPATH=.
python automation/test_crewai_integration.py
```

### Manual Fallback
```python
# Force standard generator
os.environ['CREWAI_ENABLED'] = 'false'

# Or set rollout to 0
os.environ['CREWAI_ROLLOUT_PERCENTAGE'] = '0'
```

## 🧪 Testing

### Run Integration Tests
```bash
# Comprehensive test suite
python automation/test_crewai_integration.py

# Expected output:
# ✅ Configuration System test PASSED
# ✅ Factory Pattern test PASSED
# ✅ Performance Monitoring test PASSED
# ✅ Integrated Generator test PASSED
# ✅ Backward Compatibility test PASSED
# ✅ Fallback Behavior test PASSED
```

### Test Scenarios Covered
1. **Configuration System**: Environment variable handling
2. **Factory Pattern**: Generator selection logic
3. **Performance Monitoring**: Metrics collection and analysis
4. **Integrated Generator**: Core functionality
5. **Backward Compatibility**: Interface consistency
6. **Fallback Behavior**: Error handling and recovery

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Run integration test suite (`python automation/test_crewai_integration.py`)
- [ ] Verify all tests pass (6/6)
- [ ] Set appropriate environment variables
- [ ] Start with low rollout percentage (5-10%)
- [ ] Ensure monitoring is enabled

### Post-Deployment
- [ ] Monitor error rates and quality scores
- [ ] Check log files for issues
- [ ] Validate A/B testing consistency
- [ ] Review performance comparison metrics
- [ ] Adjust rollout percentage based on results

### Rollback Plan
1. Set `CREWAI_ENABLED=false` for immediate disable
2. Or set `CREWAI_ROLLOUT_PERCENTAGE=0` for gradual disable
3. Monitor logs to confirm fallback to SuperPrompt
4. Investigate issues before re-enabling

## 🔮 Future Enhancements

### Planned Features
- **Dynamic Rollout**: Automatic percentage adjustment based on performance
- **Custom Quality Metrics**: Domain-specific quality scoring
- **Multi-Model Support**: Integration with additional AI models
- **Real-time Dashboard**: Web interface for monitoring and control

### Optimization Opportunities
- **Caching**: Cache successful generations for similar content
- **Parallel Processing**: Run both generators simultaneously for comparison
- **Smart Routing**: Route episodes to optimal generator based on content type

## 📞 Support

### Getting Help
1. Check logs in `logs/crewai_integration/`
2. Run diagnostic test: `python automation/test_crewai_integration.py`
3. Review performance metrics in `logs/crewai_metrics/`
4. Consult troubleshooting section above

### Key Files
- `automation/crewai_integration.py`: Main integration layer
- `automation/test_crewai_integration.py`: Comprehensive test suite
- `automation/crew_ai_story_generator.py`: 9-agent CrewAI implementation
- `automation/story_generator.py`: Original SuperPrompt generator

---

## Summary

The CrewAI integration provides a production-ready enhancement to the existing automation system with:

✅ **Zero Risk**: 100% backward compatibility with automatic fallback  
✅ **Gradual Rollout**: Configurable percentage-based deployment  
✅ **Quality Monitoring**: Comprehensive performance comparison  
✅ **A/B Testing**: Consistent episode-based assignment  
✅ **Easy Configuration**: Environment variable driven setup  
✅ **Comprehensive Testing**: Full test suite with 6 test scenarios  

The integration is designed to enhance the existing system without any risk to current operations, providing a safe path to leverage the advanced capabilities of the 9-agent CrewAI workflow.