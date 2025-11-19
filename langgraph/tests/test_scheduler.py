"""
Test Scheduler Node

Tests the scheduler's ability to queue actions and manage execution.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from nodes.supervisor.scheduler import scheduler_node, get_ready_actions, mark_action_sent
from states.supervisor_state import SupervisorState
import logging

logging.basicConfig(level=logging.INFO)


def test_empty_selected_actions():
    """Test scheduler with no actions."""
    print("=" * 70)
    print("TEST 1: EMPTY SELECTED ACTIONS")
    print("=" * 70)
    
    state: SupervisorState = {
        "recent_messages": [],
        "group_sentiment": "neutral",
        "group_metadata": {},
        "selected_actions": [],
        "execution_queue": [],
        "current_nodes": None,
        "next_nodes": None
    }
    
    result = scheduler_node(state)
    
    print(f"Execution queue: {result['execution_queue']}")
    assert result['execution_queue'] == [], "Should have empty queue"
    print("✓ PASSED\n")


def test_no_action_needed_filtered():
    """Test that neutral triggers are filtered out."""
    print("=" * 70)
    print("TEST 2: FILTER NO_ACTION_NEEDED STATUS")
    print("=" * 70)
    
    state: SupervisorState = {
        "recent_messages": [],
        "group_sentiment": "neutral",
        "group_metadata": {},
        "selected_actions": [
            {
                "agent_name": "Tamar",
                "agent_type": "active",
                "status": "no_action_needed",
                "selected_action": {"id": "none"},
                "styled_response": "",
                "phone_number": "+123456789"
            },
            {
                "agent_name": "Matan",
                "agent_type": "off_radar",
                "status": "no_action_needed",
                "selected_action": {"id": "none"},
                "styled_response": "",
                "phone_number": "+987654321"
            }
        ],
        "execution_queue": [],
        "current_nodes": None,
        "next_nodes": None
    }
    
    result = scheduler_node(state)
    
    print(f"Input actions: {len(state['selected_actions'])}")
    print(f"Execution queue size: {len(result['execution_queue'])}")
    assert len(result['execution_queue']) == 0, "Should filter out no_action_needed"
    print("✓ PASSED\n")


def test_queue_multiple_actions():
    """Test queueing multiple actions from different agents."""
    print("=" * 70)
    print("TEST 3: QUEUE MULTIPLE ACTIONS")
    print("=" * 70)
    
    state: SupervisorState = {
        "recent_messages": [],
        "group_sentiment": "neutral",
        "group_metadata": {},
        "selected_actions": [
            {
                "agent_name": "Tamar",
                "agent_type": "active",
                "status": "success",
                "selected_action": {
                    "id": "initiate_discussion",
                    "purpose": "Start conversation about travel"
                },
                "styled_response": "Hey everyone! Has anyone been to Jerusalem lately?",
                "phone_number": "+37379276083"
            },
            {
                "agent_name": "Matan",
                "agent_type": "off_radar",
                "status": "success",
                "selected_action": {
                    "id": "express_consensus_agreement",
                    "purpose": "Show agreement"
                },
                "styled_response": "agree",
                "phone_number": "+19252088164"
            }
        ],
        "execution_queue": [],
        "current_nodes": None,
        "next_nodes": None
    }
    
    result = scheduler_node(state)
    
    print(f"Input actions: {len(state['selected_actions'])}")
    print(f"Execution queue size: {len(result['execution_queue'])}")
    print("\nQueued actions:")
    for action in result['execution_queue']:
        print(f"  - {action['agent_name']}: {action['action']['id']}")
    
    assert len(result['execution_queue']) == 2, "Should queue both actions"
    assert result['execution_queue'][0]['agent_name'] == "Tamar", "First action should be Tamar"
    assert result['execution_queue'][1]['agent_name'] == "Matan", "Second action should be Matan"
    print("✓ PASSED\n")


def test_mixed_actions():
    """Test with mix of actionable and no_action_needed."""
    print("=" * 70)
    print("TEST 4: MIXED ACTIONS (ACTIONABLE + NO ACTION)")
    print("=" * 70)
    
    state: SupervisorState = {
        "recent_messages": [],
        "group_sentiment": "neutral",
        "group_metadata": {},
        "selected_actions": [
            {
                "agent_name": "Tamar",
                "agent_type": "active",
                "status": "success",
                "selected_action": {
                    "id": "show_interest",
                    "purpose": "Engage with user"
                },
                "styled_response": "That sounds amazing! Tell me more!",
                "phone_number": "+37379276083"
            },
            {
                "agent_name": "Matan",
                "agent_type": "off_radar",
                "status": "no_action_needed",
                "selected_action": None,
                "styled_response": "",
                "phone_number": "+19252088164"
            }
        ],
        "execution_queue": [],
        "current_nodes": None,
        "next_nodes": None
    }
    
    result = scheduler_node(state)
    
    print(f"Input actions: {len(state['selected_actions'])}")
    print(f"Execution queue size: {len(result['execution_queue'])}")
    print("\nQueued actions:")
    for action in result['execution_queue']:
        print(f"  - {action['agent_name']}: {action['action']['id']}")
    
    assert len(result['execution_queue']) == 1, "Should queue only actionable items"
    assert result['execution_queue'][0]['agent_name'] == "Tamar", "Should be Tamar's action"
    print("✓ PASSED\n")


def test_get_ready_actions():
    """Test getting ready actions from queue."""
    print("=" * 70)
    print("TEST 5: GET READY ACTIONS")
    print("=" * 70)
    
    state: SupervisorState = {
        "recent_messages": [],
        "group_sentiment": "neutral",
        "group_metadata": {},
        "selected_actions": [],
        "execution_queue": [
            {
                "agent_name": "Tamar",
                "agent_type": "active",
                "action": {"id": "initiate_discussion"},
                "action_content": "Test message",
                "phone_number": "+37379276083",
                "status": "pending"
            },
            {
                "agent_name": "Matan",
                "agent_type": "off_radar",
                "action": {"id": "post_neutral_response"},
                "action_content": "ok",
                "phone_number": "+19252088164",
                "status": "pending"
            }
        ],
        "current_nodes": None,
        "next_nodes": None
    }
    
    ready = get_ready_actions(state)
    
    print(f"Ready actions: {len(ready)}")
    for action in ready:
        print(f"  - {action['agent_name']}: {action['action']['id']}")
    
    assert len(ready) == 2, "Should return all pending actions"
    print("✓ PASSED\n")


def test_mark_action_sent():
    """Test marking an action as sent."""
    print("=" * 70)
    print("TEST 6: MARK ACTION AS SENT")
    print("=" * 70)
    
    execution_queue = [
        {
            "agent_name": "Tamar",
            "agent_type": "active",
            "action": {"id": "initiate_discussion"},
            "action_content": "Test message",
            "phone_number": "+37379276083",
            "status": "pending"
        },
        {
            "agent_name": "Matan",
            "agent_type": "off_radar",
            "action": {"id": "post_neutral_response"},
            "action_content": "ok",
            "phone_number": "+19252088164",
            "status": "pending"
        }
    ]
    
    print(f"Queue size before: {len(execution_queue)}")
    
    # Mark first action as sent
    mark_action_sent(execution_queue, execution_queue[0])
    
    print(f"Queue size after: {len(execution_queue)}")
    print(f"Remaining action: {execution_queue[0]['agent_name']}")
    
    assert len(execution_queue) == 1, "Should have 1 action remaining"
    assert execution_queue[0]['agent_name'] == "Matan", "Matan's action should remain"
    print("✓ PASSED\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("SCHEDULER TEST SUITE")
    print("=" * 70 + "\n")
    
    test_empty_selected_actions()
    test_no_action_needed_filtered()
    test_queue_multiple_actions()
    test_mixed_actions()
    test_get_ready_actions()
    test_mark_action_sent()
    
    print("=" * 70)
    print("ALL TESTS PASSED! ✓")
    print("=" * 70)
