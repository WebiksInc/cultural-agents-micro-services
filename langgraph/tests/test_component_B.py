"""
Test file for Component B - Emotion/Sentiment Analysis Node

This test demonstrates how Component B works with sample data.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to Python path so we can import from nodes
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from nodes.supervisor.component_B import emotion_analysis_node

# Load environment variables from .env file
load_dotenv()

# Set up environment variable for model (you can change this)
os.environ['COMPONENT_B_MODEL'] = 'gpt-5-nano'

# Sample state with test messages
test_state = {
    'group_metadata': {
        'name': 'Tech Enthusiasts',
        'id': 'group_123',
        'members': 50,
        'topic': 'Technology and Innovation'
    },
    'recent_messages': [
        {
            'message_id': 'msg_001',
            'sender_id': 'user_alice',
            'sender_username': 'alice_tech',
            'sender_first_name': 'Alice',
            'sender_last_name': 'Smith',
            'text': 'I just got the new iPhone! So excited!',
            'date': datetime(2025, 11, 11, 10, 0, 0),
            'message_emotion': None,  # Unclassified
            'sender_personality': None
        },
        {
            'message_id': 'msg_002',
            'sender_id': 'user_bob',
            'sender_username': 'bob_dev',
            'sender_first_name': 'Bob',
            'sender_last_name': 'Johnson',
            'text': 'Really? Another iPhone? They never innovate anymore. Just the same thing every year.',
            'date': datetime(2025, 11, 11, 10, 5, 0),
            'message_emotion': None,  # Unclassified
            'sender_personality': None
        },
        {
            'message_id': 'msg_003',
            'sender_id': 'user_charlie',
            'sender_username': 'charlie_codes',
            'sender_first_name': 'Charlie',
            'sender_last_name': 'Brown',
            'text': 'Has anyone tried the new AI coding assistant? I heard it can write entire functions.',
            'date': datetime(2025, 11, 11, 10, 10, 0),
            'message_emotion': None,  # Unclassified
            'sender_personality': None
        },
        {
            'message_id': 'msg_004',
            'sender_id': 'user_diana',
            'sender_username': 'diana_design',
            'sender_first_name': 'Diana',
            'sender_last_name': 'Martinez',
            'text': 'I tried it last week. Honestly, I\'m worried it might replace junior developers soon.',
            'date': datetime(2025, 11, 11, 10, 15, 0),
            'message_emotion': None,  # Unclassified
            'sender_personality': None
        }
    ],
    'group_sentiment': None,
    'selected_actions': [],
    'execution_queue': [],
    'current_nodes': None,
    'next_nodes': None
}

def main():
    print("=" * 80)
    print("TESTING COMPONENT B - EMOTION/SENTIMENT ANALYSIS")
    print("=" * 80)
    print()
    
    print("Initial State:")
    print(f"Group: {test_state['group_metadata']['name']}")
    print(f"Topic: {test_state['group_metadata']['topic']}")
    print(f"Number of messages: {len(test_state['recent_messages'])}")
    print()
    
    print("Messages (before analysis):")
    for msg in test_state['recent_messages']:
        print(f"  [{msg['message_id']}] {msg['sender_username']}: {msg['text']}")
        print(f"    Emotion: {msg['message_emotion']}")
    print()
    
    print("-" * 80)
    print("Running Component B...")
    print("-" * 80)
    print()
    
    # Run the emotion analysis node
    try:
        result = emotion_analysis_node(test_state)
        
        # Update test_state with returned values (simulating LangGraph behavior)
        if result:
            test_state.update(result)
        
        print()
        print("=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        print()
        
        print("Messages (after analysis):")
        for msg in test_state['recent_messages']:
            print(f"  [{msg['message_id']}] {msg['sender_username']}: {msg['text']}")
            emotion = msg.get('message_emotion', {})
            if isinstance(emotion, dict):
                print(f"    Emotion: {emotion.get('emotion', 'N/A')}")
                print(f"    Justification: {emotion.get('justification', 'N/A')}")
            else:
                print(f"    Emotion: {emotion}")
            print()
        
        print("Group Sentiment:")
        print(f"  {test_state.get('group_sentiment', 'N/A')}")
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
