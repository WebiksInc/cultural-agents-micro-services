"""
Test file for Trigger Analysis Node

This test demonstrates how the trigger analysis node works with sample data.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to Python path so we can import from langgraph
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from nodes.agent.trigger_analysis import trigger_analysis_node
from utils import load_json_file

# Load environment variables from .env file
load_dotenv()

# Load triggers and actions for active agent
triggers_path = project_root / "triggers" / "active" / "active_triggers.json"
triggers = load_json_file(triggers_path)

# Sample state with test messages
test_state = {
    'agent_type': 'active',
    'agent_goal': 'Keep the group engaged and steer discussions towards technology and innovation topics',
    'selected_persona': {
        'name': 'TechBot',
        'username': 'techbot_ai',
        'role': 'Active discussion facilitator'
    },
    'triggers': triggers,
    'recent_messages': [
        {
            'message_id': 'msg_001',
            'sender_id': 'user_alice',
            'sender_username': 'alice_tech',
            'sender_first_name': 'Alice',
            'sender_last_name': 'Smith',
            'text': 'Has anyone seen the new Apple event?',
            'date': datetime(2025, 11, 11, 14, 0, 0),
            'message_emotion': {'emotion': 'neutral', 'justification': 'Simple question'},
            'sender_personality': None
        },
        {
            'message_id': 'msg_002',
            'sender_id': 'user_bob',
            'sender_username': 'bob_dev',
            'sender_first_name': 'Bob',
            'sender_last_name': 'Johnson',
            'text': 'Yeah, nothing special this year.',
            'date': datetime(2025, 11, 11, 14, 2, 0),
            'message_emotion': {'emotion': 'sadness', 'justification': 'Disappointed tone'},
            'sender_personality': None
        },
        {
            'message_id': 'msg_003',
            'sender_id': 'user_charlie',
            'sender_username': 'charlie_codes',
            'sender_first_name': 'Charlie',
            'sender_last_name': 'Brown',
            'text': 'ok',
            'date': datetime(2025, 11, 11, 14, 5, 0),
            'message_emotion': {'emotion': 'neutral', 'justification': 'Disengaged response'},
            'sender_personality': None
        }
    ],
    'group_metadata': {
        'name': 'Tech Enthusiasts',
        'id': 'group_123',
        'members': 50,
        'topic': 'Technology and Innovation'
    },
    'group_sentiment': 'The conversation is losing momentum with short, disengaged responses.',
    'detected_trigger': None,
    'selected_action': None,
    'agent_prompt': '',
    'generated_response': None,
    'styled_response': None,
    'validation': None,
    'current_node': None,
    'next_node': None
}

def main():
    print("=" * 80)
    print("TESTING TRIGGER ANALYSIS NODE")
    print("=" * 80)
    print()
    
    print("Agent Configuration:")
    print(f"  Name: {test_state['selected_persona']['name']}")
    print(f"  Type: {test_state['agent_type']}")
    print(f"  Goal: {test_state['agent_goal']}")
    print()
    
    print("Recent Conversation:")
    for msg in test_state['recent_messages']:
        emotion = msg.get('message_emotion', {})
        emotion_str = emotion.get('emotion', 'N/A') if isinstance(emotion, dict) else str(emotion)
        print(f"  [{msg['date'].strftime('%H:%M')}] {msg['sender_username']} [{emotion_str}]: {msg['text']}")
    print()
    
    print("Available Triggers:")
    for trigger in test_state['triggers']['triggers']:
        print(f"  - {trigger['id']}: {trigger['description']}")
    print()
    
    print("-" * 80)
    print("Running Trigger Analysis...")
    print("-" * 80)
    print()
    
    # Run the trigger analysis node
    try:
        trigger_analysis_node(test_state)
        
        print()
        print("=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        print()
        
        detected = test_state.get('detected_trigger', {})
        print("Detected Trigger:")
        print(f"  ID: {detected.get('id', 'N/A')}")
        print(f"  Justification: {detected.get('justification', 'N/A')}")
        print()
        
        # Show suggested actions for this trigger
        trigger_id = detected.get('id')
        for trigger in test_state['triggers']['triggers']:
            if trigger['id'] == trigger_id:
                print(f"Suggested Actions for '{trigger_id}':")
                suggested = trigger.get('suggested_actions', [])
                if suggested:
                    for action in suggested:
                        print(f"  - {action}")
                else:
                    print("  (No actions suggested)")
                break
        print()
        
        print("=" * 80)
        print("TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
    except Exception as e:
        print()
        print("=" * 80)
        print("ERROR DURING TEST")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
