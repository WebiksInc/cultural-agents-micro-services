"""
Group data management - fetch and store group information from Telegram.
All data comes from Telegram API, nothing is hardcoded.
"""
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to import telegram_exm_yair
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .storage import save_json, load_json, get_group_directory
import logging

logger = logging.getLogger(__name__)



def save_group_metadata(
    chat_id: str,
    chat_title: str = None,
    **additional_fields
) -> None:
    """
    Save or update group metadata.
    
    Args:
        chat_id: Telegram chat ID
        chat_title: Chat title from Telegram (optional for updates)
        **additional_fields: Any additional fields to save/update
    """
    group_dir = get_group_directory(chat_id)
    metadata_path = os.path.join(group_dir, "group_metadata.json")
    
    # Load existing metadata or create new
    existing = load_json(metadata_path, default={})
    
    # Prepare updates
    metadata = {
        "id": chat_id,
        **existing  # Keep all existing fields
    }
    
    # Set created_at only if new
    if "created_at" not in metadata:
        metadata["created_at"] = datetime.now().isoformat()
    
    # Update name if provided
    if chat_title is not None:
        metadata["name"] = chat_title
    
    # Apply additional fields
    metadata.update(additional_fields)
    
    save_json(metadata_path, metadata)


def get_group_metadata(chat_id: str) -> Optional[Dict[str, Any]]:
    """
    Get group metadata.
    
    Args:
        chat_id: Telegram chat ID
        
    Returns:
        Metadata dict or None if not found
    """
    group_dir = get_group_directory(chat_id)
    metadata_path = os.path.join(group_dir, "group_metadata.json")
    return load_json(metadata_path)


