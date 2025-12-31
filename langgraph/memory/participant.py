"""
Participant data management - track participants and their personality analysis.
Separates regular participants from agent bots.
"""
import os
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from .storage import save_json, load_json, get_group_directory
from .group import get_group_messages
import logging

logger = logging.getLogger(__name__)




def get_participant_directory(chat_id: str) -> str:
    """
    Get the directory path for participants.
    
    Args:
        chat_id: Telegram chat ID
        
    Returns:
        Path to participant directory
    """
    group_dir = get_group_directory(chat_id)
    participant_dir = os.path.join(group_dir, "participant")
    os.makedirs(participant_dir, exist_ok=True)
    return participant_dir


def get_participant_messages(
    chat_id: str,
    user_id: str
) -> List[Dict[str, Any]]:
    """
    Get all messages a user sent in the group (from group_history).
    Does NOT save to participant JSON - just returns the messages.
    
    Args:
        chat_id: Telegram chat ID
        user_id: User ID to get messages for
        
    Returns:
        List of messages sent by this user
    """
    
    # Get all group messages
    all_messages = get_group_messages(chat_id)
    
    # Filter messages from this user
    user_messages = [
        {
            "date": msg.get("date"),
            "text": msg.get("text") or "",
            "messageId": msg.get("id"),
            "senderUsername": msg.get("senderUsername") or "",
            "senderFirstName": msg.get("senderFirstName") or "",
            "senderLastName": msg.get("senderLastName") or "",
            "senderId": msg.get("senderId")
        }
        for msg in all_messages
        if str(msg.get("senderId")) == str(user_id)
    ]
    
    return user_messages


