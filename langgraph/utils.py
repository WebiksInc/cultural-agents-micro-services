"""
Utility functions for LangGraph nodes.

Provides common functionality for loading prompts, model configs, and formatting data.
"""

import json
import logging
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
    
    Args:
        prompt_path: Relative path from langgraph/prompts/ directory
                    (e.g., "agent_graph/trigger_analysis_prompt.txt")
    
    Returns:
        The prompt template as a string
        
    Raises:
        FileNotFoundError: If prompt file doesn't exist
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
    Get model settings for a specific node.
    
    Args:
        node_name: Name of the node (e.g., "trigger_analysis", "component_B")
        env_var_name: Optional environment variable name to override model setting
        
    Returns:
        Dictionary with 'model' and 'temperature' keys
    """
    import os
    
    model_configs = load_model_config()
    node_config = model_configs.get(node_name, {})
    
    # Default settings
    default_model = "gpt-4o-mini"
    default_temperature = 0
    
    # Get settings (env var > config > defaults)
    model = node_config.get('model', default_model)
    if env_var_name and os.getenv(env_var_name):
        model = os.getenv(env_var_name)
    
    temperature = node_config.get('temperature', default_temperature)
    
    return {
        'model': model,
        'temperature': temperature
    }


def format_message_for_prompt(msg: Dict[str, Any], 
                              include_timestamp: bool = True,
                              include_emotion: bool = True) -> str:
    """
    Format a message for inclusion in a prompt.
    
    Args:
        msg: Message dictionary with keys: sender_username, sender_first_name, text, date, message_emotion
        include_timestamp: Whether to include the timestamp
        include_emotion: Whether to include emotion annotation
        
    Returns:
        Formatted message string (e.g., "[2025-11-11 10:00:00] alice [joy]: Hello!")
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
    return f"{header}: {text}"


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """
    Load and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
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
