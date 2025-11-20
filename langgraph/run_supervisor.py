"""
Main entry point for running the Supervisor graph with polling loop.

This script:
1. Builds the hierarchical supervisor graph
2. Polls Telegram for new messages periodically
3. Runs the graph when new messages arrive
4. Handles the continuous polling loop with sleep intervals
"""

import time
import json
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

# Import graph builder
from build_graph import build_supervisor_graph
from states.supervisor_state import SupervisorState
from states.agent_state import Message

# Import Telegram functions
from telegram_exm import get_chat_messages, get_all_group_participants

# Import Logfire logging
from logs.logfire_config import setup_logfire, get_logger

# Setup Logfire
setup_logfire("cultural-agents-supervisor")
logger = get_logger(__name__)

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config" / "supervisor_config.json"
with open(CONFIG_PATH, 'r') as f:
    CONFIG = json.load(f)

CHAT_ID = CONFIG["telegram"]["chat_id"]
MESSAGE_CHECK_INTERVAL = CONFIG["polling"]["message_check_interval_seconds"]
TELEGRAM_FETCH_LIMIT = CONFIG["polling"]["telegram_fetch_limit"]
MAX_RECENT_MESSAGES = CONFIG["polling"]["max_recent_messages"]

# Global state
_first_run = True
_last_message_check = 0


def parse_telegram_message(msg_data: dict) -> Message:
    """Parse Telegram API message into Message TypedDict."""
    return Message(
        message_id=str(msg_data.get("id", "")),
        sender_id=msg_data.get("senderId") or "",
        sender_username=msg_data.get("senderUsername") or "",
        sender_first_name=msg_data.get("senderFirstName") or "",
        sender_last_name=msg_data.get("senderLastName") or "",
        text=msg_data.get("text") or "",
        date=datetime.fromisoformat(msg_data.get("date", "").replace("Z", "+00:00")) if msg_data.get("date") else datetime.now(),
        message_emotion=None,
        sender_personality=None,
        processed=False
    )


def is_agent_message(msg: Message, agent_personas: list) -> bool:
    """Check if message was sent by one of our agents."""
    sender_username = msg.get("sender_username", "").lower()
    sender_first = msg.get("sender_first_name", "").lower()
    sender_last = msg.get("sender_last_name", "").lower()
    
    for persona in agent_personas:
        agent_username = persona.get("user_name", "").lower()
        agent_first = persona.get("first_name", "").lower()
        agent_last = persona.get("last_name", "").lower()
        
        if sender_username and agent_username and sender_username == agent_username:
            return True
        
        if sender_first and sender_last and agent_first and agent_last:
            if sender_first == agent_first and sender_last == agent_last:
                return True
    
    return False


def load_agent_personas() -> list:
    """Load agent personas from config."""
    personas = []
    base_path = Path(__file__).parent
    
    for agent_config in CONFIG["agents"]:
        persona_path = base_path / agent_config["persona_file"]
        try:
            with open(persona_path, 'r') as f:
                persona_data = json.load(f)
                personas.append(persona_data)
        except Exception as e:
            logger.error(f"Failed to load persona: {e}")
            raise
    
    return personas


