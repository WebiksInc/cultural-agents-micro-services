"""
Validator Node

Performs final quality check on styled response before sending.
Validates against 4 criteria: goal alignment, action alignment, persona coherence, context sanity.
"""

import json
import logging
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from langchain.chat_models import init_chat_model

# Import utilities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils import load_prompt, get_model_settings, format_message_for_prompt

# Configure logging
logger = logging.getLogger(__name__)

# Maximum number of retries before accepting the response
MAX_RETRIES = 3


def validator_node(state: Dict[str, Any]) -> None:
    """
    Validator Node
    
    Validates the styled response against 4 criteria:
    1. Goal Alignment
    2. Action Alignment
    3. Persona Coherence
    4. Context Sanity Check
    
    Modifies the state in-place by setting validation dict.
    
    Args:
        state: AgentState dict containing styled_response, agent_goal, selected_action, etc.
    """
    logger.info("Starting Validator")
    
    # Get required inputs
    styled_response = state.get('styled_response')
    agent_goal = state.get('agent_goal', '')
    selected_action = state.get('selected_action', {})
    selected_persona = state.get('selected_persona', {})
    recent_messages = state.get('recent_messages', [])
    retry_count = state.get('retry_count', 0)
    
    # Validate styled_response exists
    if not styled_response:
        logger.error("No styled_response to validate")
        state['validation'] = {
            "approved": False,
            "explanation": "No styled response was generated",
            "styled_response": styled_response
        }
        state['validation_feedback'] = "No styled response was generated"
        return
    
    logger.info(f"Validating response (retry_count: {retry_count}/{MAX_RETRIES})")
    
    # Check if we've exceeded max retries - if so, approve by default
    if retry_count >= MAX_RETRIES:
        logger.warning(f"Max retries ({MAX_RETRIES}) reached - approving response by default")
        state['validation'] = {
            "approved": True,
            "styled_response": styled_response
        }
        state['validation_feedback'] = None
        state['retry_count'] = 0  # Reset for next action
        return
    
    # Format selected_action as JSON
    selected_action_json = json.dumps(selected_action, indent=2)
    
    # Format selected_persona as JSON
    selected_persona_json = json.dumps(selected_persona, indent=2)
    
    # Format recent_messages as JSON
    recent_messages_formatted = [
        format_message_for_prompt(msg, include_timestamp=True, include_emotion=True)
        for msg in recent_messages
    ]
    recent_messages_json = json.dumps(recent_messages_formatted, indent=2)
    
    # Build the validation prompt
    prompt_template = load_prompt("agent_graph/validator/validator_prompt.txt")
    validation_prompt = prompt_template.format(
        styled_response=styled_response,
        agent_goal=agent_goal,
        selected_action=selected_action_json,
        selected_persona=selected_persona_json,
        recent_messages=recent_messages_json
    )
    
    try:
        # Get model settings
        model_settings = get_model_settings('validator', 'VALIDATOR_MODEL')
        model_name = model_settings['model']
        temperature = model_settings['temperature']
        
        logger.info(f"Using model: {model_name} (temperature: {temperature})")
        
        model = init_chat_model(
            model=model_name,
            model_provider="openai",
            temperature=temperature
        )
        
        # Call LLM for validation
        messages = [HumanMessage(content=validation_prompt)]
        response = model.invoke(messages)
        response_text = response.content.strip()
        
        logger.info(f"Validator response: {response_text[:200]}...")
        
        # Parse JSON response
        try:
            validation_result = json.loads(response_text)
            approved = validation_result.get('approved', False)
            explanation = validation_result.get('explanation', '')
            
            if approved:
                logger.info("✓ Response APPROVED")
                state['validation'] = {
                    "approved": True,
                    "styled_response": styled_response
                }
                state['validation_feedback'] = None
                state['retry_count'] = 0  # Reset for next action
            else:
                logger.warning(f"✗ Response NOT APPROVED: {explanation}")
                state['validation'] = {
                    "approved": False,
                    "explanation": explanation,
                    "styled_response": styled_response
                }
                state['validation_feedback'] = explanation
                state['retry_count'] = retry_count + 1
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse validator JSON response: {e}")
            logger.error(f"Raw response: {response_text}")
            # Default to not approved if we can't parse
            state['validation'] = {
                "approved": False,
                "explanation": "Validator response could not be parsed",
                "styled_response": styled_response
            }
            state['validation_feedback'] = "Validator response could not be parsed"
            state['retry_count'] = retry_count + 1
        
    except Exception as e:
        logger.error(f"Error in validator: {e}", exc_info=True)
        state['validation'] = {
            "approved": False,
            "explanation": f"Validator error: {str(e)}",
            "styled_response": styled_response
        }
        state['validation_feedback'] = f"Validator error: {str(e)}"
        state['retry_count'] = retry_count + 1
    
    logger.info("Validator completed")
