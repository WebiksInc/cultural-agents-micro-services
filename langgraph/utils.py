"""
Utility functions for LangGraph nodes.

Provides common functionality for loading prompts, model configs, and formatting data.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from logs.logfire_config import get_logger

logger = get_logger(__name__)

# Base paths - utils.py is in langgraph/ folder
LANGGRAPH_DIR = Path(__file__).parent
PROMPTS_DIR = LANGGRAPH_DIR / "prompts"
CONFIG_DIR = LANGGRAPH_DIR / "config"
MODEL_CONFIG_PATH = CONFIG_DIR / "model_config.json"
SUPERVISOR_CONFIG_PATH = CONFIG_DIR / "supervisor_config.json"

def get_all_agent_usernames() -> list:
    """
    Get usernames of all agents in the system.
    
    Returns:
        List of agent usernames from supervisor config
    """
    supervisor_config = load_json_file(SUPERVISOR_CONFIG_PATH)
    return [agent["username"] for agent in supervisor_config["agents"]]

def get_all_agent_names() -> list:
    """
    Get names of all agents in the system.
    
    Returns:
        List of agent names from supervisor config
    """
    supervisor_config = load_json_file(SUPERVISOR_CONFIG_PATH)
    return [agent["name"] for agent in supervisor_config["agents"]]


def load_agent_personas() -> list:
    """
    Load all agent personas from files specified in config.
    
    Returns:
        List of persona dictionaries
    """
    supervisor_config = load_json_file(SUPERVISOR_CONFIG_PATH)
    personas = []
    
    for agent_config in supervisor_config.get("agents", []):
        persona_path = LANGGRAPH_DIR / agent_config["persona_file"]
        try:
            with open(persona_path, 'r', encoding='utf-8') as f:
                persona_data = json.load(f)
                # Ensure username/name from config are also available if needed
                if "username" not in persona_data and "username" in agent_config:
                    persona_data["user_name"] = agent_config["username"]
                personas.append(persona_data)
        except Exception as e:
            logger.error(f"Failed to load persona from {persona_path}: {e}")
    
    return personas


def is_agent_sender(
    message: Optional[Dict[str, Any]] = None,
    display_name: Optional[str] = None,
    agent_personas: Optional[list] = None
) -> bool:
    """
    Check if a sender is one of our agents.
    Can check based on a message object or a display name string.
    
    Args:
        message: Message dict with sender_username, sender_first_name, sender_last_name
        display_name: Display name string (e.g. "Sandra K")
        agent_personas: List of agent personas. If None, loads them.
        
    Returns:
        True if the sender is an agent
    """
    if agent_personas is None:
        agent_personas = load_agent_personas()
        
    # Case 1: Check by display name (used in Component C)
    if display_name:
        display_name = display_name.strip().lower()
        
        for persona in agent_personas:
            # Check against username
            p_username = persona.get("user_name", "").lower()
            if p_username and p_username == display_name:
                return True
                
            # Check against first/last name
            p_first = persona.get("first_name", "").lower()
            p_last = persona.get("last_name", "").lower()
            p_full = f"{p_first} {p_last}".strip()
            
            # Exact match with full name
            if p_full and p_full == display_name:
                return True
                
            # Exact match with first name
            if p_first and p_first == display_name:
                return True
                
            # First word match (e.g. "Sandra K" matches "Sandra")
            if p_first and display_name.split()[0] == p_first:
                return True
                
        return False

    # Case 2: Check by message details (used in Supervisor)
    if message:
        sender_username = message.get("sender_username", "").lower()
        sender_first = message.get("sender_first_name", "").lower()
        sender_last = message.get("sender_last_name", "").lower()
        
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


def get_other_agents_info(current_agent_name: str) -> list:
    """
    Get info about other agents in the system, excluding the current agent.
    
    Args:
        current_agent_name: Name of the current agent to exclude
        
    Returns:
        List of dicts with agent_name, agent_type, and agent_goal
    """
    supervisor_config = load_json_file(SUPERVISOR_CONFIG_PATH)
    return [
        {
            "agent_name": agent["name"],
            "agent_type": agent["type"],
            "agent_goal": agent["agent_goal"]
        }
        for agent in supervisor_config["agents"]
        if agent["name"] != current_agent_name
    ]


def format_other_agents_for_prompt(current_agent_name: str) -> str:
    """
    Format other agents' info as a string for inclusion in prompts.
    
    Args:
        current_agent_name: Name of the current agent to exclude
        
    Returns:
        Formatted string listing other agents, or "None" if no other agents
    """
    other_agents = get_other_agents_info(current_agent_name)
    if not other_agents:
        return "None"
    
    lines = []
    for i, agent in enumerate(other_agents, 1):
        lines.append(f"Agent {i}:")
        lines.append(f"  - Name: {agent['agent_name']}")
        lines.append(f"  - Type: {agent['agent_type']}")
        lines.append(f"  - Goal: {agent['agent_goal']}")
    return "\n".join(lines)


def load_prompt(prompt_path: str) -> str:
    """
    Load a prompt template from file.
    """
    full_path = PROMPTS_DIR / prompt_path
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {full_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading prompt from {full_path}: {e}")
        raise


def load_model_config() -> Dict[str, Any]:
    """
    Load model configuration from config file.
    
    Returns:
        Dictionary mapping node names to their model configurations
        Each config contains: model, temperature, description
    """
    try:
        with open(MODEL_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('nodes', {})
    except FileNotFoundError:
        logger.warning(f"Config file not found: {MODEL_CONFIG_PATH}. Using defaults.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}


def get_model_settings(node_name: str, env_var_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Extracting model settings for a specific node as configured in the model config file.
        
    Returns:
        Dictionary with 'model' and 'temperature' keys
    """
    model_configs = load_model_config()
    node_config = model_configs.get(node_name, {})
    
    # Default settings
    default_model = "gpt-5-nano"
    default_temperature = 0
    
    # Get settings (env var > config > defaults)
    model = node_config.get('model', default_model)
    if env_var_name and os.getenv(env_var_name):
        model = os.getenv(env_var_name)
    
    temperature = node_config.get('temperature', default_temperature)
    model_provider = node_config.get('provider', '')
    
    return {
        'model': model,
        'temperature': temperature,
        'provider': model_provider
    }


