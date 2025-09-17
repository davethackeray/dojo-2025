#!/usr/bin/env python3
"""
Direct comparison script to generate JSON outputs from both SuperPrompt and CrewAI approaches
"""

import sys
import json
from datetime import datetime
import traceback

# Add current directory to path
sys.path.append('.')

def main():
    # Test data
    test_transcript = '''
This is a test podcast transcript about investing. The host discusses the importance of diversification in uncertain economic times. They mention that when experts disagree about whether we're in a recession, the best strategy is to spread investments across different asset classes like stocks, bonds, and real estate. The guest, an economist, explains that AI is disrupting traditional industries and creating new investment opportunities. The discussion covers how white-collar jobs are at risk from AI automation, but also how AI can create deflationary pressures that benefit consumers while potentially hurting corporate profits.
'''

    test_episode = {
        'id': 'test-comparison-episode',
        'title': 'Investment Strategies in Uncertain Times',
        'description': 'A discussion about diversification and AI impact on investing',
        'duration': '30:00',
        'transcript': test_transcript,
        'url': 'https://example.com/test-episode',
        'published_date': '2025-07-30'
    }

    print('=' * 60)
    print('SUPERPROMPT vs CREWAI JSON OUTPUT COMPARISON')
    print('=' * 60)
    
    # Test SuperPrompt approach
    print('\n=== GENERATING SUPERPROMPT OUTPUT ===')
    superprompt_result = None
    try:
        from story_generator import StoryGenerator
        api_key = "AIzaSyBwwqspks4SlM8ZWbPie-vMFbvDD_-ysG8"
        superprompt_path = "SuperPrompt_Optimized.md"
        superprompt_gen = StoryGenerator(api_key, superprompt_path)
        superprompt_result = superprompt_gen.generate_stories_from_transcript(test_transcript, test_episode)
        
        print('✅ SuperPrompt generation successful')
        
        # Handle both list and dict formats
        if isinstance(superprompt_result, list):
            stories_count = len(superprompt_result)
            superprompt_stories = superprompt_result
        else:
            stories_count = len(superprompt_result.get("investing-dojo-stories", []))
            superprompt_stories = superprompt_result.get("investing-dojo-stories", [])
        
        print(f'Stories generated: {stories_count}')
        
        # Save to file for detailed analysis
        with open('logs/superprompt_output_comparison.json', 'w', encoding='utf-8') as f:
            json.dump(superprompt_result, f, indent=2, ensure_ascii=False)
        
        print('SuperPrompt JSON Output:')
        output_str = json.dumps(superprompt_result, indent=2)
        print(output_str[:2000] + '...' if len(output_str) > 2000 else output_str)
        
    except Exception as e:
        print(f'❌ SuperPrompt Error: {e}')
        print(f'Traceback: {traceback.format_exc()}')

    # Test CrewAI approach
    print('\n=== GENERATING CREWAI OUTPUT ===')
    crewai_result = None
    try:
        from crew_ai_story_generator import CrewAIStoryGenerator
        api_key = "AIzaSyBwwqspks4SlM8ZWbPie-vMFbvDD_-ysG8"
        superprompt_path = "SuperPrompt_Optimized.md"
        crewai_gen = CrewAIStoryGenerator(api_key, superprompt_path)
        crewai_result = crewai_gen.generate_stories_from_transcript(test_transcript, test_episode)
        
        print('✅ CrewAI generation successful')
        
        # Handle both list and dict formats
        if isinstance(crewai_result, list):
            stories_count = len(crewai_result)
            crewai_stories = crewai_result
        else:
            stories_count = len(crewai_result.get("investing-dojo-stories", []))
            crewai_stories = crewai_result.get("investing-dojo-stories", [])
        
        print(f'Stories generated: {stories_count}')
        
        # Save to file for detailed analysis
        with open('logs/crewai_output_comparison.json', 'w', encoding='utf-8') as f:
            json.dump(crewai_result, f, indent=2, ensure_ascii=False)
        
        print('CrewAI JSON Output:')
        output_str = json.dumps(crewai_result, indent=2)
        print(output_str[:2000] + '...' if len(output_str) > 2000 else output_str)
        
    except Exception as e:
        print(f'❌ CrewAI Error: {e}')
        print(f'Traceback: {traceback.format_exc()}')

    # Comparison analysis
    print('\n=== COMPARISON ANALYSIS ===')
    if superprompt_result and crewai_result:
        print('✅ Both systems generated outputs successfully')
        
        # Compare structure - handle both list and dict formats
        if isinstance(superprompt_result, list):
            sp_stories = superprompt_result
        else:
            sp_stories = superprompt_result.get("investing-dojo-stories", [])
            
        if isinstance(crewai_result, list):
            ca_stories = crewai_result
        else:
            ca_stories = crewai_result.get("investing-dojo-stories", [])
        
        print(f'SuperPrompt stories count: {len(sp_stories)}')
        print(f'CrewAI stories count: {len(ca_stories)}')
        
        if sp_stories and ca_stories:
            sp_story = sp_stories[0]
            ca_story = ca_stories[0]
            
            print(f'\nSuperPrompt first story keys: {len(sp_story.keys())}')
            print(f'CrewAI first story keys: {len(ca_story.keys())}')
            
            # Check key differences
            sp_keys = set(sp_story.keys())
            ca_keys = set(ca_story.keys())
            
            common_keys = sp_keys & ca_keys
            sp_only = sp_keys - ca_keys
            ca_only = ca_keys - sp_keys
            
            print(f'Common keys: {len(common_keys)}')
            print(f'SuperPrompt only: {list(sp_only)[:5]}...' if len(sp_only) > 5 else f'SuperPrompt only: {list(sp_only)}')
            print(f'CrewAI only: {list(ca_only)[:5]}...' if len(ca_only) > 5 else f'CrewAI only: {list(ca_only)}')
            
            # Compare content lengths
            sp_content_len = len(sp_story.get('full_content', ''))
            ca_content_len = len(ca_story.get('full_content', ''))
            
            print(f'\nContent length comparison:')
            print(f'SuperPrompt: {sp_content_len} characters')
            print(f'CrewAI: {ca_content_len} characters')
            print(f'Difference: {abs(sp_content_len - ca_content_len)} characters')
            
    else:
        print('❌ Could not complete comparison - one or both systems failed')
    
    print('\n=== FILES SAVED ===')
    print('📁 logs/superprompt_output_comparison.json - SuperPrompt full output')
    print('📁 logs/crewai_output_comparison.json - CrewAI full output')
    print('\nYou can examine these files for detailed JSON structure comparison.')

if __name__ == '__main__':
    main()