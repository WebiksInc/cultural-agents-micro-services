"""
Scheduler Node - Manages action execution queue

Responsibilities:
1. Take selected_actions from multiple agents
2. Build execution_queue in FIFO order
3. Provide helpers to get ready actions and mark them as sent
4. Maintain in-memory queue state
"""

import logging
from typing import Dict, Any, List
from logs.logfire_config import get_logger

# Configure logging
logger = get_logger(__name__)


def scheduler_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scheduler Node
    
    Takes selected_actions from agents and builds execution_queue.
    Actions are queued in FIFO order.
    
    Args:
        state: SupervisorState dict containing selected_actions
        
    Returns:
        Dict with updated execution_queue
    """
    selected_actions = state.get('selected_actions', [])
    
    # Filter out actions with no_action_needed status
    actionable_items = []
    for action in selected_actions:
        status = action.get('status')
        if status and status != 'no_action_needed':
            actionable_items.append(action)
    
    if not actionable_items:
        logger.info("Scheduler: No actionable items to queue")
        return {
            'execution_queue': []
        }
    
    logger.info(f"Scheduler: Queuing {len(actionable_items)} actions")
    
    # Build execution queue with all necessary fields
    execution_queue = []
    for action in actionable_items:
        queue_item = {
            'agent_name': action.get('agent_name', 'unknown'),
            'agent_type': action.get('agent_type', 'unknown'),
            'action': action.get('selected_action', {}),  # Full action dict with id, purpose
            'action_content': action.get('styled_response', ''),  # The actual message to send
            'phone_number': action.get('phone_number', ''),
            'status': 'pending'  # pending, sent
        }
        execution_queue.append(queue_item)
        logger.info(f"Queued action from {queue_item['agent_name']}: {queue_item['action'].get('id', 'unknown')}", **queue_item)
    
    return {
        'execution_queue': execution_queue
    }


def get_ready_actions(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get all pending actions from execution_queue that are ready to execute.
    
    For simple FIFO: all pending actions are ready.
    Future enhancement: filter by scheduled time.
    
    Args:
        state: SupervisorState dict containing execution_queue
        
    Returns:
        List of ready action items
    """
    execution_queue = state.get('execution_queue', [])
    ready = [action for action in execution_queue if action.get('status') == 'pending']
    return ready


def mark_action_sent(execution_queue: List[Dict[str, Any]], action: Dict[str, Any]) -> None:
    """
    Mark an action as sent and remove it from the queue.
    Modifies the execution_queue list in-place.
    
    Args:
        execution_queue: The execution queue list
        action: The action item that was sent
    """
    # Find and remove the action from queue
    for i, item in enumerate(execution_queue):
        if (item.get('agent_name') == action.get('agent_name') and
            item.get('action', {}).get('id') == action.get('action', {}).get('id')):
            execution_queue.pop(i)
            logger.info(f"Removed sent action from queue: {action.get('agent_name')} - {action.get('action', {}).get('id')}")
            break


def clear_selected_actions(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clear selected_actions after all actions have been executed.
    This should be called after the execution queue is empty.
    
    Args:
        state: SupervisorState dict
        
    Returns:
        Dict with cleared selected_actions
    """
    return {
        'selected_actions': []
    }
