"""
Test file for Component E.1 - Text Generator Node

This test demonstrates how the text generator creates response content.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to Python path so we can import from langgraph
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from nodes.agent.component_E1 import text_generator_node
from utils import load_json_file

# Load environment variables from .env file
load_dotenv()

# Load actions for active agent
actions_path = project_root / "actions" / "active" / "active_actions.json"
actions = load_json_file(actions_path)

# Sample agent prompt (this would normally be loaded from prompts/agents/active_prompt.txt)
agent_prompt = """You are an active, engaging member of a tech enthusiast group. Your role is to keep discussions lively and steer conversations towards technology and innovation topics. You are knowledgeable, curious, and conversational."""

# Sample state with selected action from decision maker
test_state = {
    'agent_type': 'active',
    'agent_goal': 'Keep the group engaged and steer discussions towards technology and innovation topics',
    'agent_prompt': agent_prompt,
    'selected_persona': {
        'name': 'TechBot',
        'username': 'techbot_ai',
        'age': 25,
        'interests': ['AI', 'programming', 'gadgets', 'open source'],
        'personality': 'enthusiastic, curious, helpful',
        'communication_style': 'casual, friendly, uses tech jargon occasionally'
    },
    'actions': actions,
    'selected_action': {
        'id': 'expand_discussion',
        'purpose': 'The discussion about the Apple event is losing momentum with brief, disengaged responses. Expanding on this topic with new perspectives or related information will re-energize the conversation and align with the goal of keeping the group engaged in technology discussions.'
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
    'group_sentiment': 'The conversation is losing momentum with short, disengaged responses. There is a sense of disappointment and lack of enthusiasm about the Apple event topic.',
    'generated_response': None,
    'styled_response': None,
    'validation': None
}

def main():
    print("=" * 80)
    print("TESTING TEXT GENERATOR (E.1) NODE")
    print("=" * 80)
    print()
    
    print("Agent Configuration:")
    print(f"  Name: {test_state['selected_persona']['name']}")
    print(f"  Type: {test_state['agent_type']}")
    print(f"  Goal: {test_state['agent_goal']}")
    print()
    
    print("Agent Prompt (System Message):")
    print(f"  {test_state['agent_prompt']}")
    print()
    
    print("Selected Action:")
    action = test_state['selected_action']
    print(f"  ID: {action['id']}")
    print(f"  Purpose: {action['purpose']}")
    print()
    
    print("Group Sentiment:")
    print(f"  {test_state['group_sentiment']}")
    print()
    
    print("Recent Conversation:")
    for msg in test_state['recent_messages']:
        print(f"  {msg['sender_username']}: {msg['text']}")
    print()
    
    print("-" * 80)
    print("Running Text Generator (E.1)...")
    print("-" * 80)
    print()
    
    # Run the text generator node
    try:
        text_generator_node(test_state)
        
        print()
        print("=" * 80)
        print("GENERATION COMPLETE")
        print("=" * 80)
        print()
        
        generated = test_state.get('generated_response')
        if generated:
            print("Generated Response:")
            print(f"  {generated}")
            print()
            print(f"Length: {len(generated)} characters")
        else:
            print("No response generated (error occurred)")
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
