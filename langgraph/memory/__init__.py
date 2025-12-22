"""
Memory system - Long-term storage for Telegram group data.
All data is fetched from Telegram API, nothing hardcoded.
"""

from .storage import (
    DATA_DIR,  # Base data directory path
    ensure_directory,  # Create directory if missing
    save_json,  # Write data to JSON file
    load_json,  # Read data from JSON file
    get_group_directory  # Get path for group's data folder
)

from .group import (
    save_group_metadata,  # Save or update group info
    get_group_metadata,  # Retrieve group info
    save_group_messages,  # Append messages to history
    get_group_messages,  # Retrieve all group messages
    sync_group_messages  # Fetch new messages from Telegram API
)

from .participant import (
    get_participant_messages,  # Get user's messages from group history
    initialize_participants,  # Create JSON files for all participants
    save_personality_analysis,  # Add new personality snapshot
    get_participant_data,  # Retrieve participant's full data
    list_participants  # Get all participants with message counts
)

from .actions import (
    save_action,  # Log an agent action with trigger details
    get_agent_actions,  # Retrieve actions for specific agent
    get_all_actions,  # Get all actions from all agents
    get_actions_by_trigger,  # Filter actions by trigger type
    list_agents,  # List agents with action statistics
    get_action_statistics  # Get comprehensive action analytics
)

__all__ = [
    # Storage
    'DATA_DIR',
    'ensure_directory',
    'save_json',
    'load_json',
    'get_group_directory',
    
    # Group
    'save_group_metadata',
    'get_group_metadata',
    'save_group_messages',
    'get_group_messages',
    'sync_group_messages',
    
    # Participant
    'get_participant_messages',
    'initialize_participants',
    'save_personality_analysis',
    'get_participant_data',
    'list_participants',
    
    # Actions
    'save_action',
    'get_agent_actions',
    'get_all_actions',
    'get_actions_by_trigger',
    'list_agents',
    'get_action_statistics',
]
