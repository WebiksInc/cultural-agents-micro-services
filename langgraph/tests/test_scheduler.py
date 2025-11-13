"""
Test Scheduler Node

Tests the scheduler's ability to arrange and time actions from multiple agents.
"""

import sys
from pathlib import Path
from datetime import datetime
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


def test_scheduler_basic():
    """Test scheduler with multiple successful actions."""
    print("=" * 70)
    print("TEST 1: BASIC SCHEDULING - Multiple successful actions")
    print("=" * 70)
    
    state: SupervisorState = {
        "group_sentiment": "positive",
        "group_metadata": {},
        "recent_messages": [],
        "selected_actions": [
            {
                "status": "success",
                "agent_name": "TrollBot_Alpha",
                "agent_type": "troll",
                "id": "casual_joke",
                "purpose": "Add humor",
                "styled_response": "lol that's hilarious 😂"
            },
            {
                "status": "success",
                "agent_name": "ActiveUser_Beta",
                "agent_type": "active",
                "id": "thoughtful_comment",
                "purpose": "Share insight",
                "styled_response": "I think this raises an interesting point about community engagement."
            },
            {
                "status": "success",
                "agent_name": "ManagerBot_Gamma",
                "agent_type": "manager",
                "id": "moderate_discussion",
                "purpose": "Keep discussion on track",
                "styled_response": "Great discussion everyone! Let's make sure we stay on topic."
            }
        ],
        "execution_queue": [],
        "current_nodes": None,
        "next_nodes": None
    }
    
    scheduler_node(state)
    
    execution_queue = state.get('execution_queue', [])
    
    print(f"\n--- Execution Queue ({len(execution_queue)} items) ---")
    for i, item in enumerate(execution_queue):
        print(f"\n{i+1}. Agent: {item['agent_name']} ({item['agent_type']})")
        print(f"   Action: {item['action']['id']}")
        print(f"   Content: {item['action_content'][:50]}...")
        print(f"   Scheduled: {item['scheduled_time']}")
        print(f"   Status: {item['status']}")
    
    assert len(execution_queue) == 3, "Should have 3 actions in queue"
    assert all(item['status'] == 'pending' for item in execution_queue), "All should be pending"
    print("\n✓ PASSED\n")


def test_scheduler_filtering():
    """Test scheduler filtering out no_action_needed and errors."""
    print("=" * 70)
    print("TEST 2: FILTERING - Skip no_action_needed and errors")
    print("=" * 70)
    
    state: SupervisorState = {
        "group_sentiment": "neutral",
        "group_metadata": {},
        "recent_messages": [],
        "selected_actions": [
            {
                "status": "success",
                "agent_name": "TrollBot_Alpha",
                "agent_type": "troll",
                "id": "casual_joke",
                "purpose": "Add humor",
                "styled_response": "lol that's funny 😄"
            },
            {
                "status": "no_action_needed",
                "reason": "neutral_trigger",
                "agent_name": "ActiveUser_Beta",
                "agent_type": "active"
            },
            {
                "status": "error",
                "reason": "text_generation_failed",
                "error": "LLM timeout",
                "agent_name": "ManagerBot_Gamma",
                "agent_type": "manager"
            },
            {
                "status": "success",
                "agent_name": "TrollBot_Delta",
                "agent_type": "troll",
                "id": "react_to_meme",
                "purpose": "Engage with meme",
                "styled_response": "this is gold 🔥"
            }
        ],
        "execution_queue": [],
        "current_nodes": None,
        "next_nodes": None
    }
    
    scheduler_node(state)
    
    execution_queue = state.get('execution_queue', [])
    
    print(f"\n--- Execution Queue ({len(execution_queue)} items) ---")
    for i, item in enumerate(execution_queue):
        print(f"{i+1}. {item['agent_name']} - {item['action']['id']}")
    
    assert len(execution_queue) == 2, "Should only have 2 successful actions"
    assert execution_queue[0]['agent_name'] == 'TrollBot_Alpha', "First should be TrollBot_Alpha"
    assert execution_queue[1]['agent_name'] == 'TrollBot_Delta', "Second should be TrollBot_Delta"
    print("\n✓ PASSED\n")


