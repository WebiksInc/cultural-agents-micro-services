"""
Test Validator Node
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Add parent directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from nodes.agent.validator import validator_node
from states.agent_state import AgentState
import logging

logging.basicConfig(level=logging.INFO)


def test_validator_approved():
    """Test validator with a good response that should be approved."""
    
    # Sample persona
    persona = {
        "agent_type": "active",
        "persona_id": "active_25_35_casual",
        "age_group": "25-35",
        "communication_style": "casual_friendly",
        "traits": [
            "helpful and supportive",
            "uses casual language",
            "friendly tone"
        ]
    }
    
    # Create test state with a good response
    state: AgentState = {
        "recent_messages": [
            {
                "message_id": "1",
                "sender_id": "user1",
                "sender_username": "john",
                "sender_first_name": "John",
                "sender_last_name": "Doe",
                "text": "Does anyone know a good Italian restaurant around here?",
                "date": datetime.now(),
                "message_emotion": "curious",
                "sender_personality": None
            }
        ],
        "group_sentiment": "neutral, casual conversation",
        "group_metadata": {},
        "selected_persona": persona,
        "agent_type": "active",
        "agent_goal": "be helpful and engage in conversations",
        "triggers": {},
        "actions": {},
        "detected_trigger": {"id": "direct_question", "justification": "User asked a direct question"},
        "selected_action": {
            "id": "answer_question",
            "purpose": "Provide helpful answer to user's question about restaurants"
        },
        "agent_prompt": "You are a helpful group member who likes to share recommendations.",
        "generated_response": "Yeah I know a great spot! Luigi's on Main Street has amazing pasta.",
        "styled_response": "yeah i know a great spot! luigi's on main street has amazing pasta 🍝",
        "validation": None,
        "validation_feedback": None,
        "retry_count": 0,
        "current_node": "validator",
        "next_node": None
    }
    
    print("=" * 50)
    print("TEST 1: VALIDATOR - GOOD RESPONSE")
    print("=" * 50)
    
    print("\n--- Styled Response ---")
    print(state['styled_response'])
    
    print("\n--- Action Purpose ---")
    print(state['selected_action']['purpose'])
    
    print("\n--- Running Validator... ---")
    validator_node(state)
    
    print("\n--- Validation Result ---")
    validation = state.get('validation')
    if validation:
        print(f"Approved: {validation.get('approved')}")
        if not validation.get('approved'):
            print(f"Explanation: {validation.get('explanation')}")
        print(f"Retry Count: {state.get('retry_count')}")
    else:
        print("ERROR: No validation result")
    
    print("\n" + "=" * 50)


def test_validator_rejected():
    """Test validator with a bad response that should be rejected."""
    
    # Sample persona
    persona = {
        "agent_type": "active",
        "persona_id": "active_25_35_casual",
        "age_group": "25-35",
        "communication_style": "casual_friendly",
        "traits": [
            "helpful and supportive",
            "uses casual language",
            "friendly tone"
        ]
    }
    
    # Create test state with a bad response (doesn't answer the question)
    state: AgentState = {
        "recent_messages": [
            {
                "message_id": "1",
                "sender_id": "user1",
                "sender_username": "john",
                "sender_first_name": "John",
                "sender_last_name": "Doe",
                "text": "Does anyone know a good Italian restaurant around here?",
                "date": datetime.now(),
                "message_emotion": "curious",
                "sender_personality": None
            }
        ],
        "group_sentiment": "neutral, casual conversation",
        "group_metadata": {},
        "selected_persona": persona,
        "agent_type": "active",
        "agent_goal": "be helpful and engage in conversations",
        "triggers": {},
        "actions": {},
        "detected_trigger": {"id": "direct_question", "justification": "User asked a direct question"},
        "selected_action": {
            "id": "answer_question",
            "purpose": "Provide helpful answer to user's question about restaurants"
        },
        "agent_prompt": "You are a helpful group member who likes to share recommendations.",
        "generated_response": "I love pizza! What's your favorite food?",
        "styled_response": "i love pizza! what's your favorite food? 🍕",
        "validation": None,
        "validation_feedback": None,
        "retry_count": 0,
        "current_node": "validator",
        "next_node": None
    }
    
    print("\n\n" + "=" * 50)
    print("TEST 2: VALIDATOR - BAD RESPONSE (doesn't answer)")
    print("=" * 50)
    
    print("\n--- Styled Response ---")
    print(state['styled_response'])
    
    print("\n--- Action Purpose ---")
    print(state['selected_action']['purpose'])
    
    print("\n--- Problem ---")
    print("Response doesn't answer the question about Italian restaurants")
    
    print("\n--- Running Validator... ---")
    validator_node(state)
    
    print("\n--- Validation Result ---")
    validation = state.get('validation')
    if validation:
        print(f"Approved: {validation.get('approved')}")
        if not validation.get('approved'):
            print(f"Explanation: {validation.get('explanation')}")
        print(f"Retry Count: {state.get('retry_count')}")
        print(f"Validation Feedback: {state.get('validation_feedback')}")
    else:
        print("ERROR: No validation result")
    
    print("\n" + "=" * 50)


def test_validator_max_retries():
    """Test validator behavior when max retries is reached."""
    
    # Sample persona
    persona = {
        "agent_type": "troll",
        "persona_id": "troll_18_25_casual",
        "age_group": "18-25",
        "communication_style": "playful_chaotic"
    }
    
    # Create test state with retry_count already at max
    state: AgentState = {
        "recent_messages": [],
        "group_sentiment": "neutral",
        "group_metadata": {},
        "selected_persona": persona,
        "agent_type": "troll",
        "agent_goal": "add humor",
        "triggers": {},
        "actions": {},
        "detected_trigger": {"id": "opportunity_chaos"},
        "selected_action": {
            "id": "make_joke",
            "purpose": "Add humor to conversation"
        },
        "agent_prompt": "You are a playful troll.",
        "generated_response": "Random nonsense here",
        "styled_response": "random nonsense here lol",
        "validation": None,
        "validation_feedback": None,
        "retry_count": 3,  # Already at max
        "current_node": "validator",
        "next_node": None
    }
    
    print("\n\n" + "=" * 50)
    print("TEST 3: VALIDATOR - MAX RETRIES REACHED")
    print("=" * 50)
    
    print("\n--- Styled Response ---")
    print(state['styled_response'])
    
    print(f"\n--- Retry Count: {state['retry_count']} (at max) ---")
    
    print("\n--- Running Validator... ---")
    validator_node(state)
    
    print("\n--- Validation Result ---")
    validation = state.get('validation')
    if validation:
        print(f"Approved: {validation.get('approved')} (should auto-approve)")
        print(f"Retry Count After: {state.get('retry_count')} (should be reset to 0)")
    else:
        print("ERROR: No validation result")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    # Run all test cases
    test_validator_approved()
    test_validator_rejected()
    test_validator_max_retries()