def run_supervisor_loop():
    """
    Main supervisor loop.
    
    Continuously polls for messages and runs the graph when new messages arrive.
    """
    global _first_run, _last_message_check
    
    logger.info("Building supervisor graph")
    graph = build_supervisor_graph()
    logger.info("Supervisor graph built successfully")
    
    # Load agent personas for filtering
    agent_personas = load_agent_personas()
    logger.info(f"Loaded {len(agent_personas)} agent personas")
    
    # Use first agent's phone for API calls
    primary_phone = agent_personas[0].get("phone_number", "+37379276083")
    
    # Track all seen message IDs (separate from recent_messages which gets trimmed)
    seen_message_ids = set()
    
    # Initialize state
    state = SupervisorState(
        recent_messages=[],
        group_sentiment="",
        group_metadata=CONFIG["group_metadata"],
        selected_actions=[],
        execution_queue=[],
        current_nodes=None,
        next_nodes=None
    )
    
    logger.info(f"Chat ID: {CHAT_ID}")
    
    try:
        while True:
            current_time = time.time()
            time_since_check = current_time - _last_message_check
            
            # Check if it's time to poll
            if time_since_check >= MESSAGE_CHECK_INTERVAL:
                logger.info(f"Fetching messages...")
                
                if _first_run:
                    logger.info("First run: Initializing group metadata")
                    
                    # Get group metadata
                    participants_data = get_all_group_participants(phone=primary_phone, chat_id=CHAT_ID)
                    if participants_data and participants_data.get("success"):
                        state["group_metadata"] = {
                            "id": CHAT_ID,
                            "name": participants_data.get("chatTitle", CONFIG["group_metadata"]["name"]),
                            "topic": CONFIG["group_metadata"]["topic"],
                            "members": participants_data.get("participantCount", CONFIG["group_metadata"]["members"])
                        }
                    
                    # Get initial messages
                    messages_data = get_chat_messages(phone=primary_phone, chat_id=CHAT_ID, limit=TELEGRAM_FETCH_LIMIT)
                    if messages_data and messages_data.get("success"):
                        new_messages = [parse_telegram_message(msg) for msg in messages_data.get("messages", [])]
                        state["recent_messages"] = new_messages
                        # Track all initial message IDs
                        seen_message_ids.update(msg["message_id"] for msg in new_messages)
                        logger.info(f"Loaded {len(new_messages)} initial messages")
                        
                        # Mark agent messages as processed
                        for msg in state["recent_messages"]:
                            if is_agent_message(msg, agent_personas):
                                msg['processed'] = True
                        
                        # Check if there are unprocessed messages to analyze
                        unprocessed = [msg for msg in state["recent_messages"] if not msg.get('processed', False)]
                        
                        if unprocessed:
                            logger.info(f"Running graph for {len(unprocessed)} initial unprocessed messages...")
                            
                            # Run the graph on initial messages
                            state = graph.invoke(state)
                            
                            # Mark messages as processed
                            for msg in state["recent_messages"]:
                                msg['processed'] = True
                            
                           
                            
                            logger.info("Initial graph execution completed")
                        else:
                            logger.info("All initial messages are from agents, skipping graph execution")
                    
                    _first_run = False
                
                else:
                    # Poll for new messages
                    messages_data = get_chat_messages(phone=primary_phone, chat_id=CHAT_ID, limit=TELEGRAM_FETCH_LIMIT)
                    
                    if messages_data and messages_data.get("success"):
                        new_messages = [parse_telegram_message(msg) for msg in messages_data.get("messages", [])]
                        
                        # Filter out already-seen messages using persistent tracking
                        truly_new = [msg for msg in new_messages if msg["message_id"] not in seen_message_ids]
                        
                        # Add new message IDs to tracking set
                        if truly_new:
                            seen_message_ids.update(msg["message_id"] for msg in truly_new)
                        
                        if truly_new:
                            # Prepend new messages to existing ones (Component B will analyze and trim)
                            state["recent_messages"] = truly_new + state["recent_messages"]
                            logger.info(f"Found {len(truly_new)} new messages")
                            
                            # Mark agent messages as processed
                            for msg in state["recent_messages"]:
                                if is_agent_message(msg, agent_personas) and not msg.get('processed', False):
                                    msg['processed'] = True
                            
                            # Check if there are unprocessed messages
                            unprocessed = [msg for msg in state["recent_messages"] if not msg.get('processed', False)]
                            
                            if unprocessed:
                                logger.info(f"Running graph for {len(unprocessed)} unprocessed messages")
                                
                                # Run the graph
                                state = graph.invoke(state)
                                
                                # Mark messages as processed
                                for msg in state["recent_messages"]:
                                    msg['processed'] = True
                                
                                
                                
                                logger.info("Graph execution completed")
                            else:
                                logger.info("All new messages are from agents, skipping graph execution")
                        else:
                            logger.info("No new messages")
                
                _last_message_check = current_time
            else:
                # Show idle status every 30 seconds
                if int(time_since_check) % 30 == 0 and int(time_since_check) > 0:
                    remaining = MESSAGE_CHECK_INTERVAL - int(time_since_check)
                    logger.info(f"Idle... Next poll in {remaining}s")
            
            # Sleep briefly before next check
            time.sleep(10)
    
    except KeyboardInterrupt:
        logger.info("Supervisor loop stopped by user")
    except Exception as e:
        logger.error(f"Error in supervisor loop: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_supervisor_loop()
