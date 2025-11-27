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
from logs import log_node_start, log_prompt, log_state, log_node_output

# Configure logging
logger = get_logger(__name__)


def trigger_analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
    # Get agent name for logging
    selected_persona = state.get('selected_persona', {})
    agent_name = f"{selected_persona.get('first_name', 'Unknown')} {selected_persona.get('last_name', '')}".strip()
    
    # Log to Logfire
    log_node_start("trigger_analysis", {
        "message_count": len(state.get('recent_messages', [])),
        "agent_type": state.get('agent_type', 'unknown')
    }, agent_name=agent_name)
    log_state("trigger_analysis_entry", state, "agent")
    
    recent_messages = state.get('recent_messages', [])
    triggers = state.get('triggers', {})
    agent_type = state.get('agent_type', 'unknown')
    agent_goal = state.get('agent_goal', 'No goal specified')
    
    # Validate inputs
    if not recent_messages:
        logger.warning("No recent messages provided")
        return {
            'detected_trigger': {
                'id': 'neutral',
                'justification': 'No recent messages to analyze'
            },
            'current_node': 'trigger_analysis'
        }
    
    if not triggers:
        logger.warning("No triggers provided")
        return {
            'detected_trigger': {
                'id': 'ERROR',
                'justification': 'No triggers configuration available'
            },
            'current_node': 'trigger_analysis'
        }
    
    # Format recent messages for prompt
    message_lines = []
    for msg in recent_messages:
        message_lines.append(format_message_for_prompt(msg, include_timestamp=True, include_emotion=True, selected_persona=selected_persona))
    recent_messages_text = "\n".join(message_lines)
    
    # Format triggers JSON
    triggers_json = json.dumps(triggers, indent=2)

    # Build prompt
    prompt_template = load_prompt("agent_graph/trigger_analysis/trigger_analysis_prompt.txt")
    prompt = prompt_template.format(
        agent_name=agent_name,
        agent_type=agent_type,
        agent_goal=agent_goal,
        triggers_json=triggers_json,
        recent_messages=recent_messages_text
    )
    
    try:
        # Get model settings
        model_settings = get_model_settings('trigger_analysis', 'TRIGGER_ANALYSIS_MODEL')
        model_name = model_settings['model']
        temperature = model_settings['temperature']
        provider = model_settings['provider']
        
        # Log prompt to Logfire
        log_prompt("trigger_analysis", prompt, model_name, temperature, agent_name=agent_name)
                
        model = init_chat_model(
            model=model_name,
            model_provider=provider,
            temperature=temperature
        )
        
        # Call LLM
        response = model.invoke([HumanMessage(content=prompt)])
        response_text = response.content
                
        # Parse JSON response
        try:
            result = json.loads(response_text)
            trigger_id = result.get('id', 'neutral')
            justification = result.get('justification', 'No justification provided')
            target_message_raw = result.get('target_message')
            
            # Process target_message if present
            target_message = None
            if target_message_raw and isinstance(target_message_raw, dict):
                timestamp_str = target_message_raw.get('timestamp', '')
                text = target_message_raw.get('text', '')
                
                if timestamp_str and text:
                    target_message = {
                        'timestamp': timestamp_str,
                        'text': text
                    }
            
            # Log output to Logfire
            output_data = {
                'detected_trigger': {
                    'id': trigger_id,
                    'justification': justification,
                    'target_message': target_message
                },
                'current_node': 'trigger_analysis'
            }
            log_node_output("trigger_analysis", {
                "trigger_id": trigger_id,
                "justification": justification,
                "target_message": target_message
            }, agent_name=agent_name)
            log_state("trigger_analysis_exit", {**state, **output_data}, "agent")
            
            # Return detected trigger
            return output_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text}")
            
            return {
                'detected_trigger': {
                    'id': 'ERROR',
                    'justification': f'JSON parsing failed: {str(e)}'
                },
                'current_node': 'trigger_analysis'
            }
            
    except Exception as e:
        logger.error(f"Error in trigger analysis: {e}", exc_info=True)
        
        return {
            'detected_trigger': {
                'id': 'ERROR',
                'justification': f'Analysis failed: {str(e)}'
            },
            'current_node': 'trigger_analysis'
        }