def format_message_for_prompt(msg: Dict[str, Any], 
                              include_timestamp: bool = True,
                              include_emotion: bool = True,
                              selected_persona: Dict[str, Any] = None,
                              messages_replies: Dict[str, Any] = None,
                              recent_messages: list = None) -> str:
    """
    Format a message for inclusion in a prompt.
    
    Args:
        msg: Message dictionary with keys: sender_username, sender_first_name, text, date, message_emotion (a single message)
        include_timestamp: Whether to include the timestamp
        include_emotion: Whether to include emotion annotation
        selected_persona: The agent's persona to identify (YOU) messages
        messages_replies: Dict mapping agent message IDs to reply lists
        recent_messages: List of all recent messages (for looking up sender names in replies)
        
    Returns:
        Formatted message string with timestamp, sender, emotion, reactions, and text.
    """
    
    
    # Get sender name (prefer full name, fall back to first_name, then username) and msg_id
    sender_username = msg.get('sender_username', '').strip()
    sender_first_name = msg.get('sender_first_name', '').strip()
    sender_last_name = msg.get('sender_last_name', '').strip()
    msg_id = msg.get('message_id')
    
    if sender_first_name and sender_last_name:
        sender = f"{sender_first_name} {sender_last_name}"
    elif sender_first_name:
        sender = sender_first_name
    elif sender_username:
        sender = sender_username
    else:
        sender = 'Unknown'
    
    # Check if this message is from the current agent (YOU) or another agent
    is_agent = False
    is_other_agent = False
    all_agent_names = get_all_agent_names()
    
    if selected_persona:
        persona_username = selected_persona.get('user_name', '').strip().lower()
        persona_first = selected_persona.get('first_name', '').strip().lower()
        persona_last = selected_persona.get('last_name', '').strip().lower()
        
        if persona_username and sender_username.lower() == persona_username:
            is_agent = True
        elif persona_first and persona_last:
            if sender_first_name.lower() == persona_first and sender_last_name.lower() == persona_last:
                is_agent = True
        
        if is_agent:
            sender = f"{sender} (YOU)"
    
    # If not the current agent, check if sender is another agent in the system
    if not is_agent:
        for agent_name in all_agent_names:
            agent_name_lower = agent_name.lower()
            # Check if sender matches agent name (full name or first name)
            if sender.lower() == agent_name_lower or sender_first_name.lower() == agent_name_lower.split()[0]:
                sender = f"{sender} (Agent)"
                is_other_agent = True
                break
    
    text = msg.get('text', '')
    
    parts = []
    
    # Add message ID
    if msg_id:
        parts.append(f"[id: {msg_id}]")
    
    # Add timestamp if requested
    if include_timestamp:
        date = msg.get('date')
        if isinstance(date, datetime):
            timestamp_str = date.strftime('%Y-%m-%d %H:%M:%S')
        elif date:
            timestamp_str = str(date)
        else:
            timestamp_str = "Unknown time"
        parts.append(f"[{timestamp_str}]")
    
    # Add sender
    parts.append(sender)
    
    # Add emotion if requested
    if include_emotion:
        emotion = msg.get('message_emotion')
        if emotion:
            if isinstance(emotion, dict):
                emotion_str = emotion.get('emotion', 'unknown')
            else:
                emotion_str = str(emotion)
            parts.append(f"[{emotion_str}]")
    
    # Combine: "[timestamp] sender [emotion]: text"
    header = " ".join(parts)
    result = f"{header}: {text}"
    
    # Add reactions if present
    reactions = msg.get('reactions')
    if reactions and len(reactions) > 0:
        reaction_parts = []
        for r in reactions:
            emoji = r.get('emoji', '?')
            count = r.get('count', 0)
            users = r.get('users', [])
            if users:
                # Check if the current agent (selected_persona) reacted
                agent_reacted = False
                if selected_persona:
                    persona_first = selected_persona.get('first_name', '').strip()
                    persona_last = selected_persona.get('last_name', '').strip()
                    persona_full_name = f"{persona_first} {persona_last}".strip()
                    agent_reacted = any(
                        u.lower() == persona_full_name.lower() or u.lower() == persona_first.lower()
                        for u in users
                    )
                
                users_str = ", ".join(users)
                if agent_reacted:
                    reaction_parts.append(f"{emoji}×{count} (incl. {users_str} [YOU])")
                else:
                    reaction_parts.append(f"{emoji}×{count} (incl. {users_str} [Agent])")
            else:
                reaction_parts.append(f"{emoji}×{count}")
        reaction_str = ", ".join(reaction_parts)
        result += f" [Reactions: {reaction_str}]"
    
    # Check if this message is a reply to any message
    reply_to_id = msg.get('replyToMessageId')
    if reply_to_id is not None:
        reply_to_id_str = str(reply_to_id)
        
        # First check if it's a reply to the agent's message
        is_reply_to_agent = False
        if messages_replies and reply_to_id_str in messages_replies:
            result += f" [⤷ Replying to YOUR earlier message id: {reply_to_id_str}]"
            is_reply_to_agent = True
        
        # If not replying to agent, find the sender name from the replied-to messages
        if not is_reply_to_agent:
            replied_to_name = "another user"
            if recent_messages:
                for m in recent_messages:
                    if str(m.get('message_id')) == reply_to_id_str:
                        # Get the sender name
                        first_name = m.get('sender_first_name', '').strip()
                        last_name = m.get('sender_last_name', '').strip()
                        username = m.get('sender_username', '').strip()
                        
                        if first_name and last_name:
                            replied_to_name = f"{first_name} {last_name}"
                        elif first_name:
                            replied_to_name = first_name
                        elif username:
                            replied_to_name = username
                        break
            result += f" [⤷ Replying to {replied_to_name}'s message id: {reply_to_id_str}]"

    return result


