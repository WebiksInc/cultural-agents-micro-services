"""
Component E.1 - Text Generator Node

Generates natural, human-like response content based on selected action and context.
"""

import json
import logging
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.chat_models import init_chat_model

# Import utilities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils import load_prompt, get_model_settings
from logs.logfire_config import get_logger
from logs import log_node_start, log_prompt, log_node_output, log_state

# Configure logging
logger = get_logger(__name__)


def text_generator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Component E.1: Text Generator Node
    
    Generates response content based on selected action and conversation context.
    Modifies the state in-place by setting generated_response.
    
    Args:
        state: AgentState dict containing agent_prompt, selected_action, recent_messages, etc.
    """
    log_node_start("text_generator", {
        "action_id": state.get('selected_action', {}).get('id', 'none')
    })
    log_state("text_generator_entry", state, "agent")
    
    logger.info("Starting Text Generator (E.1)")
    
    # Get required inputs
    agent_prompt = state.get('agent_prompt', '')
    selected_action = state.get('selected_action')
    recent_messages = state.get('recent_messages', [])
    selected_persona = state.get('selected_persona', {})
    agent_goal = state.get('agent_goal', 'No goal specified')
    group_sentiment = state.get('group_sentiment', 'No sentiment analysis available')
    actions = state.get('actions', {})
    
    # Validate selected_action
    if not selected_action:
        logger.error("No selected_action - cannot generate response")
        state['generated_response'] = None
        return
    
    action_id = selected_action.get('id')
    action_purpose = selected_action.get('purpose', 'No purpose specified')
    
    if not action_id:
        logger.error("selected_action missing 'id' field")
        state['generated_response'] = None
        return
    
    # Get full action details (description)
    action_description = 'No description available'
    all_actions = actions.get('actions', [])
    for action in all_actions:
        if action['id'] == action_id:
            action_description = action.get('description', 'No description available')
            break
    
    logger.info(f"Generating response for action '{action_id}'")
    
    # Format recent messages as JSON
    recent_messages_json = json.dumps(recent_messages, indent=2, default=str)
    
    # Format persona as JSON
    persona_json = json.dumps(selected_persona, indent=2)
    
    # Build the main prompt
    prompt_template = load_prompt("agent_graph/E1/component_E1_prompt.txt")
    main_prompt = prompt_template.format(
        agent_goal=agent_goal,
        action_id=action_id,
        action_description=action_description,
        action_purpose=action_purpose,
        group_sentiment=group_sentiment,
        recent_messages_json=recent_messages_json,
        persona_json=persona_json
    )
    
    # If there's validation feedback, prepend it to the prompt for retry
    validation_feedback = state.get('validation_feedback')
    if validation_feedback:
        logger.info(f"Retry attempt - including validation feedback")
        feedback_note = f"""
                            IMPORTANT - PREVIOUS ATTEMPT FAILED VALIDATION 

                            Your previous response was rejected for the following reason:
                            {validation_feedback}

                            Please generate a NEW response that addresses this issue while still fulfilling the action purpose.
                            Focus on fixing the specific problem mentioned above.

---
"""
        main_prompt = feedback_note + main_prompt
    
    try:
        # Get model settings
        model_settings = get_model_settings('text_generator', 'TEXT_GENERATOR_MODEL')
        model_name = model_settings['model']
        temperature = model_settings['temperature']
        
        # Log prompt to Logfire
        log_prompt("text_generator", main_prompt, model_name, temperature)
        
        logger.info(f"Using model: {model_name} (temperature: {temperature})")
        
        model = init_chat_model(
            model=model_name,
            model_provider="openai",
            temperature=temperature
        )
        
        # Call LLM with system message (agent_prompt) and user message (main_prompt)
        messages = [
            SystemMessage(content=agent_prompt),
            HumanMessage(content=main_prompt)
        ]
        
        response = model.invoke(messages)
        response_text = response.content.strip()
        
        logger.info(f"Generated response ({len(response_text)} chars): {response_text[:100]}...")
        print(("=" * 100))
        
        # Log output to Logfire
        log_node_output("text_generator", {"generated_response": response_text})
        log_state("text_generator", state, "exit")
        
        # Return generated response
        return {
            'generated_response': response_text,
            'current_node': 'text_generator'
        }
        
    except Exception as e:
        logger.error(f"Error in text generator: {e}", exc_info=True)
    
    # Return None if error occurred
    return {
        'generated_response': None,
        'current_node': 'text_generator'
    }
