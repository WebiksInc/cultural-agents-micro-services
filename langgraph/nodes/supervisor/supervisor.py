"""
Supervisor Node - Main orchestrator for the hierarchical agent system.

Responsibilities:
1. Poll Telegram for new messages every 10 seconds (configurable)
2. Maintain recent_messages list (max 10 messages)
3. Update state for routing to Component B, C, and agent nodes
4. Execute ready actions from the execution_queue every 2 seconds
5. Send messages back to Telegram using agent phone numbers
"""

import time
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import existing state classes
from states.agent_state import Message
from states.supervisor_state import SupervisorState

# Import Telegram API functions
from telegram_exm import (
    get_chat_messages,
    get_unread_telegram_messages,
    get_all_group_participants,
    send_telegram_message
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "supervisor_config.json"
with open(CONFIG_PATH, 'r') as f:
    CONFIG = json.load(f)

# Extract config values
CHAT_ID = CONFIG["telegram"]["chat_id"]
MESSAGE_CHECK_INTERVAL = CONFIG["polling"]["message_check_interval_seconds"]
EXECUTOR_CHECK_INTERVAL = CONFIG["polling"]["executor_check_interval_seconds"]
MAX_RECENT_MESSAGES = CONFIG["polling"]["max_recent_messages"]

# Global state for first run detection
_first_run = True
_last_message_check = 0
_last_executor_check = 0


def parse_telegram_message(msg_data: Dict[str, Any]) -> Message:
    """
    Parse Telegram API message format into our Message TypedDict from agent_state.
    
    Args:
        msg_data: Raw message data from Telegram API
        
    Returns:
        Parsed Message object
    """
    return Message(
        message_id=str(msg_data.get("id", "")),
        sender_id=msg_data.get("senderId") or "",
        sender_username=msg_data.get("senderUsername") or "",
        sender_first_name=msg_data.get("senderFirstName") or "",
        sender_last_name=msg_data.get("senderLastName") or "",
        text=msg_data.get("text") or "",
        date=datetime.fromisoformat(msg_data.get("date", "").replace("Z", "+00:00")) if msg_data.get("date") else datetime.now(),
        message_emotion=None,  # Filled by Component B
        sender_personality=None,  # Filled by Component C
        processed=False  # New messages are unprocessed
    )


def update_recent_messages(current_messages: List[Message], new_messages: List[Message]) -> List[Message]:
    """
    Update the recent_messages list with new messages.
    Maintains max size and removes duplicates.
    
    Args:
        current_messages: Current list of messages in state
        new_messages: New messages to add
        
    Returns:
        Updated list of messages (newest first, max MAX_RECENT_MESSAGES)
    """
    # Combine current and new messages
    all_messages = new_messages + current_messages
    
    # Remove duplicates by message_id (keep first occurrence = newest)
    seen_ids = set()
    unique_messages = []
    for msg in all_messages:
        if msg["message_id"] not in seen_ids and msg["message_id"]:
            seen_ids.add(msg["message_id"])
            unique_messages.append(msg)
    
    # Keep only the most recent MAX_RECENT_MESSAGES
    return unique_messages[:MAX_RECENT_MESSAGES]


def supervisor_node(state: SupervisorState, agent_personas: Dict[str, Dict[str, Any]]) -> SupervisorState:
    """
    Main supervisor node that orchestrates the entire system.
    
    Responsibilities:
    1. Check if it's time to poll for new messages (every MESSAGE_CHECK_INTERVAL seconds)
    2. Check if it's time to execute ready actions (every EXECUTOR_CHECK_INTERVAL seconds)
    3. Update state with new messages and route to next nodes
    4. Execute ready actions by sending to Telegram
    
    Args:
        state: Current supervisor state
        agent_personas: Pre-loaded agent persona configurations with phone numbers
        
    Returns:
        Updated supervisor state
    """
    global _first_run, _last_message_check, _last_executor_check
    
    current_time = time.time()
    updated_state = state.copy()
    
    # Use first active agent's phone for API calls (they're all in the same group)
    primary_phone = agent_personas.get("active", {}).get("phone_number", "+37379276083")
    
    # ===== MESSAGE POLLING LOGIC =====
    time_since_message_check = current_time - _last_message_check
    should_check_messages = time_since_message_check >= MESSAGE_CHECK_INTERVAL
    
    if should_check_messages:
        logger.info(f"Polling for messages (interval: {MESSAGE_CHECK_INTERVAL}s)")
        
        if _first_run:
            logger.info("First run: Initializing group metadata and fetching initial messages")
            
            # Initialize group metadata on first run
            participants_data = get_all_group_participants(phone=primary_phone, chat_id=CHAT_ID)
            if participants_data and participants_data.get("success"):
                updated_state["group_metadata"] = {
                    "name": participants_data.get("chatTitle", CONFIG["group_metadata"]["name"]),
                    "topic": CONFIG["group_metadata"]["topic"],
                    "members": participants_data.get("participantCount", CONFIG["group_metadata"]["members"]),
                    "participants": participants_data.get("participants", [])
                }
                logger.info(f"Group metadata initialized: {updated_state['group_metadata']['name']}")
            
            # Get initial messages using get_chat_messages
            messages_data = get_chat_messages(phone=primary_phone, chat_id=CHAT_ID, limit=MAX_RECENT_MESSAGES)
            if messages_data and messages_data.get("success"):
                new_messages = [parse_telegram_message(msg) for msg in messages_data.get("messages", [])]
                updated_state["recent_messages"] = update_recent_messages(
                    updated_state.get("recent_messages", []),
                    new_messages
                )
                logger.info(f"Loaded {len(new_messages)} initial messages")
            
            _first_run = False
            
        else:
            # Subsequent runs: fetch messages and filter for new ones
            messages_data = get_chat_messages(phone=primary_phone, chat_id=CHAT_ID, limit=MAX_RECENT_MESSAGES)
            
            if messages_data and messages_data.get("success"):
                new_messages = [parse_telegram_message(msg) for msg in messages_data.get("messages", [])]
                
                # Filter out messages we've already seen
                current_ids = {msg["message_id"] for msg in updated_state.get("recent_messages", [])}
                truly_new = [msg for msg in new_messages if msg["message_id"] not in current_ids]
                
                if truly_new:
                    logger.info(f"Found {len(truly_new)} new messages")
                    updated_state["recent_messages"] = update_recent_messages(
                        updated_state.get("recent_messages", []),
                        truly_new
                    )
        
        _last_message_check = current_time
    
    # ===== ACTION EXECUTION LOGIC =====
    time_since_executor_check = current_time - _last_executor_check
    should_execute_actions = time_since_executor_check >= EXECUTOR_CHECK_INTERVAL
    
    if should_execute_actions:
        execution_queue = updated_state.get("execution_queue", [])
        if execution_queue:
            logger.info(f"Checking execution queue ({len(execution_queue)} actions)")
            
            # Import scheduler helper functions
            from .scheduler import get_ready_actions, mark_action_sent
            
            ready_actions = get_ready_actions(updated_state)
            
            if ready_actions:
                logger.info(f"Found {len(ready_actions)} ready actions to execute")
                
                for action in ready_actions:
                    agent_name = action.get("agent_name", "unknown")
                    agent_type = action.get("agent_type", "unknown")
                    action_content = action.get("action_content", "")
                    phone_number = action.get("phone_number", "")
                    action_id = action.get("action", {}).get("id", "unknown")
                    
                    logger.info(f"Executing action '{action_id}' for {agent_name}")
                    
                    if not phone_number:
                        logger.error(f"No phone number found for agent {agent_name} (type: {agent_type})")
                        mark_action_sent(execution_queue, action)
                        continue
                    
                    # action_content is the styled_response text
                    message_text = action_content if isinstance(action_content, str) else ""
                    
                    if not message_text:
                        logger.error(f"No message text for action from {agent_name}")
                        mark_action_sent(execution_queue, action)
                        continue
                    
                    logger.info(f"Sending message from {agent_name} ({phone_number}) to {CHAT_ID}")
                    logger.info(f"Message preview: {message_text[:100]}...")
                    
                    # Send message using telegram_exm function
                    response = send_telegram_message(
                        from_phone=phone_number,
                        to_target=CHAT_ID,
                        content_value=message_text,
                        reply_to_timestamp=None  # For now, not replying to specific messages
                    )
                    
                    if response and response.get("success"):
                        logger.info(f"✓ Successfully sent message from {agent_name}")
                        mark_action_sent(execution_queue, action)
                    else:
                        logger.error(f"✗ Failed to send message from {agent_name}: {response.get('error', 'Unknown error')}")
                        # Mark as sent anyway to avoid infinite retries
                        mark_action_sent(execution_queue, action)
                
                # Update execution queue in state
                updated_state["execution_queue"] = execution_queue
            else:
                # Check if there are pending actions that aren't ready yet
                pending_actions = [a for a in execution_queue if a.get("status") == "pending"]
                if pending_actions:
                    logger.info(f"{len(pending_actions)} actions still pending (not ready yet)")
        
        _last_executor_check = current_time
    
    logger.info(f"Supervisor cycle complete. Recent messages: {len(updated_state.get('recent_messages', []))}")
    return updated_state


def supervisor_continuous_loop(initial_state: SupervisorState, agent_personas: Dict[str, Dict[str, Any]], max_iterations: Optional[int] = None) -> None:
    """
    Run the supervisor in a continuous loop.
    This is for standalone testing. In production, the supervisor is part of the LangGraph.
    
    Args:
        initial_state: Initial supervisor state
        agent_personas: Pre-loaded agent persona configurations
        max_iterations: Optional limit on number of iterations (for testing)
    """
    state = initial_state
    iteration = 0
    
    logger.info("Starting supervisor continuous loop")
    
    try:
        while True:
            state = supervisor_node(state, agent_personas)
            iteration += 1
            
            if max_iterations and iteration >= max_iterations:
                logger.info(f"Reached max iterations ({max_iterations})")
                break
            
            # Sleep briefly to avoid tight loop
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        logger.info("Supervisor loop interrupted by user")
    except Exception as e:
        logger.error(f"Supervisor loop error: {e}", exc_info=True)


def load_agent_personas() -> Dict[str, Dict[str, Any]]:
    """
    Load agent persona configurations from JSON files.
    
    **IMPORTANT: This should be called ONCE during application initialization,
    NOT inside the supervisor node. Pass the loaded personas as a parameter.**
    
    Returns:
        Dictionary mapping agent_type to persona data including phone_number
    """
    personas = {}
    base_path = Path(__file__).parent.parent.parent
    
    for agent_config in CONFIG["agents"]:
        agent_type = agent_config["type"]
        persona_file = agent_config["persona_file"]
        persona_path = base_path / persona_file
        
        try:
            with open(persona_path, 'r') as f:
                persona_data = json.load(f)
                personas[agent_type] = persona_data
                logger.info(f"Loaded persona for {agent_type}: {persona_data.get('first_name', 'Unknown')}")
        except Exception as e:
            logger.error(f"Failed to load persona from {persona_path}: {e}")
            raise
    
    return personas


if __name__ == "__main__":
    # Test the supervisor node standalone
    # Load personas once at startup
    personas = load_agent_personas()
    
    initial_state = SupervisorState(
        recent_messages=[],
        group_sentiment="neutral",
        group_metadata=CONFIG["group_metadata"],
        selected_actions=[],
        execution_queue=[],
        current_nodes=None,
        next_nodes=None
    )
    
    # Run for 60 seconds (6 message checks, 30 executor checks)
    supervisor_continuous_loop(initial_state, personas, max_iterations=120)
