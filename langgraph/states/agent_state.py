from typing import TypedDict, List, Optional
from datetime import datetime


class Message(TypedDict):
    """Structure for individual messages from Telegram."""
    message_id: str
    sender_id: str
    sender_username: str
    sender_first_name: str
    sender_last_name: str
    text: str # message content
    date: datetime
    reactions: Optional[List[dict]]  # List of reactions: [{"emoji": "👍", "count": 2}, ...]
    message_emotion: Optional[str]  # Filled by Component B (Emotion Analysis)
    sender_personality: Optional[dict]  # Filled by Component C on-demand (Personality Analysis)
    processed: Optional[bool]  # Track if message has been analyzed for triggers


class AgentState(TypedDict):
    # Data copied from Supervisor
    recent_messages: List[Message]
    group_sentiment: str
    group_metadata: dict
    
    # Agent configuration
    selected_persona: dict  # JSON file 
    agent_type: str  # e.g., "troll", "active", "manager"
    agent_goal: str
    triggers: dict  # JSON file content for this agent's triggers
    actions: dict  # JSON file content for this agent's possible actions
    
    # Agent processing outputs
    detected_trigger: Optional[dict]  # Output of Trigger Analysis, e.g., {"id": "...", "justification": "..."}
    selected_action: Optional[dict]  # Output of Decision Maker, e.g., {"id": "...", "purpose": "...", "content": "..."}
    
    # Agent prompt and response generation
    agent_prompt: str  # System prompt for this agent
    generated_response: Optional[str]  # Output of E.1 (Text Generator)
    styled_response: Optional[str]  # Output of E.2 (Styler)
    
    # Validation
    validation: Optional[dict]  # Output of Validator, e.g., {"approved": True/False, "explanation": "...", "styled_response": "..."}
    validation_feedback: Optional[str]  # Feedback from failed validation to help E.1 regenerate
    retry_count: int  # Number of times E.1 has been retried due to validation failure
    
    # Internal tracking
    current_node: Optional[str]
    next_node: Optional[str]
