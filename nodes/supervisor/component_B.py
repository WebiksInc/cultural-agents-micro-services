"""
Component B - Emotion/Sentiment Analysis Node

Analyzes emotions in group messages and generates overall group sentiment.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from langchain.chat_models import init_chat_model

# Configure logging
logger = logging.getLogger(__name__)

# Load prompt template
PROMPT_DIR = Path(__file__).parent.parent.parent / "prompts" / "component_B"
PROMPT_PATH = PROMPT_DIR / "emotion_analysis.txt"

def load_prompt() -> str:
    """Load the emotion analysis prompt from file."""
    try:
        with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {PROMPT_PATH}")
        raise
    except Exception as e:
        logger.error(f"Error loading prompt: {e}")
        raise


def format_message_for_prompt(msg: Dict[str, Any], include_emotion: bool = True) -> str:
    """Format a single message for the prompt."""
    sender = msg.get('sender_username', msg.get('sender_first_name', 'Unknown'))
    text = msg.get('text', '')
    emotion_str = ""
    
    if include_emotion and msg.get('message_emotion'):
        emotion = msg['message_emotion']
        if isinstance(emotion, dict):
            emotion_str = f" [CLASSIFIED: {emotion.get('emotion', 'unknown')}]"
        else:
            emotion_str = f" [CLASSIFIED: {emotion}]"
    
    return f"{sender}: {text}{emotion_str}"


def emotion_analysis_node(state: Dict[str, Any]) -> None:
    """
    Component B: Emotion/Sentiment Analysis Node
    
    Analyzes emotions for unclassified messages and generates group sentiment.
    Modifies the state in-place.
    
    Args:
        state: SupervisorState dict containing recent_messages and group_metadata
    """
    logger.info("Starting Component B - Emotion + Sentiment Analysis")
    
    recent_messages = state.get('recent_messages', [])
    group_metadata = state.get('group_metadata', {})
    
    # Filter unclassified messages
    unclassified_indices = []
    unclassified_messages = []
    
    for idx, msg in enumerate(recent_messages):
        if msg.get('message_emotion') is None:
            unclassified_indices.append(idx)
            unclassified_messages.append(msg)
    
    # If no unclassified messages, skip LLM call but still generate group sentiment if needed
    if not unclassified_messages:
        logger.info("No unclassified messages found. Skipping emotion analysis.")
        if not state.get('group_sentiment'):
            state['group_sentiment'] = "No recent messages to analyze."
        return
    
    logger.info(f"Found {len(unclassified_messages)} unclassified messages")
    
    # Extract group metadata
    group_name = group_metadata.get('name', 'Unknown Group')
    group_topic = group_metadata.get('topic', 'General discussion')
    member_count = group_metadata.get('members', 'Unknown')
    
    # Format conversation history (all messages for context)
    conversation_lines = []
    for msg in recent_messages:
        conversation_lines.append(format_message_for_prompt(msg, include_emotion=True))
    conversation_history = "\n".join(conversation_lines)
    
    # Format unclassified messages
    unclassified_lines = []
    for msg in unclassified_messages:
        sender = msg.get('sender_username', msg.get('sender_first_name', 'Unknown'))
        text = msg.get('text', '')
        msg_id = msg.get('message_id', 'unknown')
        unclassified_lines.append(f"[ID: {msg_id}] {sender}: {text}")
    unclassified_text = "\n".join(unclassified_lines)
    
    # Build prompt
    prompt_template = load_prompt()
    prompt = prompt_template.format(
        group_name=group_name,
        group_topic=group_topic,
        member_count=member_count,
        conversation_history=conversation_history,
        unclassified_messages=unclassified_text
    )
    
    try:
        # Initialize model
        model_name = os.getenv('COMPONENT_B_MODEL', 'gpt-5-nano')
        logger.info(f"Using model: {model_name}")
        
        model = init_chat_model(
            model=model_name,
            model_provider="openai",
            temperature=0
        )
        
        # Call LLM
        response = model.invoke([HumanMessage(content=prompt)])
        response_text = response.content
        
        logger.info(f"Received LLM response: {response_text[:200]}...")
        
        # Parse JSON response
        try:
            result = json.loads(response_text)
            message_emotions = result.get('message_emotions', [])
            group_sentiment = result.get('group_sentiment', 'ERROR: No sentiment provided')
            
            # Update state with emotions
            emotion_map = {item['message_id']: item for item in message_emotions}
            
            for idx in unclassified_indices:
                msg = recent_messages[idx]
                msg_id = msg.get('message_id')
                
                if msg_id in emotion_map:
                    emotion_data = emotion_map[msg_id]
                    msg['message_emotion'] = {
                        'emotion': emotion_data.get('emotion', 'neutral'),
                        'justification': emotion_data.get('justification', 'No justification provided')
                    }
                    logger.info(f"Classified message {msg_id}: {emotion_data.get('emotion')}")
                else:
                    logger.warning(f"No emotion returned for message {msg_id}")
                    msg['message_emotion'] = {
                        'emotion': 'ERROR',
                        'justification': 'LLM did not return emotion for this message'
                    }
            
            # Update group sentiment
            state['group_sentiment'] = group_sentiment
            logger.info(f"Group sentiment: {group_sentiment}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text}")
            
            # Set ERROR for all unclassified messages
            for idx in unclassified_indices:
                recent_messages[idx]['message_emotion'] = {
                    'emotion': 'ERROR',
                    'justification': 'JSON parsing failed'
                }
            state['group_sentiment'] = 'ERROR: Failed to parse LLM response'
            
    except Exception as e:
        logger.error(f"Error in emotion analysis: {e}", exc_info=True)
        
        # Set ERROR for all unclassified messages
        for idx in unclassified_indices:
            recent_messages[idx]['message_emotion'] = {
                'emotion': 'ERROR',
                'justification': f'Analysis failed: {str(e)}'
            }
        state['group_sentiment'] = f'ERROR: {str(e)}'
    
    logger.info("Component B - Emotion/Sentiment Analysis completed")
