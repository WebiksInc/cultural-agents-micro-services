"""
Main entry point for running the Supervisor graph with polling loop.

This script:
1. Builds the hierarchical supervisor graph
2. Calls Telegram for new messages periodically
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

# Configure logging
logging.basicConfig(level=logging.INFO)

from build_graph import build_supervisor_graph
from states.supervisor_state import SupervisorState
from states.agent_state import Message
from telegram_exm import *
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


def parse_telegram_message(msg_data: dict) -> Message:
    """Parse Telegram API message into Message TypedDict."""
    # Parse reactions if present
    reactions = None
    if msg_data.get("reactions"):
        reactions = [
            {"emoji": r.get("emoji", ""), "count": r.get("count", 0)}
            for r in msg_data.get("reactions", [])
        ]
    
    msg_id = msg_data.get("id")
    if msg_id is None or msg_id == "":
        logger.warning(f"Message with missing ID detected: {msg_data}")
        msg_id = f"UNKNOWN_{msg_data.get('date', 'NO_DATE')}"
    
    # Preserve original ISO timestamp
    original_timestamp = msg_data.get("date", "")
    
    return Message(
        message_id=str(msg_id),
        sender_id=msg_data.get("senderId") or "",
        sender_username=msg_data.get("senderUsername") or "",
        sender_first_name=msg_data.get("senderFirstName") or "",
        sender_last_name=msg_data.get("senderLastName") or "",
        text=msg_data.get("text") or "",
        date=datetime.fromisoformat(original_timestamp.replace("Z", "+00:00")) if original_timestamp else datetime.now(),
        timestamp=original_timestamp if original_timestamp else datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        reactions=reactions,
        message_emotion=None,
        sender_personality=None,
        processed=False,
        replyToMessageId = msg_data.get("replyToMessageId", None)
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

from collections import deque
import time

def run_supervisor_loop():
    # STEP 1: INITIALIZATION 
    logger.info("Starting Supervisor initialization...")
    
    # 1. Build graph and dependencies
    graph = build_supervisor_graph()
    logger.info("Supervisor graph built successfully")
    
    agent_personas = load_agent_personas()
    logger.info(f"Loaded {len(agent_personas)} agent personas")
    
    primary_phone = agent_personas[0].get("phone_number", None)
   

    # This automatically discards the oldest IDs when we reach 1000
    seen_message_ids = deque(maxlen=1000)
    
    # 2. Initialize State
    state = SupervisorState(
        recent_messages=[],
        group_sentiment="",
        group_metadata={"id": CHAT_ID, "name": "", "topic": "", "members": 0},
        selected_actions=[],
        execution_queue=[],
        current_nodes=None,
        next_nodes=None
    )
    logger.info(f"Target Chat ID: {CHAT_ID}")

    # 3. Fetch Group Metadata (Run once)
    logger.info("Fetching group metadata from Telegram API...")
    participants_data = get_all_group_participants(phone=primary_phone, chat_id=CHAT_ID)
    
    if participants_data and participants_data.get("success"):
        state["group_metadata"] = {
            "id": CHAT_ID,
            "name": participants_data.get("chatTitle", "Unknown Group"),
            "topic": participants_data.get("chatDescription", "No description available"),
            "members": participants_data.get("participantsCount", 0)
        }
        logger.info(f"Group metadata initialized: {state['group_metadata']['name']} ({state['group_metadata']['members']} members)")
    else:
        logger.warning("Failed to fetch group metadata from API, using defaults")
        state["group_metadata"] = {
            "id": CHAT_ID,
            "name": "Unknown Group",
            "topic": "No description available",
            "members": 0
        }

    # 4. Fetch Initial History (Run once)
    logger.info("Fetching initial message history...")
    messages_data = get_chat_messages(phone=primary_phone, chat_id=CHAT_ID, limit=TELEGRAM_FETCH_LIMIT)
    
    if messages_data and messages_data.get("success"):
        initial_messages = [parse_telegram_message(msg) for msg in messages_data.get("messages", [])]
        state["recent_messages"] = initial_messages
        
        # --- CHANGE 2: Load initial IDs into deque ---
        for msg in initial_messages:
            seen_message_ids.append(msg["message_id"])
            
        logger.info(f"Loaded {len(initial_messages)} initial messages")
        
        # Mark agent messages as processed
        for msg in state["recent_messages"]:
            if is_agent_message(msg, agent_personas):
                msg['processed'] = True
        
        # Check for unprocessed messages in history to react to
        unprocessed = [msg for msg in state["recent_messages"] if not msg.get('processed', False)]
        
        if unprocessed:
            logger.info(f"Running graph for {len(unprocessed)} initial unprocessed messages...")
            state = graph.invoke(state)
            
            # Mark processed locally after run
            for msg in state["recent_messages"]:
                msg['processed'] = True
            
            logger.info("Initial graph execution completed")
        else:
            logger.info("No actionable initial messages found")

    logger.info("Initialization complete. Entering main fetching loop.")

    # STEP 2: MAIN FETCHING LOOP 
    last_message_check = 0
    
    try:
        while True:
            current_time = time.time()
            time_since_check = current_time - last_message_check
            
            if time_since_check >= MESSAGE_CHECK_INTERVAL:
                logger.info("Fetching new messages...")
                
                messages_data = get_chat_messages(phone=primary_phone, chat_id=CHAT_ID, limit=TELEGRAM_FETCH_LIMIT)
                
                if messages_data and messages_data.get("success"):
                    raw_messages = [parse_telegram_message(msg) for msg in messages_data.get("messages", [])]
                    
                    # Log IDs for debugging
                    all_ids = [msg["message_id"] for msg in raw_messages]
                    logger.info(f"📥 Fetched {len(raw_messages)} messages. IDs: {all_ids}")
                    
                    # --- CHANGE 3: Simplified logic ---
                    # Only filter based on what is NOT in our seen history (deque)
                    # No clearing, no intersection logic.
                    new_messages = []
                    for msg in raw_messages:
                        if msg["message_id"] not in seen_message_ids:
                            new_messages.append(msg)
                            # Add to seen immediately so we don't process it again next loop
                            seen_message_ids.append(msg["message_id"])
                    
                    if new_messages:
                        # Prepend new messages to state
                        state["recent_messages"] = new_messages + state["recent_messages"]
                        logger.info(f"Found {len(new_messages)} truly new messages")
                        
                        # Mark agent messages as processed
                        for msg in state["recent_messages"]:
                            if is_agent_message(msg, agent_personas) and not msg.get('processed', False):
                                msg['processed'] = True
                        
                        # Process if actionable messages exist
                        unprocessed = [msg for msg in state["recent_messages"] if not msg.get('processed', False)]
                        
                        if unprocessed:
                            logger.info(f"Running graph for {len(unprocessed)} new messages")
                            state = graph.invoke(state)
                            
                            # Mark processed locally
                            for msg in state["recent_messages"]:
                                msg['processed'] = True
                                
                            logger.info("Graph execution completed")
                        else:
                            logger.info("All new messages are internal/agent messages, skipping")
                    else:
                        logger.info("No new messages found (all IDs already seen)")
                
                last_message_check = current_time
                
            else:
                # Idle logging
                if int(time_since_check) % 30 == 0 and int(time_since_check) > 0:
                    remaining = MESSAGE_CHECK_INTERVAL - int(time_since_check)
                    logger.info(f"Idle... Next pull in {remaining}s")
            
            time.sleep(30)

    except KeyboardInterrupt:
        logger.info("Supervisor loop stopped by user")
    except Exception as e:
        logger.error(f"Error in supervisor loop: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    run_supervisor_loop()
