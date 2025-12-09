import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.chat_models import init_chat_model

# utilities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils import load_prompt, get_model_settings, format_message_for_prompt
from logs.logfire_config import get_logger
from logs import log_node_start, log_prompt, log_node_output, log_state

# Configure logging
logger = get_logger(__name__)


def styler_node(state: Dict[str, Any]) -> Dict[str, Any]:
    # Get agent name for logging
    selected_persona = state.get('selected_persona', {})
    agent_name = f"{selected_persona.get('first_name', 'Unknown')} {selected_persona.get('last_name', '')}".strip()
    
    log_node_start("styler", agent_name=agent_name)
    log_state("styler", state, "entry")
    
    # Get required inputs
    generated_response = state.get('generated_response')
    agent_prompt = state.get('agent_prompt', '')
    recent_messages = state.get('recent_messages', [])
    
    # Validate generated_response
    if not generated_response:
        logger.error("No generated_response - cannot apply styling")
        return {
            'styled_response': None,
            'current_node': 'styler'
        }
    
    # Format selected_persona as JSON (exclude phone_number)
    persona_for_prompt = {k: v for k, v in selected_persona.items() if k != 'phone_number'}
    selected_persona_json = json.dumps(persona_for_prompt, indent=2, ensure_ascii=False)
    
    recent_messages_formatted = [
        format_message_for_prompt(
            msg, 
            include_timestamp=True, 
            include_emotion=True, 
            selected_persona=selected_persona,
            recent_messages=recent_messages
        )
        for msg in recent_messages
    ]
    recent_messages_json = json.dumps(recent_messages_formatted, indent=2, ensure_ascii=False, default=str)
    # Build the main prompt
    prompt_template = load_prompt("agent_graph/E2/component_E2_prompt.txt")
    main_prompt = prompt_template.format(
        generated_response=generated_response,
        selected_persona=selected_persona_json,
        recent_messages=recent_messages_json,
        agent_name=agent_name
    
    )
    
    try:
        # Get model settings
        model_settings = get_model_settings('styler', 'STYLER_MODEL')
        model_name = model_settings['model']
        temperature = model_settings['temperature']
        provider = model_settings['provider']
        
        # Log prompt to Logfire
        log_prompt("styler", main_prompt, model_name, temperature, agent_name=agent_name)
                
        model = init_chat_model(
            model=model_name,
            model_provider=provider,
            temperature=temperature
        )
        
        # Call LLM with system message (agent_prompt) and user message (styling task)
        messages = [
            SystemMessage(content=agent_prompt),
            HumanMessage(content=main_prompt)
        ]
        
        response = model.invoke(messages)
        response_text = response.content.strip()
        
        # Log output to Logfire
        log_node_output("styler", {"styled_response": response_text}, agent_name=agent_name)
        log_state("styler", state, "exit")
        
        # Return styled response
        return {
            'styled_response': response_text,
            'current_node': 'styler'
        }
        
    except Exception as e:
        logger.error(f"Error in styler: {e}", exc_info=True)
    
    # Return None if error occurred
    return {
        'styled_response': None,
        'current_node': 'styler'
    }
