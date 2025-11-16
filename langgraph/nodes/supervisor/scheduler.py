"""
Scheduler Node (Supervisor)

Arranges actions from multiple agents and schedules them for execution.
Creates an execution queue with timing information.
"""

import logging
import random
from typing import Dict, Any, List
from datetime import datetime, timedelta
from logs.logfire_config import get_logger

# Configure logging
logger = get_logger(__name__)

# Configuration for demo scheduling
MIN_DELAY_SECONDS = 2  # Minimum delay between actions
MAX_DELAY_SECONDS = 10  # Maximum delay between actions


def scheduler_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scheduler Node
    
    Processes selected_actions from multiple agents and creates an execution_queue
    with scheduled times for each action.
    
    For demo purposes, uses random delays between MIN_DELAY_SECONDS and MAX_DELAY_SECONDS.
    
    Filters out:
    - Actions with status "no_action_needed"
    - Actions with status "error"
    
    Args:
        state: SupervisorState dict containing selected_actions
    """
    logger.info("Starting Scheduler")
    
    selected_actions = state.get('selected_actions', [])
    
    if not selected_actions:
        logger.info("No selected_actions to schedule")
        state['execution_queue'] = []
        return state
    
    logger.info(f"Processing {len(selected_actions)} selected actions")
    
    # Filter actions - only include successful ones or max_retries_reached
    valid_actions = []
    for action in selected_actions:
        status = action.get('status', '')
        
        if status == 'no_action_needed':
            logger.info(f"Skipping action (no action needed): {action.get('reason', 'unknown')}")
            continue
        
        if status == 'error':
            logger.warning(f"Skipping action (error): {action.get('error', 'unknown')}")
            continue
        
        if status in ['success', 'max_retries_reached']:
            valid_actions.append(action)
        else:
            logger.warning(f"Unknown action status '{status}' - skipping")
    
    logger.info(f"Filtered to {len(valid_actions)} valid actions")
    
    if not valid_actions:
        logger.info("No valid actions to schedule")
        state['execution_queue'] = []
        return state
    
    # Schedule actions with random delays (FIFO order)
    execution_queue = []
    current_time = datetime.now()
    
    for i, action in enumerate(valid_actions):
        # Calculate scheduled time with random delay
        if i == 0:
            # First action - schedule immediately or with small delay
            delay_seconds = random.uniform(0, MIN_DELAY_SECONDS)
        else:
            # Subsequent actions - random delay from previous action
            delay_seconds = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
        
        scheduled_time = current_time + timedelta(seconds=delay_seconds)
        current_time = scheduled_time  # Next action scheduled after this one
        
        # Create execution queue item
        queue_item = {
            "agent_name": action.get('agent_name', 'unknown'),
            "agent_type": action.get('agent_type', 'unknown'),
            "phone_number": action.get('phone_number', ''),
            "action": {
                "id": action.get('id', 'unknown'),
                "purpose": action.get('purpose', '')
            },
            "action_content": action.get('styled_response', ''),
            "scheduled_time": scheduled_time.isoformat(),
            "status": "pending"
        }
        
        # Add validation note if present (for max_retries_reached)
        if action.get('validation_note'):
            queue_item['validation_note'] = action['validation_note']
        
        execution_queue.append(queue_item)
        
        logger.info(
            f"Scheduled action {i+1}/{len(valid_actions)}: "
            f"{queue_item['agent_name']} ({queue_item['agent_type']}) - "
            f"{queue_item['action']['id']} at {scheduled_time.strftime('%H:%M:%S')}"
        )
    
    # Update state with execution queue
    state['execution_queue'] = execution_queue
    
    # Mark all recent messages as processed so we don't analyze them again
    for msg in state.get('recent_messages', []):
        msg['processed'] = True
    
    # Clear selected_actions after scheduling (they're now in execution_queue)
    state['selected_actions'] = []
    
    logger.info(f"Scheduler completed - {len(execution_queue)} actions queued, {len(state.get('recent_messages', []))} messages marked as processed")
    
    # CRITICAL: Return the updated state
    return state


def get_ready_actions(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Helper function to get actions that are ready to execute (scheduled time has passed).
    
    Args:
        state: SupervisorState dict containing execution_queue
        
    Returns:
        List of actions ready to execute
    """
    execution_queue = state.get('execution_queue', [])
    now = datetime.now()
    
    ready_actions = []
    for action in execution_queue:
        if action.get('status') != 'pending':
            continue
        
        scheduled_time_str = action.get('scheduled_time')
        if not scheduled_time_str:
            continue
        
        try:
            scheduled_time = datetime.fromisoformat(scheduled_time_str)
            if scheduled_time <= now:
                ready_actions.append(action)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid scheduled_time format: {scheduled_time_str} - {e}")
    
    return ready_actions


def mark_action_sent(execution_queue: List[Dict[str, Any]], action: Dict[str, Any]) -> None:
    """
    Helper function to mark an action as sent in the execution queue.
    
    Args:
        execution_queue: List of actions in the execution queue
        action: The specific action dict to mark as sent
    """
    # Find the action in the queue and mark it as sent
    for item in execution_queue:
        if item is action:  # Same object reference
            item['status'] = 'sent'
            item['sent_time'] = datetime.now().isoformat()
            logger.info(f"Marked action {action.get('action', {}).get('id', 'unknown')} as sent")
            return
    
    logger.error(f"Action not found in execution_queue")
