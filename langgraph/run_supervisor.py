"""
Main entry point for running the Supervisor graph with polling loop.

This script:
1. Builds the hierarchical supervisor graph
2. Calls Telegram for new messages periodically
3. Runs the graph when new messages arrive
4. Handles the continuous polling loop with sleep intervals
5. Supports Human-in-the-Loop (HITL) approval via interrupt mechanism
"""

import time
import json
import logging
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

from build_graph import build_supervisor_graph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from utils import get_all_agent_usernames, load_agent_personas, is_agent_sender
from states.supervisor_state import SupervisorState
from states.agent_state import Message
from telegram_exm import *
from logs.logfire_config import setup_logfire, get_logger
from memory import save_group_messages, update_messages_emotions, get_group_messages, get_agent_actions, get_group_sentiment
from collections import deque
import time
from logs.logfire_export import export_run_logs
from approval_state import approval_state

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
MAX_INITIAL_ACTIONS = CONFIG["polling"]["max_initial_actions_per_agent"]


def parse_telegram_message(msg_data: dict, agent_usernames: list = None) -> Message:
    """Parse Telegram API message into Message TypedDict."""
    # Parse reactions if present
    reactions = None
    if msg_data.get("reactions"):
        reactions = []
        for r in msg_data.get("reactions", []):
            reaction = {"emoji": r.get("emoji", ""), "count": r.get("count", 0)}
            # Filter users to only include agents (match by username)
            if agent_usernames and r.get("users"):
                agent_usernames_lower = [u.lower() for u in agent_usernames]
                filtered_users = []
                for u in r.get("users", []):
                    username = (u.get("username") or "").lower()
                    if username and username in agent_usernames_lower:
                        first = (u.get("firstName", "") or "").strip()
                        last = (u.get("lastName", "") or "").strip()
                        full_name = f"{first} {last}".strip()
                        filtered_users.append(full_name)
                reaction["users"] = filtered_users
            reactions.append(reaction)
    
    msg_id = msg_data.get("id")
    if msg_id is None or msg_id == "":
        logger.warning(f"Message with missing ID detected: {msg_data}")
        msg_id = f"UNKNOWN_{msg_data.get('date', 'NO_DATE')}"
    
    # Preserve original ISO timestamp
    original_timestamp = msg_data.get("date", "")
    
    # Load existing emotion if present (from previous Component B analysis)
    existing_emotion = msg_data.get("message_emotion")
    
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
        message_emotion=existing_emotion,
        sender_personality=None,
        processed=False,
        replyToMessageId = msg_data.get("replyToMessageId", None)
    )


# HITL Approval check interval (seconds)
APPROVAL_CHECK_INTERVAL = 2


def invoke_graph_with_hitl(graph, state: dict, config: dict) -> dict:
    """
    Invoke the graph with Human-in-the-Loop support.
    
    If the graph hits an interrupt (human_approval node), this function:
    1. Stores the pending approval in approval_state
    2. Waits for operator response
    3. Resumes the graph with the operator's decision
    
    Args:
        graph: The compiled LangGraph
        state: The current SupervisorState
        config: The graph config with thread_id
        
    Returns:
        The final state after graph completion
    """
    # Invoke graph - may hit interrupt
    result = graph.invoke(state, config)
    
    # Check if we hit an interrupt
    if "__interrupt__" in result:
        interrupt_data = result["__interrupt__"][0].value
        logger.info(f"🔔 HITL: Graph interrupted with {interrupt_data.get('total_pending', 0)} pending approvals")
        
        # Store pending approval for Streamlit to pick up
        approval_state.set_pending(config, interrupt_data)
        
        # Wait for operator response
        logger.info("⏳ HITL: Waiting for operator approval...")
        while not approval_state.has_response():
            time.sleep(APPROVAL_CHECK_INTERVAL)
        
        # Get operator response and resume
        operator_response = approval_state.get_response()
        logger.info(f"✅ HITL: Received operator response, resuming graph...")
        
        # Resume the graph with operator's decision
        result = graph.invoke(Command(resume=operator_response), config)
        
        # Clear approval state
        approval_state.clear()
        logger.info("HITL: Graph resumed and completed")
    
    return result


