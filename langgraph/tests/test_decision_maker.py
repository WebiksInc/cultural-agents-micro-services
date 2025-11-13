"""
Test file for Decision Maker Node

This test demonstrates how the decision maker node works with sample data.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to Python path so we can import from langgraph
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from nodes.agent.decision_maker import decision_maker_node
from utils import load_json_file

# Load environment variables from .env file
load_dotenv()

# Load triggers and actions for active agent
triggers_path = project_root / "triggers" / "active" / "active_triggers.json"
actions_path = project_root / "actions" / "active" / "active_actions.json"
triggers = load_json_file(triggers_path)
actions = load_json_file(actions_path)

# Sample state with detected trigger from trigger analysis
test_state = {
    'agent_type': 'active',
    'agent_goal': 'Keep the group engaged and steer discussions towards technology and innovation topics',
    'selected_persona': {
        'name': 'TechBot',
        'username': 'techbot_ai',
        'role': 'Active discussion facilitator'
    },
    'triggers': triggers,
    'actions': actions,
    'detected_trigger': {
        'id': 'discussion_faltering',
        'justification': 'The conversation has become sparse with short, disengaged responses like "ok" and "nothing special". The energy and depth of the discussion have clearly diminished after an initial question about the Apple event.'
    },
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
    'group_sentiment': 'The conversation is losing momentum with short, disengaged responses. There is a sense of disappointment and lack of enthusiasm about the Apple event topic.',
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
    print("TESTING DECISION MAKER NODE")
    print("=" * 80)
    print()
    
    print("Agent Configuration:")
    print(f"  Name: {test_state['selected_persona']['name']}")
    print(f"  Type: {test_state['agent_type']}")
    print(f"  Goal: {test_state['agent_goal']}")
    print()
    
    print("Detected Trigger:")
    trigger = test_state['detected_trigger']
    print(f"  ID: {trigger['id']}")
    print(f"  Justification: {trigger['justification']}")
    print()
    
    # Show suggested actions for this trigger
    trigger_id = trigger['id']
    suggested_action_ids = []
    for t in test_state['triggers']['triggers']:
        if t['id'] == trigger_id:
            suggested_action_ids = t.get('suggested_actions', [])
            print(f"Suggested Actions for '{trigger_id}':")
            for action_id in suggested_action_ids:
                for action in test_state['actions']['actions']:
                    if action['id'] == action_id:
                        print(f"  - {action['id']}: {action['description']}")
                        break
            break
    print()
    
    print("Group Sentiment:")
    print(f"  {test_state['group_sentiment']}")
    print()
    
    print("Recent Conversation:")
    for msg in test_state['recent_messages']:
        emotion = msg.get('message_emotion', {})
        emotion_str = emotion.get('emotion', 'N/A') if isinstance(emotion, dict) else str(emotion)
        print(f"  [{msg['date'].strftime('%H:%M')}] {msg['sender_username']} [{emotion_str}]: {msg['text']}")
    print()
    
    print("-" * 80)
    print("Running Decision Maker...")
    print("-" * 80)
    print()
    
    # Run the decision maker node
    try:
        decision_maker_node(test_state)
        
        print()
        print("=" * 80)
        print("DECISION COMPLETE")
        print("=" * 80)
        print()
        
        selected = test_state.get('selected_action')
        if selected:
            print("Selected Action:")
            print(f"  ID: {selected.get('id', 'N/A')}")
            print(f"  Purpose: {selected.get('purpose', 'N/A')}")
            print()
            
            # Show full action details
            action_id = selected.get('id')
            for action in test_state['actions']['actions']:
                if action['id'] == action_id:
                    print(f"Action Details:")
                    print(f"  Description: {action.get('description', 'N/A')}")
                    print(f"  Purpose: {action.get('purpose', 'N/A')}")
                    break
        else:
            print("No action selected (neutral or error)")
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