def initialize_participants(
    chat_id: str,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Create a JSON file for every participant in the group (if doesn't exist).
    Extracts participant info from group_history.
    
    Args:
        chat_id: Telegram chat ID
        verbose: Print progress
        
    Returns:
        Dict with results: {
            "success": bool,
            "participants_created": int,
            "participants_existing": int,
            "total_participants": int
        }
    """
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"Initializing participants for group {chat_id}")
        print(f"{'='*70}\n")
    
    try:
        # Get all group messages
        messages = get_group_messages(chat_id)
        logger.info(f"Initializing participants: Found {len(messages)} messages in group history for {chat_id}")
        
        if not messages:
            if verbose:
                print("⚠️  No messages found in group history")
            return {
                "success": True,
                "participants_created": 0,
                "participants_existing": 0,
                "total_participants": 0
            }
        
        # Find unique participants
        participants = {}
        for msg in messages:
            sender_id = msg.get("senderId")
            if not sender_id:
                continue
            
            if str(sender_id) not in participants:
                participants[str(sender_id)] = {
                    "username": msg.get("senderUsername") or msg.get("senderFirstName") or f"user_{sender_id}"
                }
        
        logger.info(f"Found {len(participants)} unique participants: {list(participants.keys())}")
        
        if verbose:
            print(f"👥 Found {len(participants)} participants in group history")
        
        participant_dir = get_participant_directory(chat_id)
        created = 0
        existing = 0
        
        # Create JSON file for each participant if doesn't exist
        for user_id, info in participants.items():
            participant_path = os.path.join(participant_dir, f"{user_id}.json")
            
            if os.path.exists(participant_path):
                existing += 1
                if verbose:
                    print(f"  ⏭️  {info['username']}: already exists")
            else:
                # Create new participant file
                participant_data = {
                    "user_id": user_id,
                    "username": info["username"],
                    "personality_snapshots": []
                }
                save_json(participant_path, participant_data)
                created += 1
                logger.info(f"Created participant file: {participant_path}")
                if verbose:
                    print(f"  ✅ {info['username']}: created")
        
        if verbose:
            print(f"\n📊 Created: {created}, Existing: {existing}, Total: {len(participants)}")
        
        return {
            "success": True,
            "participants_created": created,
            "participants_existing": existing,
            "total_participants": len(participants)
        }
        
    except Exception as e:
        logger.error(f"Error initializing participants: {e}", exc_info=True)
        if verbose:
            print(f"❌ Error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "participants_created": 0,
            "participants_existing": 0,
            "total_participants": 0
        }


def save_personality_analysis(
    chat_id: str,
    user_id: str,
    big5_results: Optional[Dict[str, Dict[str, Any]]] = None,
    confidence_penalty_config: Optional[Dict[str, Any]] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Save Big5 personality analysis for a participant.
    Adds a new snapshot without erasing previous analyses.
    
    Args:
        chat_id: Telegram chat ID
        user_id: User ID
        big5_results: Dict with big5 traits, each containing score, confidence, justification.
                      Format: {
                          "openness": {"score": 4, "confidence": 0.8, "justification": "..."},
                          "conscientiousness": {"score": 3, "confidence": 0.7, "justification": "..."},
                          ...
                      }
                      If None, generates random values (for testing only).
        confidence_penalty_config: Optional config for message count penalty.
                      Format: {
                          "enabled": True,
                          "min_messages_full_confidence": 15,
                          "penalty_factor": 0.03
                      }
        verbose: Print progress
        
    Returns:
        Dict with success status and snapshot info
    """
    participant_dir = get_participant_directory(chat_id)
    participant_path = os.path.join(participant_dir, f"{user_id}.json")
    
    # Check if participant file exists
    if not os.path.exists(participant_path):
        if verbose:
            print(f"❌ Participant {user_id} not found. Run initialize_participants first.")
        return {
            "success": False,
            "error": f"Participant {user_id} not found"
        }
    
    # Load existing data
    participant_data = load_json(participant_path)
    
    # Get message count
    messages = get_participant_messages(chat_id, user_id)
    message_count = len(messages)
    
    # Generate random values if none provided (for testing only)
    if big5_results is None:
        big5_results = {
            trait: {
                "score": random.randint(1, 5),
                "confidence": round(random.uniform(0.3, 0.9), 2),
                "justification": "Randomly generated for testing"
            }
            for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        }
    
    # Apply confidence penalty based on message count
    if confidence_penalty_config and confidence_penalty_config.get("enabled", False):
        min_messages = confidence_penalty_config.get("min_messages_full_confidence", 15)
        penalty_factor = confidence_penalty_config.get("penalty_factor", 0.03)
        
        if message_count < min_messages:
            penalty = (min_messages - message_count) * penalty_factor
            for trait in big5_results:
                raw_confidence = big5_results[trait].get("confidence", 0.5)
                big5_results[trait]["raw_confidence"] = raw_confidence
                big5_results[trait]["confidence"] = round(max(0, raw_confidence - penalty), 2)
    
    # Calculate overall confidence (average across traits)
    trait_confidences = [big5_results[t].get("confidence", 0.5) for t in big5_results]
    overall_confidence = round(sum(trait_confidences) / len(trait_confidences), 2) if trait_confidences else 0.5
    
    # Create new snapshot with human-readable date
    new_snapshot = {
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "messages_analyzed_count": message_count,
        "personality_analysis": {
            "big5": big5_results
        },
        "overall_confidence": overall_confidence
    }
    
    # Insert at beginning so most recent is first
    participant_data["personality_snapshots"].insert(0, new_snapshot)
    
    # Save
    save_json(participant_path, participant_data)
    
    if verbose:
        username = participant_data.get("username", user_id)
        print(f"✅ Saved personality analysis for {username}")
        print(f"   Messages analyzed: {message_count}")
        print(f"   Overall confidence: {overall_confidence}")
        print(f"   Total snapshots: {len(participant_data['personality_snapshots'])}")
    
    return {
        "success": True,
        "user_id": user_id,
        "username": participant_data.get("username"),
        "messages_analyzed": message_count,
        "overall_confidence": overall_confidence,
        "trait_results": big5_results,
        "total_snapshots": len(participant_data["personality_snapshots"])
    }


def get_participant_data(
    chat_id: str,
    user_id: str
) -> Optional[Dict[str, Any]]:
    """
    Get participant data.
    
    Args:
        chat_id: Telegram chat ID
        user_id: User ID
        
    Returns:
        Participant data dict or None if not found
    """
    participant_dir = get_participant_directory(chat_id)
    participant_path = os.path.join(participant_dir, f"{user_id}.json")
    return load_json(participant_path)


def list_participants(chat_id: str) -> List[Dict[str, Any]]:
    """
    List all participants in a group.
    
    Args:
        chat_id: Telegram chat ID
        
    Returns:
        List of participant summaries
    """
    participant_dir = get_participant_directory(chat_id)
    
    participants = []
    
    if not os.path.exists(participant_dir):
        return participants
    
    for filename in os.listdir(participant_dir):
        if filename.endswith(".json"):
            user_id = filename.replace(".json", "")
            data = get_participant_data(chat_id, user_id)
            if data:
                # Get message count dynamically
                messages = get_participant_messages(chat_id, user_id)
                participants.append({
                    "user_id": data.get("user_id"),
                    "username": data.get("username"),
                    "message_count": len(messages),
                    "snapshots_count": len(data.get("personality_snapshots", []))
                })
    
    return participants
