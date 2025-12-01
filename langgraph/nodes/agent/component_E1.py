import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.chat_models import init_chat_model
import logfire

# utilities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils import load_prompt, get_model_settings, format_message_for_prompt
from logs.logfire_config import get_logger
from logs import log_node_start, log_prompt, log_node_output, log_state

# Configure logging
logger = get_logger(__name__)


def text_generator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    # Get agent name for logging
    selected_persona = state.get('selected_persona', {})
    agent_name = f"{selected_persona.get('first_name', 'Unknown')} {selected_persona.get('last_name', '')}".strip()
    
    log_node_start("text_generator", {
        "action_id": state.get('selected_action', {}).get('id', 'none')
    }, agent_name=agent_name)
    log_state("text_generator_entry", state, "agent")
    
    # Get required inputs
    agent_prompt = state.get('agent_prompt', '')
    selected_action = state.get('selected_action')
    recent_messages = state.get('recent_messages', [])
    selected_persona = state.get('selected_persona', {})
    agent_goal = state.get('agent_goal', 'No goal specified')
    group_sentiment = state.get('group_sentiment', 'No sentiment analysis available')
    actions = state.get('actions', {})
    group_metadata = state.get('group_metadata', {})
    agent_name = f"{selected_persona.get('first_name', 'Unknown')} {selected_persona.get('last_name', '')}".strip()
    # Validate selected_action
    if not selected_action:
        logger.error("No selected_action - cannot generate response")
        return {
            'generated_response': None,
            'current_node': 'text_generator'
        }
    
    action_id = selected_action.get('id')
    action_purpose = selected_action.get('purpose', 'No purpose specified')
    
    if not action_id:
        logger.error("selected_action missing 'id' field")
        return {
            'generated_response': None,
            'current_node': 'text_generator'
        }
    
    # Get full action details (description)
    action_description = 'No description available'
    all_actions = actions.get('actions', [])
    for action in all_actions:
        if action['id'] == action_id:
            action_description = action.get('description', 'No description available')
            break
        
    # Format recent messages with (YOU) marker for agent's own messages
    recent_messages_formatted = [
        format_message_for_prompt(msg, include_timestamp=True, include_emotion=True, selected_persona=selected_persona)
        for msg in recent_messages
    ]
    recent_messages_json = json.dumps(recent_messages_formatted, indent=2, ensure_ascii=False, default=str)
    
    # Format persona as JSON (exclude phone_number)
    persona_for_prompt = {k: v for k, v in selected_persona.items() if k != 'phone_number'}
    persona_json = json.dumps(persona_for_prompt, indent=2, ensure_ascii=False)
    # Build the main prompt
    prompt_template = load_prompt("agent_graph/E1/component_E1_prompt.txt")
    main_prompt = prompt_template.format(
        agent_name=agent_name,
        agent_goal=agent_goal,
        action_id=action_id,
        action_description=action_description,
        action_purpose=action_purpose,
        name=group_metadata.get('name', 'Unknown'),
        topic=group_metadata.get('topic', 'No topic provided'),
        group_sentiment=group_sentiment,
        recent_messages_json=recent_messages_json,
        persona_json=persona_json
    )
    
    # If there's validation feedback, prepend it to the prompt for retry
    validation_feedback = state.get('validation_feedback')
    if validation_feedback:
        logger.info(f"Retry attempt - including validation feedback {agent_name}")
        previous_response = state.get('generated_response', 'No previous response available')
        feedback_note = f"""
                            IMPORTANT - PREVIOUS ATTEMPT FAILED VALIDATION 

                            Your previous response was:
                            "{previous_response}"

                            It was rejected for the following reason:
                            {validation_feedback}

                            Generate a NEW response that addresses this issue while still fulfilling the action purpose.
                            Focus on fixing the specific problem mentioned above."""
                                                                  
        main_prompt = feedback_note + main_prompt
    
    try:
        # Get model settings
        model_settings = get_model_settings('text_generator', 'TEXT_GENERATOR_MODEL')
        model_name = model_settings['model']
        temperature = model_settings['temperature']
        provider = model_settings['provider']
        
        # Log prompt to Logfire (including system prompt)
        try:      
            display_name = f"text_generator ({agent_name})"
            logfire.info(f"📝 Prompt for {display_name}", **{
                "component": "text_generator",
                "agent_name": agent_name,
                "system_prompt": agent_prompt,
                "user_prompt": main_prompt,
                "prompt_length": len(main_prompt),
                "system_prompt_length": len(agent_prompt),
                "model": model_name,
                "temperature": temperature
            })
        except Exception as e:
            logger.debug(f"Failed to log prompt to Logfire: {e}")
                
        model = init_chat_model(
            model=model_name,
            model_provider=provider,
            temperature=temperature
        )
        
        # Call LLM with system message (agent_prompt) and user message (main_prompt)
        messages = [
            SystemMessage(content=agent_prompt),
            HumanMessage(content=main_prompt)
        ]
        
        response = model.invoke(messages)
        response_text = response.content.strip()
        
        # Log output to Logfire
        log_node_output("text_generator", {"generated_response": response_text}, agent_name=agent_name)
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
