import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.chat_models import init_chat_model

# utilities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils import load_prompt, get_model_settings
from logs.logfire_config import get_logger
from logs import log_node_start, log_prompt, log_node_output, log_state

# Configure logging
logger = get_logger(__name__)


def styler_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Component E.2: Styler Node
    
    Stylizes the generated response to match the agent's persona.
    Modifies the state in-place by setting styled_response.
    
    Args:
        state: AgentState dict containing generated_response, selected_persona, agent_prompt, etc.
    """
    # Get agent name for logging
    selected_persona = state.get('selected_persona', {})
    agent_name = f"{selected_persona.get('first_name', 'Unknown')} {selected_persona.get('last_name', '')}".strip()
    
    log_node_start("styler", agent_name=agent_name)
    log_state("styler", state, "entry")
    # logger.info("Starting Styler (E.2)")
    
    # Get required inputs
    generated_response = state.get('generated_response')
    agent_prompt = state.get('agent_prompt', '')
    
    # Validate generated_response
    if not generated_response:
        logger.error("No generated_response - cannot apply styling")
        return {
            'styled_response': None,
            'current_node': 'styler'
        }
    
    # logger.info(f"Styling response ({len(generated_response)} chars)")
    
    # Format selected_persona as JSON
    selected_persona_json = json.dumps(selected_persona, indent=2)
    
    # Build the main prompt
    prompt_template = load_prompt("agent_graph/E2/component_E2_prompt.txt")
    main_prompt = prompt_template.format(
        generated_response=generated_response,
        selected_persona=selected_persona_json
    )
    
    try:
        # Get model settings
        model_settings = get_model_settings('styler', 'STYLER_MODEL')
        model_name = model_settings['model']
        temperature = model_settings['temperature']
        provider = model_settings['provider']
        
        # Log prompt to Logfire
        log_prompt("styler", main_prompt, model_name, temperature, agent_name=agent_name)
        
        # logger.info(f"Using model: {model_name} (temperature: {temperature})")
        
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
        
        # logger.info(f"Styled response ({len(response_text)} chars): {response_text[:100]}...\n")
        print(("-" * 80))
        
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
