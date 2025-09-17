#!/usr/bin/env python3
"""
JSON IMPORT VALIDATION SCRIPT
Tests both SuperPrompt and CrewAI JSON outputs for database compatibility
"""

import json
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_json_structure(json_file: Path) -> Optional[List[Dict[str, Any]]]:
    """Validate JSON file structure and return parsed data"""
    try:
        logger.info(f"📄 Reading JSON file: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"📊 File size: {len(content)} characters")
        
        # Try to parse JSON
        try:
            data = json.loads(content)
            logger.info(f"✅ JSON parsing successful")
            
            if isinstance(data, list):
                logger.info(f"📋 Found {len(data)} stories in array format")
                return data
            elif isinstance(data, dict):
                if 'investing-dojo-stories' in data:
                    stories = data['investing-dojo-stories']
                    logger.info(f"📋 Found {len(stories)} stories in 'investing-dojo-stories' key")
                    return stories
                else:
                    logger.warning(f"⚠️ Dictionary format but no 'investing-dojo-stories' key found")
                    logger.info(f"Available keys: {list(data.keys())}")
                    return None
            else:
                logger.error(f"❌ Unexpected data type: {type(data)}")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {str(e)}")
            logger.error(f"Error at line {e.lineno}, column {e.colno}")
            
            # Try to find the problematic area
            lines = content.split('\n')
            if e.lineno <= len(lines):
                problem_line = lines[e.lineno - 1]
                logger.error(f"Problem line {e.lineno}: {problem_line}")
                
                # Show context around the error
                start_line = max(0, e.lineno - 3)
                end_line = min(len(lines), e.lineno + 2)
                logger.error("Context:")
                for i in range(start_line, end_line):
                    marker = " >>> " if i == e.lineno - 1 else "     "
                    logger.error(f"{marker}Line {i+1}: {lines[i]}")
            
            return None
            
    except Exception as e:
        logger.error(f"❌ File reading error: {str(e)}")
        return None

def validate_story_fields(story: Dict[str, Any], story_index: int) -> List[str]:
    """Validate required fields for a single story"""
    errors = []
    
    # Required fields based on database schema
    required_fields = [
        'id', 'title', 'summary', 'full_content', 'content_type',
        'belt_levels', 'difficulty_level', 'time_required'
    ]
    
    for field in required_fields:
        if field not in story:
            errors.append(f"Missing required field: {field}")
        elif story[field] is None or story[field] == "":
            errors.append(f"Empty required field: {field}")
    
    # Validate ENUM fields
    valid_enums = {
        'belt_levels': ['white-belt', 'yellow-belt', 'orange-belt', 'green-belt', 'blue-belt', 'brown-belt', 'black-belt'],
        'content_type': ['curriculum-war-story', 'ai-breakthrough', 'systematic-strategy', 'family-wealth-builder',
                        'mastery-technique', 'mindset-hack', 'research-method', 'risk-lesson', 'epic-curriculum-fail',
                        'belt-progression-moment', 'ai-integration-guide', 'generational-wealth-wisdom'],
        'difficulty_level': ['foundational', 'intermediate-skill', 'advanced-mastery'],
        'time_required': ['5-minutes', '10-minutes', '15-minutes', '30-minutes', '1-hour', '2-hours',
                         'ongoing', 'varies', 'immediate', 'quick-read', 'deep-dive']
    }
    
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
                    errors.append(f"{field}: '{value}' not in valid values")
    
    return errors

def validate_stories_data(stories: List[Dict[str, Any]], source_name: str) -> Dict[str, Any]:
    """Validate all stories and return summary"""
    logger.info(f"🔍 Validating {len(stories)} stories from {source_name}")
    
    validation_results = {
        'source': source_name,
        'total_stories': len(stories),
        'valid_stories': 0,
        'stories_with_errors': 0,
        'total_errors': 0,
        'error_details': [],
        'field_statistics': {},
        'enum_validation': {}
    }
    
    # Track field presence
    field_counts = {}
    
    for i, story in enumerate(stories):
        story_errors = validate_story_fields(story, i)
        
        if story_errors:
            validation_results['stories_with_errors'] += 1
            validation_results['total_errors'] += len(story_errors)
            validation_results['error_details'].append({
                'story_index': i,
                'story_id': story.get('id', 'unknown'),
                'story_title': story.get('title', 'unknown'),
                'errors': story_errors
            })
        else:
            validation_results['valid_stories'] += 1
        
        # Count field presence
        for field in story.keys():
            field_counts[field] = field_counts.get(field, 0) + 1
    
    validation_results['field_statistics'] = field_counts
    
    return validation_results

def compare_outputs(superprompt_results: Dict[str, Any], crewai_results: Dict[str, Any]):
    """Compare SuperPrompt vs CrewAI outputs"""
    logger.info("🔄 Comparing SuperPrompt vs CrewAI outputs")
    
    comparison = {
        'superprompt': {
            'stories': superprompt_results['total_stories'],
            'valid': superprompt_results['valid_stories'],
            'errors': superprompt_results['total_errors']
        },
        'crewai': {
            'stories': crewai_results['total_stories'],
            'valid': crewai_results['valid_stories'],
            'errors': crewai_results['total_errors']
        }
    }
    
    logger.info(f"📊 SuperPrompt: {comparison['superprompt']['stories']} stories, {comparison['superprompt']['valid']} valid, {comparison['superprompt']['errors']} errors")
    logger.info(f"📊 CrewAI: {comparison['crewai']['stories']} stories, {comparison['crewai']['valid']} valid, {comparison['crewai']['errors']} errors")
    
    # Determine winner
    if comparison['superprompt']['errors'] < comparison['crewai']['errors']:
        logger.info("🏆 SuperPrompt has fewer validation errors")
    elif comparison['crewai']['errors'] < comparison['superprompt']['errors']:
        logger.info("🏆 CrewAI has fewer validation errors")
    else:
        logger.info("🤝 Both approaches have equal validation errors")
    
    return comparison

def main():
    """Main validation function"""
    logger.info("🧪 Starting JSON Import Validation")
    logger.info("=" * 50)
    
    # File paths
    superprompt_file = Path("logs/superprompt_output_comparison.json")
    crewai_file = Path("logs/crewai_output_comparison.json")
    
    # Validate both files exist
    if not superprompt_file.exists():
        logger.error(f"❌ SuperPrompt file not found: {superprompt_file}")
        return False
    
    if not crewai_file.exists():
        logger.error(f"❌ CrewAI file not found: {crewai_file}")
        return False
    
    # Validate SuperPrompt output
    logger.info("\n=== SUPERPROMPT VALIDATION ===")
    superprompt_stories = validate_json_structure(superprompt_file)
    
    if superprompt_stories is None:
        logger.error("❌ SuperPrompt JSON validation failed")
        superprompt_results = None
    else:
        superprompt_results = validate_stories_data(superprompt_stories, "SuperPrompt")
    
    # Validate CrewAI output
    logger.info("\n=== CREWAI VALIDATION ===")
    crewai_stories = validate_json_structure(crewai_file)
    
    if crewai_stories is None:
        logger.error("❌ CrewAI JSON validation failed")
        crewai_results = None
    else:
        crewai_results = validate_stories_data(crewai_stories, "CrewAI")
    
    # Compare results
    if superprompt_results and crewai_results:
        logger.info("\n=== COMPARISON ===")
        comparison = compare_outputs(superprompt_results, crewai_results)
        
        # Show detailed errors if any
        if superprompt_results['total_errors'] > 0:
            logger.info("\n📋 SuperPrompt Errors:")
            for error_detail in superprompt_results['error_details']:
                logger.info(f"  Story {error_detail['story_index']}: {error_detail['story_id']}")
                for error in error_detail['errors']:
                    logger.info(f"    - {error}")
        
        if crewai_results['total_errors'] > 0:
            logger.info("\n📋 CrewAI Errors:")
            for error_detail in crewai_results['error_details']:
                logger.info(f"  Story {error_detail['story_index']}: {error_detail['story_id']}")
                for error in error_detail['errors']:
                    logger.info(f"    - {error}")
    
    # Summary
    logger.info("\n=== SUMMARY ===")
    if superprompt_results:
        logger.info(f"✅ SuperPrompt: {superprompt_results['valid_stories']}/{superprompt_results['total_stories']} stories valid")
    else:
        logger.info("❌ SuperPrompt: JSON parsing failed")
    
    if crewai_results:
        logger.info(f"✅ CrewAI: {crewai_results['valid_stories']}/{crewai_results['total_stories']} stories valid")
    else:
        logger.info("❌ CrewAI: JSON parsing failed")
    
    # Production readiness assessment
    logger.info("\n=== PRODUCTION READINESS ===")
    if superprompt_results and crewai_results:
        if superprompt_results['total_errors'] == 0 and crewai_results['total_errors'] == 0:
            logger.info("🚀 Both systems are production ready!")
        elif superprompt_results['total_errors'] == 0:
            logger.info("🚀 SuperPrompt is production ready!")
            logger.info("⚠️ CrewAI needs fixes before production")
        elif crewai_results['total_errors'] == 0:
            logger.info("🚀 CrewAI is production ready!")
            logger.info("⚠️ SuperPrompt needs fixes before production")
        else:
            logger.info("⚠️ Both systems need fixes before production")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)