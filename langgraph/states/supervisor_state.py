from typing import TypedDict, List, Optional
from .agent_state import Message
import operator


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
    # Use Annotated with operator.add to allow multiple agents to append actions in parallel
    selected_actions: List[dict]
    execution_queue: List[dict]  # Output of Scheduler, e.g., [{"agent": "troll", "action": ..., "time": ...}]
    
    # Internal tracking
    current_nodes: Optional[List[str]]  # For LangGraph internal tracking
    next_nodes: Optional[List[str]]  # For LangGraph internal tracking
