"""
Basic storage utilities for JSON files.
"""
import os
import json
from typing import Any


# Configuration
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def ensure_directory(path: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def save_json(file_path: str, data: Any) -> None:
    """Save data to JSON file with pretty formatting."""
    ensure_directory(os.path.dirname(file_path))
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(file_path: str, default: Any = None) -> Any:
    """Load data from JSON file."""
    if not os.path.exists(file_path):
        return default
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_group_directory(chat_id: str) -> str:
    """Get the directory path for a specific group."""
    return os.path.join(DATA_DIR, str(chat_id))