def save_group_messages(
    chat_id: str,
    messages: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Save group messages (appends to existing, avoids duplicates).
    
    Args:
        chat_id: Telegram chat ID
        messages: List of message dicts from Telegram API
        
    Returns:
        Dict with new_count and last_message_id
    """
    group_dir = get_group_directory(chat_id)
    history_path = os.path.join(group_dir, "group_history.json")
    
    # Load existing messages
    existing_messages = load_json(history_path, default=[])
    
    # Get existing message IDs to avoid duplicates
    existing_ids = {msg.get('id') for msg in existing_messages}
    
    # Add only new messages
    new_messages = [msg for msg in messages if msg.get('id') not in existing_ids]
    
    if new_messages:
        existing_messages.extend(new_messages)
        # Sort by message ID (descending - most recent first)
        existing_messages.sort(key=lambda x: x.get('id', 0), reverse=True)
        save_json(history_path, existing_messages)
        logger.info(f"Saved {len(new_messages)} new messages to group history. Total: {len(existing_messages)}")
    else:
        logger.info("No new messages to save to group history.")
    
    # Get the last message ID (highest ID)
    last_message_id = max(msg.get('id', 0) for msg in existing_messages) if existing_messages else None
    
    return {
        "new_count": len(new_messages),
        "last_message_id": last_message_id,
        "total_messages": len(existing_messages)
    }


def get_group_messages(
    chat_id: str,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get stored group messages.
    
    Args:
        chat_id: Telegram chat ID
        limit: Maximum number of messages to return (most recent)
        
    Returns:
        List of messages
    """
    group_dir = get_group_directory(chat_id)
    history_path = os.path.join(group_dir, "group_history.json")
    messages = load_json(history_path, default=[])
    
    # Messages are stored with most recent first
    if limit:
        return messages[:limit]
    return messages


def update_message_fields(
    chat_id: str,
    message_id: int,
    **fields
) -> bool:
    """
    Update specific fields in a message.
    
    Args:
        chat_id: Telegram chat ID
        message_id: Message ID to update
        **fields: Fields to update/add (e.g., emotion="happy", justification="smiling emoji")
        
    Returns:
        True if message found and updated, False otherwise
    
    Example:
        update_message_fields(
            chat_id="3389864729",
            message_id=74,
            emotion="positive",
            justification="Enthusiastic tone about Italy"
        )
    """
    group_dir = get_group_directory(chat_id)
    history_path = os.path.join(group_dir, "group_history.json")
    
    messages = load_json(history_path, default=[])
    
    # Find and update the message
    updated = False
    for msg in messages:
        if msg.get('id') == message_id:
            msg.update(fields)
            updated = True
            break
    
    if updated:
        save_json(history_path, messages)
    
    return updated


def sync_group_messages(
    phone: str,
    chat_id: str,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Sync group messages from Telegram API.
    Handles both initial fetch and incremental updates automatically.
    Always fetches maximum messages (1000 - API limit) to capture all unsaved messages.
    
    Args:
        phone: Phone number for authentication
        chat_id: Telegram chat ID
        verbose: Print progress
        
    Returns:
        Dict with results: {
            "success": bool,
            "chat_title": str,
            "total_fetched": int,
            "new_messages": int,
            "is_initial_fetch": bool,
            "error": str (if failed)
        }
    """
    from telegram_exm_yair import get_chat_messages, get_all_group_participants
    
    # Check if this is initial fetch or incremental update
    existing_messages = get_group_messages(chat_id)
    is_initial_fetch = len(existing_messages) == 0
    
    # Get last saved message ID for optimization
    metadata = get_group_metadata(chat_id)
    last_saved_id = metadata.get('last_message_id') if metadata else None
    
    # Always fetch maximum messages to capture all unsaved messages (API limit: 1000)
    limit = 1000
    
    if verbose:
        mode = "Initial fetch" if is_initial_fetch else "Incremental sync"
        print(f"\n{'='*70}")
        print(f"{mode} for group {chat_id}")
        print(f"{'='*70}\n")
        if last_saved_id:
            print(f"Last saved message ID: {last_saved_id}")
        print(f"Fetching up to {limit} messages...")
    
    try:
        # Fetch chat description from participants API
        chat_description = ""
        try:
            participants_response = get_all_group_participants(phone, chat_id)
            if participants_response.get('success'):
                chat_description = participants_response.get('chatDescription', '')
        except Exception as e:
            if verbose:
                print(f"⚠️  Could not fetch chat description: {str(e)}")
        
        response = get_chat_messages(
            phone=phone,
            chat_id=chat_id,
            limit=limit
        )
        
        if not response.get('success'):
            error_msg = response.get('error', 'Unknown error')
            if verbose:
                print(f"❌ Error: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "total_fetched": 0,
                "is_initial_fetch": is_initial_fetch
            }
        
        chat_title = response.get('chatTitle', f'Chat {chat_id}')
        messages = response.get('messages', [])
        
        if verbose:
            print(f"📊 Fetched {len(messages)} messages from API")
        
        # Quick check: if we have a last_saved_id and it's in the fetched messages,
        # we can optimize by only processing newer messages
        if last_saved_id and messages:
            # Filter out messages we already have
            new_only = [msg for msg in messages if msg.get('id', 0) > last_saved_id]
            if len(new_only) < len(messages):
                if verbose:
                    print(f"🔍 Found {len(new_only)} new messages (skipping {len(messages) - len(new_only)} already saved)")
                messages = new_only
        
        # Save messages (deduplication handled automatically)
        save_result = save_group_messages(chat_id, messages)
        new_count = save_result["new_count"]
        last_message_id = save_result["last_message_id"]
        total_messages = save_result["total_messages"]
        
        # Save metadata
        metadata_updates = {
            "chat_title": chat_title,
            "chat_description": chat_description,
            "last_sync": datetime.now().isoformat(),
            "last_message_id": last_message_id,
            "total_messages": total_messages
        }
        
        save_group_metadata(chat_id=chat_id, **metadata_updates)
        
        if verbose:
            if new_count > 0:
                print(f"✅ Saved {new_count} new messages")
            else:
                print(f"ℹ️  No new messages (all {len(messages)} already stored)")
        
        return {
            "success": True,
            "chat_title": chat_title,
            "total_fetched": len(messages),
            "new_messages": new_count,
            "is_initial_fetch": is_initial_fetch
        }
        
    except Exception as e:
        if verbose:
            print(f"❌ Exception: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "total_fetched": 0,
            "is_initial_fetch": is_initial_fetch
        }
