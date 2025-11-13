"""
Decision Maker Node

Selects the most appropriate action based on detected trigger and context.
"""

import json
import logging
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage
from langchain.chat_models import init_chat_model

# Import utilities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils import load_prompt, get_model_settings, format_message_for_prompt

# Configure logging
logger = logging.getLogger(__name__)


def decision_maker_node(state: Dict[str, Any]) -> None:
    """
    Decision Maker Node
    
    Selects the best action from suggested actions based on trigger and context.
    Modifies the state in-place by setting selected_action.
    
    Args:
        state: AgentState dict containing detected_trigger, actions, recent_messages, etc.
    """
    logger.info("Starting Decision Maker")
    
    detected_trigger = state.get('detected_trigger', {})
    actions = state.get('actions', {})
    triggers = state.get('triggers', {})
    recent_messages = state.get('recent_messages', [])
    group_sentiment = state.get('group_sentiment', 'No sentiment analysis available')
    agent_type = state.get('agent_type', 'unknown')
    agent_goal = state.get('agent_goal', 'No goal specified')
    
    # Get trigger details
    trigger_id = detected_trigger.get('id', 'neutral')
    trigger_justification = detected_trigger.get('justification', 'No justification provided')
    
    # Handle neutral trigger - no action needed
    if trigger_id == 'neutral':
        logger.info("Trigger is neutral - no action needed")
        state['selected_action'] = None
        return
    
    # Handle error trigger
    if trigger_id == 'ERROR':
        logger.error("Trigger analysis returned ERROR - cannot make decision")
        state['selected_action'] = None
        return
    
    # Find the detected trigger in triggers list to get suggested actions
    suggested_action_ids = []
    trigger_list = triggers.get('triggers', [])
    for trigger in trigger_list:
        if trigger['id'] == trigger_id:
            suggested_action_ids = trigger.get('suggested_actions', [])
            break
    
    # If no suggested actions, default to no action
    if not suggested_action_ids:
        logger.warning(f"No suggested actions for trigger '{trigger_id}' - no action taken")
        state['selected_action'] = None
        return
    
    logger.info(f"Trigger '{trigger_id}' suggests {len(suggested_action_ids)} actions: {suggested_action_ids}")
    
    # Get full details for suggested actions
    all_actions = actions.get('actions', [])
    suggested_actions = []
    for action_id in suggested_action_ids:
        for action in all_actions:
            if action['id'] == action_id:
                suggested_actions.append(action)
                break
    
    if not suggested_actions:
        logger.error(f"Could not find action details for suggested actions: {suggested_action_ids}")
        state['selected_action'] = None
        return
    
    # Format recent messages for prompt
    message_lines = []
    for msg in recent_messages:
        message_lines.append(format_message_for_prompt(msg, include_timestamp=True, include_emotion=True))
    recent_messages_text = "\n".join(message_lines) if message_lines else "No recent messages"
    
    # Format suggested actions as JSON
    suggested_actions_json = json.dumps(suggested_actions, indent=2)
    
    # Build prompt
    prompt_template = load_prompt("agent_graph/decision_maker/decision_maker_prompt.txt")
    prompt = prompt_template.format(
        agent_type=agent_type,
        agent_goal=agent_goal,
        trigger_id=trigger_id,
        trigger_justification=trigger_justification,
        group_sentiment=group_sentiment,
        recent_messages=recent_messages_text,
        suggested_actions_json=suggested_actions_json
    )
    
    try:
        # Get model settings
        model_settings = get_model_settings('decision_maker', 'DECISION_MAKER_MODEL')
        model_name = model_settings['model']
        temperature = model_settings['temperature']
        
        logger.info(f"Using model: {model_name} (temperature: {temperature})")
        
        model = init_chat_model(
            model=model_name,
            model_provider="openai",
            temperature=temperature
        )
        
        # Call LLM
        response = model.invoke([HumanMessage(content=prompt)])
        response_text = response.content
        
        logger.info(f"Received LLM response: {response_text[:200]}...")
        
        # Parse JSON response
        try:
            result = json.loads(response_text)
            action_id = result.get('id', None)
            purpose = result.get('purpose', 'No purpose provided')
            
            if not action_id:
                logger.error("LLM did not return an action ID")
                return {
                    'selected_action': None,
                    'current_node': 'decision_maker'
                }
            
            # Verify the selected action is in the suggested actions
            if action_id not in suggested_action_ids:
                logger.warning(f"LLM selected action '{action_id}' not in suggested actions. Using it anyway.")
            
            logger.info(f"Selected action: {action_id}")
            logger.info(f"Purpose: {purpose}")
            
            return {
                'selected_action': {
                    'id': action_id,
                    'purpose': purpose
                },
                'current_node': 'decision_maker'
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text}")
            return {
                'selected_action': None,
                'current_node': 'decision_maker'
            }
            
    except Exception as e:
        logger.error(f"Error in decision maker: {e}", exc_info=True)
        return {
            'selected_action': None,
            'current_node': 'decision_maker'
        }