def test_scheduler_max_retries():
    """Test scheduler including max_retries_reached actions."""
    print("=" * 70)
    print("TEST 3: MAX RETRIES - Include max_retries_reached actions")
    print("=" * 70)
    
    state: SupervisorState = {
        "group_sentiment": "neutral",
        "group_metadata": {},
        "recent_messages": [],
        "selected_actions": [
            {
                "status": "max_retries_reached",
                "agent_name": "TrollBot_Alpha",
                "agent_type": "troll",
                "id": "casual_comment",
                "purpose": "Engage casually",
                "styled_response": "That is most intriguing indeed.",
                "validation_note": "Failed validation after 3 attempts"
            },
            {
                "status": "success",
                "agent_name": "ActiveUser_Beta",
                "agent_type": "active",
                "id": "share_insight",
                "purpose": "Contribute meaningfully",
                "styled_response": "This aligns with what I've observed in similar communities."
            }
        ],
        "execution_queue": [],
        "current_nodes": None,
        "next_nodes": None
    }
    
    scheduler_node(state)
    
    execution_queue = state.get('execution_queue', [])
    
    print(f"\n--- Execution Queue ({len(execution_queue)} items) ---")
    for i, item in enumerate(execution_queue):
        print(f"\n{i+1}. {item['agent_name']} - {item['action']['id']}")
        if 'validation_note' in item:
            print(f"   Note: {item['validation_note']}")
    
    assert len(execution_queue) == 2, "Should include both actions"
    assert 'validation_note' in execution_queue[0], "Should have validation note"
    print("\n✓ PASSED\n")


def test_scheduler_empty():
    """Test scheduler with no actions."""
    print("=" * 70)
    print("TEST 4: EMPTY INPUT - No actions to schedule")
    print("=" * 70)
    
    state: SupervisorState = {
        "group_sentiment": "neutral",
        "group_metadata": {},
        "recent_messages": [],
        "selected_actions": [],
        "execution_queue": [],
        "current_nodes": None,
        "next_nodes": None
    }
    
    scheduler_node(state)
    
    execution_queue = state.get('execution_queue', [])
    
    print(f"Execution queue length: {len(execution_queue)}")
    assert len(execution_queue) == 0, "Should have empty queue"
    print("✓ PASSED\n")


def test_helper_functions():
    """Test helper functions for execution queue management."""
    print("=" * 70)
    print("TEST 5: HELPER FUNCTIONS - get_ready_actions and mark_action_sent")
    print("=" * 70)
    
    # Create a state with pre-scheduled actions (one in past, one in future)
    from datetime import timedelta
    past_time = (datetime.now() - timedelta(seconds=5)).isoformat()
    future_time = (datetime.now() + timedelta(seconds=60)).isoformat()
    
    state: SupervisorState = {
        "group_sentiment": "neutral",
        "group_metadata": {},
        "recent_messages": [],
        "selected_actions": [],
        "execution_queue": [
            {
                "agent_name": "TrollBot_Alpha",
                "agent_type": "troll",
                "action": {"id": "joke", "purpose": "humor"},
                "action_content": "lol nice",
                "scheduled_time": past_time,
                "status": "pending"
            },
            {
                "agent_name": "ActiveUser_Beta",
                "agent_type": "active",
                "action": {"id": "comment", "purpose": "insight"},
                "action_content": "Interesting point",
                "scheduled_time": future_time,
                "status": "pending"
            }
        ],
        "current_nodes": None,
        "next_nodes": None
    }
    
    # Test get_ready_actions
    ready = get_ready_actions(state)
    print(f"\nReady actions: {len(ready)}")
    assert len(ready) == 1, "Only one action should be ready (past time)"
    assert ready[0]['agent_name'] == 'TrollBot_Alpha', "Should be the past action"
    
    # Test mark_action_sent
    mark_action_sent(state, 0)
    assert state['execution_queue'][0]['status'] == 'sent', "Should mark as sent"
    assert 'sent_time' in state['execution_queue'][0], "Should add sent_time"
    
    # Ready actions should now be empty (the ready one was marked sent)
    ready_after = get_ready_actions(state)
    print(f"Ready actions after marking sent: {len(ready_after)}")
    assert len(ready_after) == 0, "No actions should be ready after marking sent"
    
    print("\n✓ PASSED\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("SCHEDULER TEST SUITE")
    print("=" * 70 + "\n")
    
    test_scheduler_basic()
    test_scheduler_filtering()
    test_scheduler_max_retries()
    test_scheduler_empty()
    test_helper_functions()
    
    print("=" * 70)
    print("ALL TESTS PASSED! ✓")
    print("=" * 70)
