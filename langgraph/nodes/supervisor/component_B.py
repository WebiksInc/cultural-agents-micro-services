import json
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from langchain.chat_models import init_chat_model

# utilities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils import load_prompt, get_model_settings, format_message_for_prompt
from logs.logfire_config import get_logger
from logs import log_node_start, log_prompt, log_node_output

# Configure logging
logger = get_logger(__name__)


def emotion_analysis_node(state: Dict[str, Any]) -> None:
    """
    Component B: Emotion/Sentiment Analysis Node
    
    Analyzes emotions for unclassified messages and generates group sentiment.
    Modifies the state in-place.
    
    Args:
        state: SupervisorState dict containing recent_messages and group_metadata
    """
    log_node_start("component_b", {
        "total_messages": len(state.get('recent_messages', []))
    })
        
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
    
    
    # Log new messages to Logfire with detailed information
    try:
        import logfire
        new_messages_data = []
        for msg in unclassified_messages:
            sender_username = msg.get('sender_username', '').strip()
            sender_first_name = msg.get('sender_first_name', '').strip()
            sender_last_name = msg.get('sender_last_name', '').strip()
            
            if sender_username:
                sender = sender_username
            elif sender_first_name and sender_last_name:
                sender = f"{sender_first_name} {sender_last_name}"
            elif sender_first_name:
                sender = sender_first_name
            else:
                sender = 'Unknown'
            
            new_messages_data.append({
                "message_id": msg.get('message_id', 'unknown'),
                "sender": sender,
                "text": msg.get('text', ''),
                "time": str(msg.get('date', 'unknown'))
            })

        logfire.info(f"New {len(unclassified_messages)} unclassified messages", **{
            "component": "component_b",
            "count": len(unclassified_messages),
            "new_messages": new_messages_data
        })
    except Exception as e:
        logger.debug(f"Failed to log new messages to Logfire: {e}")
    
    # Extract group metadata
    group_name = group_metadata.get('name', 'Unknown Group')
    group_topic = group_metadata.get('topic', 'General discussion')
    member_count = group_metadata.get('members', 'Unknown')
    
    # Format conversation history (all messages for context)
    conversation_lines = []
    for msg in recent_messages:
        conversation_lines.append(format_message_for_prompt(msg, include_timestamp=False, include_emotion=True))
    conversation_history = "\n".join(conversation_lines)
    
    # Format unclassified messages
    unclassified_lines = []
    for msg in unclassified_messages:
        # Get sender name (prefer username, fall back to first_name + last_name, then just first_name)
        sender_username = msg.get('sender_username', '').strip()
        sender_first_name = msg.get('sender_first_name', '').strip()
        sender_last_name = msg.get('sender_last_name', '').strip()
        
        if sender_username:
            sender = sender_username
        elif sender_first_name and sender_last_name:
            sender = f"{sender_first_name} {sender_last_name}"
        elif sender_first_name:
            sender = sender_first_name
        else:
            sender = 'Unknown'
        
        text = msg.get('text', '')
        msg_id = msg.get('message_id', 'unknown')
        unclassified_lines.append(f"[ID: {msg_id}] {sender}: {text}")
    unclassified_text = "\n".join(unclassified_lines)
    
    # Build prompt
    prompt_template = load_prompt("supervisor_graph/component_B/emotion_analysis_prompt.txt")
    prompt = prompt_template.format(
        group_name=group_name,
        group_topic=group_topic,
        member_count=member_count,
        conversation_history=conversation_history,
        unclassified_messages=unclassified_text
    )
    
    try:
        # Get model settings
        model_settings = get_model_settings('component_B', 'COMPONENT_B_MODEL')
        model_name = model_settings['model']
        temperature = model_settings['temperature']
        provider = model_settings['provider']
                
        model = init_chat_model(
            model=model_name,
            model_provider=provider,
            temperature=temperature
        )
        
        # Log prompt to Logfire
        log_prompt("component_b", prompt, model_name, temperature)
        
        # Call LLM
        response = model.invoke([HumanMessage(content=prompt)])
        response_text = response.content
                
        # Parse JSON response with retry logic
        for attempt in range(2):
            try:
                result = json.loads(response_text)
                message_emotions = result.get('message_emotions', [])
                group_sentiment = result.get('group_sentiment', 'ERROR: No sentiment provided')
                
                # Update state with emotions
                emotion_map = {item['message_id']: item for item in message_emotions}
                classified_results = []
                
                for idx in unclassified_indices:
                    msg = recent_messages[idx]
                    msg_id = msg.get('message_id')
                    
                    if msg_id in emotion_map:
                        emotion_data = emotion_map[msg_id]
                        msg['message_emotion'] = {
                            'emotion': emotion_data.get('emotion', 'neutral'),
                            'justification': emotion_data.get('justification', 'No justification provided')
                        }
                        classified_results.append({
                            "message_id": msg_id,
                            "emotion": emotion_data.get('emotion'),
                            "text": msg.get('text', '')
                        })
                    else:
                        logger.warning(f"No emotion returned for message {msg_id}")
                        msg['message_emotion'] = {
                            'emotion': 'ERROR',
                            'justification': 'LLM did not return emotion for this message'
                        }
                        classified_results.append({
                            "message_id": msg_id,
                            "emotion": "ERROR",
                            "text": msg.get('text', '')
                        })
                
                # Update group sentiment
                state['group_sentiment'] = group_sentiment
                
                # Log structured output to Logfire
                log_node_output("component_b", {
                    "messages_analyzed": len(unclassified_messages),
                    "classified_messages": classified_results,
                    "group_sentiment": group_sentiment
                })
                
                if attempt == 1:
                    logger.info("Retry successful")
                break
                        
            except json.JSONDecodeError as e:
                if attempt == 0:
                    logger.warning(f"JSON parsing failed on first attempt: {e}. Retrying...")
                    response = model.invoke([HumanMessage(content=prompt)])
                    response_text = response.content
                else:
                    logger.error(f"JSON parsing failed after retry: {e}")
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
    