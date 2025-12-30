"""
Simple script to sync group data and analyze participants.
"""
from memory import (
    sync_group_messages,
    save_group_metadata,
    initialize_participants,
    save_personality_analysis,
    list_participants,
    save_action
)

# Configuration
PHONE = "+37379276083"
CHAT_ID = "3389864729"

# Sync group messages from Telegram
result = sync_group_messages(PHONE, CHAT_ID, verbose=False)

if result["success"]:
    # Save group metadata with custom fields
    save_group_metadata(
        chat_id=CHAT_ID,
        chat_title=result["chat_title"],
        total_messages=result["total_fetched"]
    )
    
    # Initialize participant files
    initialize_participants(CHAT_ID, verbose=False)
    
    # Get all participants
    participants = list_participants(CHAT_ID)
    
    # Save personality analysis for each participant
    for participant in participants:
        save_personality_analysis(
            chat_id=CHAT_ID,
            user_id=participant["user_id"],
            verbose=False
        )
    
    # Save sample agent actions (mock data)
    save_action(
        chat_id=CHAT_ID,
        agent_name="SandraK9",
        group_name=result["chat_title"],
        trigger_detected="direct_mention",
        triggered_by_msg="Sample message",
        action_reason="User mentioned Sandra",
        action_id="answer_direct_mention",
        action_content="Sample response"
    )
