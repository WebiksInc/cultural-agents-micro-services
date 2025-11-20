import json
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from langchain.chat_models import init_chat_model

# Import utilities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils import load_prompt, get_model_settings, format_message_for_prompt
from logs.logfire_config import get_logger
from logs import log_node_start, log_prompt, log_node_output, log_state

logger = get_logger(__name__)

# Maximum number of retries before accepting the response
MAX_RETRIES = 3

def validator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    # Get agent name for logging
    selected_persona = state.get('selected_persona', {})
    agent_name = f"{selected_persona.get('first_name', 'Unknown')} {selected_persona.get('last_name', '')}".strip()
    
    log_node_start("validator", agent_name=agent_name)
    log_state("validator_entry", state, "agent")
    
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
        return {
            'validation': {
                "approved": False,
                "explanation": "No styled response was generated",
                "styled_response": styled_response
            },
            'validation_feedback': "No styled response was generated",
            'current_node': 'validator'
        }
    
    logger.info(f"Validating response (retry_count: {retry_count}/{MAX_RETRIES}) - ({agent_name})")
    
    # Check if we've exceeded max retries - if so, approve by default
    if retry_count >= MAX_RETRIES:
        logger.warning(f"Max retries ({MAX_RETRIES}) reached - approving response by default - ({agent_name})")
        return {
            'validation': {
                "approved": True,
                "styled_response": styled_response
            },
            'validation_feedback': None,
            'retry_count': 0,
            'current_node': 'validator'
        }
    
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
    
    # Building the validation prompt
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
        provider = model_settings.get('provider', 'openai')
       
        log_prompt("validator", validation_prompt, model_name, temperature, agent_name=agent_name)
                
        model = init_chat_model(
            model=model_name,
            model_provider=provider,
            temperature=temperature
        )
        
        # Call LLM for validation
        messages = [HumanMessage(content=validation_prompt)]
        response = model.invoke(messages)
        response_text = response.content.strip()
        
        # Parse JSON response
        try:
            validation_result = json.loads(response_text)
            approved = validation_result.get('approved', False)
            explanation = validation_result.get('explanation', '')
            
            if approved:
                logger.info(f"Response APPROVED - ({agent_name})")
                output = {
                    'validation': {
                        "approved": True,
                        "styled_response": styled_response
                    },
                    'validation_feedback': None,
                    'retry_count': 0,
                    'current_node': 'validator'
                }
                log_node_output("validator", output['validation'], agent_name=agent_name)
                log_state("validator", state, "exit")
                return output
            else:
                logger.warning(f"Response NOT APPROVED - ({agent_name})", explanation=explanation)
                output = {
                    'validation': {
                        "approved": False,
                        "explanation": explanation,
                        "styled_response": styled_response
                    },
                    'validation_feedback': explanation,
                    'retry_count': retry_count + 1,
                    'current_node': 'validator'
                }
                log_node_output("validator", output['validation'], agent_name=agent_name)
                log_state("validator", state, "exit")
                return output
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse validator JSON response: {e}")
            logger.error(f"Raw response: {response_text}")
            # Default to not approved if we can't parse
            return {
                'validation': {
                    "approved": False,
                    "explanation": "Validator response could not be parsed",
                    "styled_response": styled_response
                },
                'validation_feedback': "Validator response could not be parsed",
                'retry_count': retry_count + 1,
                'current_node': 'validator'
            }
        
    except Exception as e:
        logger.error(f"Error in validator: {e}", exc_info=True)
        return {
            'validation': {
                "approved": False,
                "explanation": f"Validator error: {str(e)}",
                "styled_response": styled_response
            },
            'validation_feedback': f"Validator error: {str(e)}",
            'retry_count': retry_count + 1,
            'current_node': 'validator'
        }
