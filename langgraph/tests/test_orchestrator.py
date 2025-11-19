"""
Test Agent Orchestrator Node

Tests the routing logic for various scenarios.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from nodes.agent.orchestrator import orchestrator_node, END
from states.agent_state import AgentState
import logging

logging.basicConfig(level=logging.INFO)


def test_entry_point():
    """Test orchestrator entry point routing."""
    print("=" * 70)
    print("TEST 1: ENTRY POINT - Should route to trigger_analysis")
    print("=" * 70)
    
    state: AgentState = {
        "recent_messages": [],
        "group_sentiment": "",
        "group_metadata": {},
        "selected_persona": {},
        "agent_type": "troll",
        "agent_goal": "add humor",
        "triggers": {},
        "actions": {},
        "detected_trigger": None,
        "selected_action": None,
        "agent_prompt": "",
        "generated_response": None,
        "styled_response": None,
        "validation": None,
        "validation_feedback": None,
        "retry_count": 0,
        "current_node": None,
        "next_node": None
    }
    
    orchestrator_node(state)
    
    print(f"Current node: {state['current_node']}")
    print(f"Next node: {state['next_node']}")
    assert state['next_node'] == 'trigger_analysis', "Should route to trigger_analysis"
    print("✓ PASSED\n")


def test_no_trigger_detected():
    """Test routing when no trigger is detected."""
    print("=" * 70)
    print("TEST 2: NO TRIGGER - Should route to END")
    print("=" * 70)
    
    state: AgentState = {
        "recent_messages": [],
        "group_sentiment": "",
        "group_metadata": {},
        "selected_persona": {},
        "agent_type": "troll",
        "agent_goal": "add humor",
        "triggers": {},
        "actions": {},
        "detected_trigger": None,  # No trigger
        "selected_action": None,
        "agent_prompt": "",
        "generated_response": None,
        "styled_response": None,
        "validation": None,
        "validation_feedback": None,
        "retry_count": 0,
        "current_node": "trigger_analysis",
        "next_node": None
    }
    
    orchestrator_node(state)
    
    print(f"Current node: {state['current_node']}")
    print(f"Next node: {state['next_node']}")
    print(f"Selected action: {state['selected_action']}")
    assert state['next_node'] == END, "Should route to END"
    assert state['selected_action']['status'] == 'no_action_needed', "Should mark no action needed"
    print("✓ PASSED\n")


def test_neutral_trigger():
    """Test routing when neutral trigger is detected."""
    print("=" * 70)
    print("TEST 3: NEUTRAL TRIGGER - Should route to END")
    print("=" * 70)
    
    state: AgentState = {
        "recent_messages": [],
        "group_sentiment": "",
        "group_metadata": {},
        "selected_persona": {},
        "agent_type": "troll",
        "agent_goal": "add humor",
        "triggers": {},
        "actions": {},
        "detected_trigger": {"id": "neutral", "justification": "No engagement trigger"},
        "selected_action": None,
        "agent_prompt": "",
        "generated_response": None,
        "styled_response": None,
        "validation": None,
        "validation_feedback": None,
        "retry_count": 0,
        "current_node": "trigger_analysis",
        "next_node": None
    }
    
    orchestrator_node(state)
    
    print(f"Current node: {state['current_node']}")
    print(f"Next node: {state['next_node']}")
    print(f"Selected action: {state['selected_action']}")
    assert state['next_node'] == END, "Should route to END"
    assert state['selected_action']['status'] == 'no_action_needed', "Should mark no action needed"
    print("✓ PASSED\n")


def test_trigger_to_decision():
    """Test routing from trigger analysis to decision maker."""
    print("=" * 70)
    print("TEST 4: TRIGGER DETECTED - Should route to decision_maker")
    print("=" * 70)
    
    state: AgentState = {
        "recent_messages": [],
        "group_sentiment": "",
        "group_metadata": {},
        "selected_persona": {},
        "agent_type": "troll",
        "agent_goal": "add humor",
        "triggers": {},
        "actions": {},
        "detected_trigger": {"id": "conversation_starter", "justification": "Good topic to engage"},
        "selected_action": None,
        "agent_prompt": "",
        "generated_response": None,
        "styled_response": None,
        "validation": None,
        "validation_feedback": None,
        "retry_count": 0,
        "current_node": "trigger_analysis",
        "next_node": None
    }
    
    orchestrator_node(state)
    
    print(f"Current node: {state['current_node']}")
    print(f"Next node: {state['next_node']}")
    assert state['next_node'] == 'decision_maker', "Should route to decision_maker"
    print("✓ PASSED\n")


def test_validation_approved():
    """Test routing when validation approves the response."""
    print("=" * 70)
    print("TEST 5: VALIDATION APPROVED - Should route to END")
    print("=" * 70)
    
    state: AgentState = {
        "recent_messages": [],
        "group_sentiment": "",
        "group_metadata": {},
        "selected_persona": {},
        "agent_type": "troll",
        "agent_goal": "add humor",
        "triggers": {},
        "actions": {},
        "detected_trigger": {"id": "conversation_starter"},
        "selected_action": {"id": "casual_comment", "purpose": "Add to conversation"},
        "agent_prompt": "",
        "generated_response": "That's interesting!",
        "styled_response": "lol that's pretty interesting ngl 😄",
        "validation": {"approved": True, "styled_response": "lol that's pretty interesting ngl 😄"},
        "validation_feedback": None,
        "retry_count": 0,
        "current_node": "validator",
        "next_node": None
    }
    
    orchestrator_node(state)
    
    print(f"Current node: {state['current_node']}")
    print(f"Next node: {state['next_node']}")
    print(f"Selected action status: {state['selected_action'].get('status')}")
    print(f"Retry count reset: {state['retry_count']}")
    assert state['next_node'] == END, "Should route to END"
    assert state['selected_action']['status'] == 'success', "Should mark success"
    assert state['retry_count'] == 0, "Should reset retry count"
    print("✓ PASSED\n")


def test_validation_failed_retry():
    """Test routing when validation fails but retries remain."""
    print("=" * 70)
    print("TEST 6: VALIDATION FAILED - Should retry (route to text_generator)")
    print("=" * 70)
    
    state: AgentState = {
        "recent_messages": [],
        "group_sentiment": "",
        "group_metadata": {},
        "selected_persona": {},
        "agent_type": "troll",
        "agent_goal": "add humor",
        "triggers": {},
        "actions": {},
        "detected_trigger": {"id": "conversation_starter"},
        "selected_action": {"id": "casual_comment", "purpose": "Add to conversation"},
        "agent_prompt": "",
        "generated_response": "That's interesting!",
        "styled_response": "That is most intriguing indeed.",
        "validation": {
            "approved": False,
            "explanation": "Response doesn't match casual persona",
            "styled_response": "That is most intriguing indeed."
        },
        "validation_feedback": "Response doesn't match casual persona",
        "retry_count": 1,
        "current_node": "validator",
        "next_node": None
    }
    
    orchestrator_node(state)
    
    print(f"Current node: {state['current_node']}")
    print(f"Next node: {state['next_node']}")
    print(f"Retry count: {state['retry_count']}")
    assert state['next_node'] == 'text_generator', "Should route back to text_generator"
    print("✓ PASSED\n")


def test_max_retries_reached():
    """Test routing when max retries are reached."""
    print("=" * 70)
    print("TEST 7: MAX RETRIES REACHED - Should route to END")
    print("=" * 70)
    
    state: AgentState = {
        "recent_messages": [],
        "group_sentiment": "",
        "group_metadata": {},
        "selected_persona": {},
        "agent_type": "troll",
        "agent_goal": "add humor",
        "triggers": {},
        "actions": {},
        "detected_trigger": {"id": "conversation_starter"},
        "selected_action": {"id": "casual_comment", "purpose": "Add to conversation"},
        "agent_prompt": "",
        "generated_response": "That's interesting!",
        "styled_response": "That is most intriguing indeed.",
        "validation": {
            "approved": False,
            "explanation": "Response doesn't match casual persona",
            "styled_response": "That is most intriguing indeed."
        },
        "validation_feedback": "Response doesn't match casual persona",
        "retry_count": 3,  # Max retries
        "current_node": "validator",
        "next_node": None
    }
    
    orchestrator_node(state)
    
    print(f"Current node: {state['current_node']}")
    print(f"Next node: {state['next_node']}")
    print(f"Selected action status: {state['selected_action'].get('status')}")
    print(f"Retry count reset: {state['retry_count']}")
    assert state['next_node'] == END, "Should route to END"
    assert state['selected_action']['status'] == 'max_retries_reached', "Should mark max retries"
    assert state['retry_count'] == 0, "Should reset retry count"
    print("✓ PASSED\n")


def test_error_handling():
    """Test routing when text generation fails."""
    print("=" * 70)
    print("TEST 8: TEXT GENERATION ERROR - Should route to END with error")
    print("=" * 70)
    
    state: AgentState = {
        "recent_messages": [],
        "group_sentiment": "",
        "group_metadata": {},
        "selected_persona": {},
        "agent_type": "troll",
        "agent_goal": "add humor",
        "triggers": {},
        "actions": {},
        "detected_trigger": {"id": "conversation_starter"},
        "selected_action": {"id": "casual_comment", "purpose": "Add to conversation"},
        "agent_prompt": "",
        "generated_response": None,  # Generation failed
        "styled_response": None,
        "validation": None,
        "validation_feedback": None,
        "retry_count": 0,
        "current_node": "text_generator",
        "next_node": None
    }
    
    orchestrator_node(state)
    
    print(f"Current node: {state['current_node']}")
    print(f"Next node: {state['next_node']}")
    print(f"Selected action: {state['selected_action']}")
    assert state['next_node'] == END, "Should route to END"
    assert state['selected_action']['status'] == 'error', "Should mark error"
    print("✓ PASSED\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("AGENT ORCHESTRATOR TEST SUITE")
    print("=" * 70 + "\n")
    
    test_entry_point()
    test_no_trigger_detected()
    test_neutral_trigger()
    test_trigger_to_decision()
    test_validation_approved()
    test_validation_failed_retry()
    test_max_retries_reached()
    test_error_handling()
    
    print("=" * 70)
    print("ALL TESTS PASSED! ✓")
    print("=" * 70)
