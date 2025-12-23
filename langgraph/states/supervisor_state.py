from typing import TypedDict, List, Optional, Annotated, Dict
from .agent_state import Message

def add_or_clear(current, new):
    if new == "CLEAR":
        return []
    if current is None: current = []
    return current + new

def merge_recent_actions(current: Dict[str, List[dict]], new: Dict[str, List[dict]]) -> Dict[str, List[dict]]:
    """Merge new agent actions into the existing recent_actions dict."""
    if current is None:
        current = {}
    if new is None:
        return current
    
    result = dict(current)
    for agent_name, actions in new.items():
        if agent_name not in result:
            result[agent_name] = []
        result[agent_name].extend(actions)
    return result

class SupervisorState(TypedDict):
    """
    State for the central Supervisor graph.
    Manages group state, analyzes incoming messages, and dispatches tasks to agents.
    """
    # Group analysis
    group_sentiment: str  #  2-3 sentence summary
    group_metadata: dict  # e.g., {"name": "...", "id": "...", "members": 50, "topic": "..."}
    
    # Message history
    recent_messages: List[Message]  # The global message history from Telegram
    
    # Action tracking
    selected_actions: Annotated[List[dict], add_or_clear]
    execution_queue: List[dict]  # Output of Scheduler, e.g., [{"agent": "troll", "action": ..., "time": ...}]
    
    # Agent action history - tracks recent actions per agent
    # Format: {"agent_name": [{"trigger_id": "...", "justification_of_trigger": "...", 
    #          "target_message": {...}, "action_id": "...", "action_purpose": "...", 
    #          "action_content": "...", "action_timestamp": "..."}]}
    agents_recent_actions: Annotated[Dict[str, List[dict]], merge_recent_actions]
    
    # Internal tracking
    current_nodes: Optional[List[str]]  
    next_nodes: Optional[List[str]]  