def load_json_file(file_path: Path) -> Dict[str, Any]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"JSON file not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        raise


def get_most_recent_message_timestamp(recent_messages: list) -> Optional[str]:
    """
    Extract the timestamp from the most recent message.
    
    Args:
        recent_messages: List of message dictionaries (first is most recent)
        
    Returns:
        Timestamp string in format "YYYY-MM-DD HH:MM:SS" or None if not available
    """
    if not recent_messages or len(recent_messages) == 0:
        return None
    
    most_recent_msg = recent_messages[0]  # First message is the most recent
    if 'date' not in most_recent_msg:
        return None
    
    date_obj = most_recent_msg['date']
    if hasattr(date_obj, 'strftime'):
        return date_obj.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return str(date_obj)


def convert_timestamp_to_iso(timestamp_str: str) -> Optional[str]:
    """
    Convert timestamp from "YYYY-MM-DD HH:MM:SS" to ISO format "YYYY-MM-DDTHH:MM:SS.000Z".
    
    Args:
        timestamp_str: Timestamp string in format "YYYY-MM-DD HH:MM:SS"
        
    Returns:
        ISO format timestamp string or None if conversion fails
    """
    from datetime import datetime
    
    if not timestamp_str:
        return None
    
    try:
        dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    except Exception as e:
        logger.warning(f"Failed to convert timestamp '{timestamp_str}': {e}")
        return None


