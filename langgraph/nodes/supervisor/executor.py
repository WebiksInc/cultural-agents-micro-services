from typing import Dict, Any
from logs.logfire_config import get_logger
from logs import log_node_start
# from nodes.supervisor.scheduler import get_ready_actions, mark_action_sent
from nodes.supervisor.scheduler import get_ready_actions
from datetime import datetime
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from telegram_exm import *

logger = get_logger(__name__)


def executor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executor Node
    
    Executes all ready actions from the execution queue by sending them to Telegram.
    Removes executed actions from both execution_queue and selected_actions.
    
    Args:
        state: SupervisorState dict containing execution_queue and group_metadata
        
    Returns:
        Dict with cleared execution_queue and selected_actions
    """
    log_node_start("executor", {
        "execution_queue_count": len(state.get('execution_queue', []))
    }, supervisor_state=state)
    
    execution_queue = state.get('execution_queue', [])
    group_metadata = state.get('group_metadata', {})
    chat_id = group_metadata.get('id', '')
    
    # If queue is empty, nothing to execute
    if not execution_queue:
        logger.info("Executor: No actions to execute")
        return {
            'execution_queue': [],
            'selected_actions': []
        }
    
    # Get ready actions
    ready_actions = get_ready_actions(state)
    
    if not ready_actions:
        logger.info("Executor: No ready actions in queue")
        return {}
    
    logger.info(f"Executor: Executing {len(ready_actions)} actions", supervisor_state=state)
    
    # Execute each action
    executed_count = 0
    for action in ready_actions:
        agent_name = action.get('agent_name', 'unknown')
        action_id = action.get('action_id', 'unknown')
        action_content = action.get('action_content', '')
        phone_number = action.get('phone_number', '')
        target_message = action.get('target_message')
        
        logger.info(f"Executing action '{action_id}' from {agent_name}")
        
        if not phone_number:
            logger.error(f"No phone number for agent {agent_name}")
            continue
        
        if not action_content:
            logger.error(f"No message content for action from {agent_name}")
            continue
        
        # Convert timestamp from "YYYY-MM-DD HH:MM:SS" to ISO format "YYYY-MM-DDTHH:MM:SS.000Z"
        reply_timestamp = None
        if target_message and isinstance(target_message, dict):
            timestamp_str = target_message.get('timestamp', '')
            if timestamp_str:
                try:
                    # Convert "2025-11-26 08:36:07" to "2025-11-26T08:36:07.000Z"
                  
                    dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    reply_timestamp = dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                    logger.info(f"Converted timestamp: {timestamp_str} -> {reply_timestamp}")
                except Exception as e:
                    logger.warning(f"Failed to convert timestamp '{timestamp_str}': {e}")
                    reply_timestamp = None
        
        # Route based on action_id
        if action_id == "add_reaction":
            # For add_reaction, use add_reaction_to_message
            if not reply_timestamp:
                logger.error(f"add_reaction action requires target_message with timestamp, but none provided")
                continue
            
            # For reactions, action_content contains the emoji
            emoji = action_content.strip()
            logger.info(f"Adding reaction '{emoji}' from {agent_name} ({phone_number}) to message at {reply_timestamp}")
            
            response = add_reaction_to_message(
                phone=phone_number,
                chat_id=chat_id,
                message_timestamp=reply_timestamp,
                emoji=emoji
            )
            
            if response and response.get("success"):
                logger.info(f"Successfully added reaction from {agent_name}")
                executed_count += 1
            else:
                logger.error(f"ERROR: Failed to add reaction from {agent_name}: {response.get('error', 'Unknown error')}")
        
        else:
            # For all other actions, use send_telegram_message
            logger.info(f"Sending message from {agent_name} ({phone_number}) to {chat_id}")
            
            response = send_telegram_message(
                from_phone=phone_number,
                to_target=chat_id,
                content_value=action_content,
                reply_to_timestamp=reply_timestamp  # Use if available, None otherwise
            )
            
            if response and response.get("success"):
                logger.info(f"Successfully sent message from {agent_name}")
                executed_count += 1
            else:
                logger.error(f"ERROR: Failed to send message from {agent_name}: {response.get('error', 'Unknown error')}")
    
    logger.info(f"Executor: Executed {executed_count}/{len(ready_actions)} actions successfully")
    
    return {
        'execution_queue': execution_queue,
        'selected_actions' : "CLEAR"
    }
