"""
Utility functions for LangGraph nodes.

Provides common functionality for loading prompts, model configs, and formatting data.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from logs.logfire_config import get_logger

logger = get_logger(__name__)

# Base paths - utils.py is in langgraph/ folder
LANGGRAPH_DIR = Path(__file__).parent
PROMPTS_DIR = LANGGRAPH_DIR / "prompts"
CONFIG_DIR = LANGGRAPH_DIR / "config"
MODEL_CONFIG_PATH = CONFIG_DIR / "model_config.json"


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
                              selected_persona: Dict[str, Any] = None) -> str:
    """
    Format a message for inclusion in a prompt.
    
    Args:
        msg: Message dictionary with keys: sender_username, sender_first_name, text, date, message_emotion
        include_timestamp: Whether to include the timestamp
        include_emotion: Whether to include emotion annotation
        
    Returns:
        Formatted message string with timestamp, sender, emotion, reactions, and text.
    """
    from datetime import datetime
    
    # Get sender name (prefer username, fall back to first_name + last_name, then just first_name)
    sender_username = msg.get('sender_username', '').strip()
    sender_first_name = msg.get('sender_first_name', '').strip()
    sender_last_name = msg.get('sender_last_name', '').strip()
    
    if sender_username:
        sender = sender_username
    elif sender_first_name and sender_last_name:
        sender = f"{sender_first_name} {sender_last_name}"
    elif sender_first_name:
        sender = sender_first_name
    else:
        sender = 'Unknown'
    
    # Check if this message is from the agent (YOU)
    if selected_persona:
        persona_username = selected_persona.get('user_name', '').strip().lower()
        persona_first = selected_persona.get('first_name', '').strip().lower()
        persona_last = selected_persona.get('last_name', '').strip().lower()
        
        is_agent = False
        if persona_username and sender_username.lower() == persona_username:
            is_agent = True
        elif persona_first and persona_last:
            if sender_first_name.lower() == persona_first and sender_last_name.lower() == persona_last:
                is_agent = True
        
        if is_agent:
            sender = f"{sender} (YOU)"
    
    text = msg.get('text', '')
    
    parts = []
    
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
        reaction_parts = [f"{r.get('emoji', '?')}×{r.get('count', 0)}" for r in reactions]
        reaction_str = ", ".join(reaction_parts)
        result += f" [Reactions: {reaction_str}]"
    
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