def get_messages_replies(selected_persona: Dict[str, Any], recent_messages: list) -> Optional[Dict[str, list]]:
    """
    Find all messages that are replies to the agent's messages.
    
    Args:
        selected_persona: Agent's persona dictionary with first_name, last_name
        recent_messages: List of message dictionaries
        
    Returns:
        Dictionary mapping agent's message IDs to lists of reply messages, or None if no replies found
        Example: {"123": [reply_msg1, reply_msg2], "456": [reply_msg3]}
    """
    messages_replies = {}
    agent_name = f"{selected_persona.get('first_name', '')} {selected_persona.get('last_name', '')}".strip()
    
    # Find all messages sent by the agent
    for msg in recent_messages:
        sender = f"{msg.get('sender_first_name', '')} {msg.get('sender_last_name', '')}".strip()
        if sender == agent_name:
            messages_replies[msg['message_id']] = []
    
    if not messages_replies:
        return None
    
    # Find all messages that reply to the agent's messages
    # Note: replyToMessageId is an int, but message_id is a string, so we convert
    for msg in recent_messages:
        reply_to_id = msg.get('replyToMessageId')
        if reply_to_id is not None:
            reply_to_id_str = str(reply_to_id)
            if reply_to_id_str in messages_replies:
                messages_replies[reply_to_id_str].append(msg)
    
    # Return None if no replies found
    if all(not value for value in messages_replies.values()):
        return None
    
    # Log summary
    total_replies = sum(len(replies) for replies in messages_replies.values())
    logger.info(f"{agent_name}: Found {total_replies} replies to {len(messages_replies)} agent messages")
    
    return messages_replies


def format_recent_actions(actions: list, last_n: int = 5) -> str:
    if not actions:
        return "No recent actions recorded yet."
    
    actions_str = []
    
    # Reverse the list so the newest is at the top (more intuitive for the model)
    for i, act in enumerate(reversed(actions[-last_n:])):
        target = act.get('target_message', {})
        # Note: Ensure 'message_id' matches your dictionary key (might be 'id' or 'message_id')
        t_id = target.get('message_id', 'N/A') 
        t_sender = target.get('sender_name', 'Unknown')
        
        trigger = act.get('trigger_id', 'Unknown')
        action = act.get('action_id', 'Unknown')
        purpose = act.get('action_purpose', 'N/A')
        content = act.get('action_content', 'N/A')
        
        # Build a detailed block for each action entry
        entry = (
            f"--- Memory Entry #{i+1} ---\n"
            f"• Target Message ID: {t_id} (Sender: {t_sender})\n"
            f"• Target Message Content: {target.get('text', 'N/A')}\n"
            f"• Trigger: '{trigger}\n"
            f"• Action Taken: '{action}'\n"
            f"• My Reasoning (Purpose): {purpose}\n"
            f"• My Actual Response: \"{content}\"\n"
        )
        actions_str.append(entry)
        
    return "\n".join(actions_str)
