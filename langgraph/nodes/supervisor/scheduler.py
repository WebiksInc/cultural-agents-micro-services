"""
Scheduler Node - Manages action execution queue

Responsibilities:
1. Take selected_actions from multiple agents
2. Build execution_queue in FIFO order
3. Provide helpers to get ready actions and mark them as sent
4. Maintain in-memory queue state
"""
from typing import Dict, Any, List
from logs.logfire_config import get_logger
from logs import log_node_start

# Configure logging
logger = get_logger(__name__)


# Scheduler Node - Takes selected_actions from the supervisor's state and builds execution_queue.
def scheduler_node(state: Dict[str, Any]) -> Dict[str, Any]:
    log_node_start("scheduler", {
        "selected_actions_count": len(state.get('selected_actions', []))
    }, supervisor_state=state)
    
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
    
    logger.info(f"Scheduler: Queuing {len(actionable_items)} actions", selected_actions=actionable_items, supervisor_state=state)
    
    # Build execution queue with all necessary fields
    execution_queue = []
    for action in actionable_items:
        selected_action_data = action.get('selected_action', {})
        queue_item = {
            'agent_name': action.get('agent_name', 'unknown'),
            'agent_type': action.get('agent_type', 'unknown'),
            'action_id': selected_action_data.get('id', 'unknown'),
            'action_purpose': selected_action_data.get('purpose', ''),
            'action_content': action.get('styled_response', ''),
            'phone_number': action.get('phone_number', ''),
            'target_message': selected_action_data.get('target_message'),  # Include target_message
            'status': 'pending'  # pending, sent
        }
        execution_queue.append(queue_item)
        logger.info(f"Queued action from {queue_item['agent_name']}: {queue_item['action_id']}", **queue_item)
    
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

# In the future this function will be used

# def mark_action_sent(execution_queue: List[Dict[str, Any]], action: Dict[str, Any]) -> None:
#     """
#     Mark an action as sent and remove it from the queue.
#     Modifies the execution_queue list in-place.
    
#     Args:
#         execution_queue: The execution queue list
#         action: The action item that was sent
#     """
#     # Find and remove the action from queue
#     for i, item in enumerate(execution_queue):
#         if (item.get('agent_name') == action.get('agent_name') and
#             item.get('action', {}).get('id') == action.get('action', {}).get('id')):
#             execution_queue.pop(i)
#             logger.info(f"Removed sent action from queue: {action.get('agent_name')} - {action.get('action', {}).get('id')}")
#             break
