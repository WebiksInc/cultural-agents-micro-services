"""
Actions logging - track all actions performed by agents in groups.
"""
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from .storage import save_json, load_json, get_group_directory


def get_actions_directory(chat_id: str) -> str:
    """
    Get the directory path for actions.
    
    Args:
        chat_id: Telegram chat ID
        
    Returns:
        Path to actions directory
    """
    group_dir = get_group_directory(chat_id)
    actions_dir = os.path.join(group_dir, "actions")
    os.makedirs(actions_dir, exist_ok=True)
    return actions_dir


def save_action(
    chat_id: str,
    agent_name: str,
    group_name: str,
    trigger_detected: str,
    triggered_by_msg: str,
    action_reason: str,
    action_id: str,
    action_content: str,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Save an action performed by an agent.
    
    Args:
        chat_id: Telegram chat ID
        agent_name: Name of the agent that performed the action
        group_name: Name of the group
        trigger_detected: Type of trigger that was detected
        triggered_by_msg: The message that triggered the action
        action_reason: Reason for the action (specific content that caused trigger)
        action_id: ID/type of the action performed
        action_content: Content of the action (e.g., message sent)
        timestamp: ISO timestamp (auto-generated if None)
        
    Returns:
        Dict with success status and action info
    """
    actions_dir = get_actions_directory(chat_id)
    agent_file = os.path.join(actions_dir, f"{agent_name}.json")
    
    # Load existing actions
    actions = load_json(agent_file, default=[])
    
    # Create new action
    new_action = {
        "agent_name": agent_name,
        "group_name": group_name,
        "trigger_detected": trigger_detected,
        "triggered_by_msg": triggered_by_msg,
        "action_reason": action_reason,
        "action_id": action_id,
        "action_content": action_content,
        "timestamp": timestamp or datetime.now().isoformat()
    }
    
    # Append and save
    actions.append(new_action)
    save_json(agent_file, actions)
    
    return {
        "success": True,
        "agent_name": agent_name,
        "action_id": action_id,
        "total_actions": len(actions)
    }


def get_agent_actions(
    chat_id: str,
    agent_name: str,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get all actions for a specific agent.
    
    Args:
        chat_id: Telegram chat ID
        agent_name: Name of the agent
        limit: Maximum number of actions to return (most recent first)
        
    Returns:
        List of action dictionaries
    """
    actions_dir = get_actions_directory(chat_id)
    agent_file = os.path.join(actions_dir, f"{agent_name}.json")
    
    actions = load_json(agent_file, default=[])
    
    # Sort by timestamp (most recent first)
    actions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    if limit:
        return actions[:limit]
    
    return actions


def get_all_actions(
    chat_id: str,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get all actions from all agents in a group.
    
    Args:
        chat_id: Telegram chat ID
        limit: Maximum number of actions to return (most recent first)
        
    Returns:
        List of action dictionaries from all agents
    """
    actions_dir = get_actions_directory(chat_id)
    
    all_actions = []
    
    if not os.path.exists(actions_dir):
        return all_actions
    
    # Read all agent action files
    for filename in os.listdir(actions_dir):
        if filename.endswith(".json"):
            agent_name = filename.replace(".json", "")
            actions = get_agent_actions(chat_id, agent_name)
            all_actions.extend(actions)
    
    # Sort by timestamp (most recent first)
    all_actions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    if limit:
        return all_actions[:limit]
    
    return all_actions


def get_actions_by_trigger(
    chat_id: str,
    trigger_type: str,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get all actions filtered by trigger type.
    
    Args:
        chat_id: Telegram chat ID
        trigger_type: Type of trigger to filter by
        limit: Maximum number of actions to return
        
    Returns:
        List of action dictionaries matching the trigger type
    """
    all_actions = get_all_actions(chat_id)
    
    filtered = [
        action for action in all_actions
        if action.get("trigger_detected") == trigger_type
    ]
    
    if limit:
        return filtered[:limit]
    
    return filtered


def list_agents(chat_id: str) -> List[Dict[str, Any]]:
    """
    List all agents that have performed actions.
    
    Args:
        chat_id: Telegram chat ID
        
    Returns:
        List of agent summaries with action counts
    """
    actions_dir = get_actions_directory(chat_id)
    
    agents = []
    
    if not os.path.exists(actions_dir):
        return agents
    
    for filename in os.listdir(actions_dir):
        if filename.endswith(".json"):
            agent_name = filename.replace(".json", "")
            actions = get_agent_actions(chat_id, agent_name)
            
            # Get unique triggers
            triggers = set(action.get("trigger_detected") for action in actions)
            
            # Get most recent action
            latest = actions[0] if actions else None
            
            agents.append({
                "agent_name": agent_name,
                "total_actions": len(actions),
                "unique_triggers": len(triggers),
                "triggers": list(triggers),
                "last_action": latest.get("timestamp") if latest else None
            })
    
    # Sort by total actions (most active first)
    agents.sort(key=lambda x: x["total_actions"], reverse=True)
    
    return agents


def get_action_statistics(chat_id: str) -> Dict[str, Any]:
    """
    Get statistics about all actions in a group.
    
    Args:
        chat_id: Telegram chat ID
        
    Returns:
        Dict with statistics
    """
    all_actions = get_all_actions(chat_id)
    agents = list_agents(chat_id)
    
    # Count actions by trigger type
    trigger_counts = {}
    for action in all_actions:
        trigger = action.get("trigger_detected")
        trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
    
    # Count actions by action_id
    action_id_counts = {}
    for action in all_actions:
        action_id = action.get("action_id")
        action_id_counts[action_id] = action_id_counts.get(action_id, 0) + 1
    
    return {
        "total_actions": len(all_actions),
        "total_agents": len(agents),
        "actions_by_trigger": trigger_counts,
        "actions_by_type": action_id_counts,
        "most_active_agent": agents[0]["agent_name"] if agents else None,
        "latest_action": all_actions[0].get("timestamp") if all_actions else None
    }