def run_supervisor_loop():
    # STEP 1: INITIALIZATION 
    logger.info("Starting Supervisor initialization...")
    
    # Track when the run started for log export
    run_start_time = datetime.utcnow()
    
    # 1. Build graph with checkpointer for HITL support
    checkpointer = InMemorySaver()
    graph = build_supervisor_graph(checkpointer=checkpointer)
    logger.info("Supervisor graph built successfully with HITL support")
    
    agent_personas = load_agent_personas()
    logger.info(f"Loaded {len(agent_personas)} agent personas")
    
    # Get agent usernames for filtering reaction users
    agent_usernames = get_all_agent_usernames()
    
    primary_phone = agent_personas[0].get("phone_number", None)
   

    # This automatically discards the oldest IDs when we reach 1000
    seen_message_ids = deque(maxlen=1000)
    
    # 2. Initialize State
    # Load group_sentiment from memory if available
    stored_sentiment = get_group_sentiment(CHAT_ID)
    initial_sentiment = stored_sentiment if stored_sentiment else ""
    if stored_sentiment:
        logger.info(f"Loaded group_sentiment from memory")
    
    state = SupervisorState(
        recent_messages=[],
        group_sentiment=initial_sentiment,
        group_metadata={"id": CHAT_ID, "name": "", "topic": "", "members": 0},
        selected_actions=[],
        execution_queue=[],
        agents_recent_actions={},  # Track recent actions per agent
        current_nodes=None,
        next_nodes=None
    )
    logger.info(f"Target Chat ID: {CHAT_ID}")
    
    # 2b. Load recent actions from disk for each agent
    logger.info(f"Loading last {MAX_INITIAL_ACTIONS} actions per agent...")
    agents_recent_actions = {}
    for agent_config in CONFIG["agents"]:
        # Load persona to get first_name - this matches how build_graph.py keys agents
        persona_file = agent_config.get("persona_file")
        if persona_file:
            persona_path = Path(__file__).parent / persona_file
            with open(persona_path, 'r') as f:
                persona = json.load(f)
            # Use first_name if available, else fallback to config name
            agent_display_name = persona.get("first_name") or agent_config.get("name", "").split()[0]
        else:
            agent_display_name = agent_config.get("name", "").split()[0]
        
        if agent_display_name:
            saved_actions = get_agent_actions(CHAT_ID, agent_display_name, limit=MAX_INITIAL_ACTIONS)
            if saved_actions:
                # Transform saved format to ActionRecord format
                action_records = []
                for action in saved_actions:
                    # Build target_message from saved data
                    target_msg = None
                    if action.get('triggered_by_msg_id'):
                        target_msg = {
                            'message_id': action.get('triggered_by_msg_id'),
                            'text': action.get('triggered_by_msg', '')
                        }
                    
                    action_record = {
                        'trigger_id': action.get('trigger_detected', 'unknown'),
                        'trigger_justification': action.get('action_reason', ''),
                        'target_message': target_msg,
                        'action_id': action.get('action_id', 'unknown'),
                        'action_purpose': action.get('action_reason', ''),
                        'action_content': action.get('action_content', ''),
                        'action_timestamp': action.get('timestamp')
                    }
                    action_records.append(action_record)
                
                agents_recent_actions[agent_display_name] = action_records
                logger.info(f"Loaded {len(action_records)} actions for {agent_display_name}")
    
    state['agents_recent_actions'] = agents_recent_actions

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
        # Save raw messages to memory (file system) so Component C can find participants
        fetched_messages_raw = messages_data.get("messages", [])
        if fetched_messages_raw:
            save_group_messages(CHAT_ID, fetched_messages_raw)
            
        # Load messages from group_history (may have emotions from previous runs)
        messages_from_storage = get_group_messages(CHAT_ID, limit=TELEGRAM_FETCH_LIMIT)
        initial_messages = [parse_telegram_message(msg, agent_usernames) for msg in messages_from_storage]
        state["recent_messages"] = initial_messages
        
        # --- CHANGE 2: Load initial IDs into deque ---
        for msg in initial_messages:
            seen_message_ids.append(msg["message_id"])
            
        logger.info(f"Loaded {len(initial_messages)} initial messages")
        
        # Mark agent messages as processed
        for msg in state["recent_messages"]:
            if is_agent_sender(message=msg, agent_personas=agent_personas):
                msg['processed'] = True
        
        # Check for unprocessed messages in history to react to
        unprocessed = [msg for msg in state["recent_messages"] if not msg.get('processed', False)]
        
        if unprocessed:
            logger.info(f"Running graph for {len(unprocessed)} initial unprocessed messages...")
            # Use HITL-aware invocation with unique thread_id
            config = {"configurable": {"thread_id": f"init-{uuid4()}"}}
            state = invoke_graph_with_hitl(graph, state, config)
            
            # Persist emotion analysis to group_history
            update_messages_emotions(CHAT_ID, state["recent_messages"])
            
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
                    # Save raw messages to memory (file system) so Component C can find participants
                    fetched_messages_raw = messages_data.get("messages", [])
                    if fetched_messages_raw:
                        save_group_messages(CHAT_ID, fetched_messages_raw)
                        
                    # Load messages from group_history (may have emotions from previous runs)
                    messages_from_storage = get_group_messages(CHAT_ID, limit=TELEGRAM_FETCH_LIMIT)
                    raw_messages = [parse_telegram_message(msg, agent_usernames) for msg in messages_from_storage]
                    
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
                        logger.info(f"Found {len(new_messages)} new messages")
                        
                        # Mark agent messages as processed
                        for msg in state["recent_messages"]:
                            if is_agent_sender(message=msg, agent_personas=agent_personas) and not msg.get('processed', False):
                                msg['processed'] = True
                        
                        # Process if actionable messages exist
                        unprocessed = [msg for msg in state["recent_messages"] if not msg.get('processed', False)]
                        
                        if unprocessed:
                            logger.info(f"Running graph for {len(unprocessed)} new messages")
                            # Use HITL-aware invocation with unique thread_id
                            config = {"configurable": {"thread_id": f"poll-{uuid4()}"}}
                            state = invoke_graph_with_hitl(graph, state, config)
                            
                            # Persist emotion analysis to group_history
                            update_messages_emotions(CHAT_ID, state["recent_messages"])
                            
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
            
            time.sleep(15)

    except KeyboardInterrupt:
        logger.info("Supervisor loop stopped by user")
        # Export logs for this run
        logger.info("📤 Exporting run logs...")
        export_run_logs(run_start_time)
    except Exception as e:
        logger.error(f"Error in supervisor loop: {e}", exc_info=True)
        # Export logs even on error
        logger.info("📤 Exporting run logs after error...")
        export_run_logs(run_start_time)
        raise

if __name__ == "__main__":
    run_supervisor_loop()
