"""
Trigger Analysis Node

Analyzes recent messages to detect which trigger condition applies to the agent.
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


def trigger_analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Trigger Analysis Node
    
    Analyzes recent messages to detect which trigger condition applies.
    Returns detected_trigger and current_node updates.
    
    Args:
        state: AgentState dict
        
    Returns:
        Dict with detected_trigger and current_node updates
    """
    logger.info("Starting Trigger Analysis")
    
    recent_messages = state.get('recent_messages', [])
    triggers = state.get('triggers', {})
    selected_persona = state.get('selected_persona', {})
    agent_type = state.get('agent_type', 'unknown')
    agent_goal = state.get('agent_goal', 'No goal specified')
    
    # DEBUG: Print recent messages
    logger.info("=" * 80)
    logger.info("RECENT MESSAGES BEING ANALYZED:")
    for i, msg in enumerate(recent_messages, 1):
        logger.info(f"  [{i}] ID:{msg.get('message_id')} From:{msg.get('sender_first_name')} Text:{msg.get('text')[:100]}")
    logger.info("=" * 80)
    
    # Extract agent name from persona
    agent_name = selected_persona.get('first_name', 'Agent')
    
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
    
    logger.info(f"Analyzing {len(recent_messages)} messages for agent '{agent_name}' (type: {agent_type})")
    
    # Format recent messages for prompt
    message_lines = []
    for msg in recent_messages:
        message_lines.append(format_message_for_prompt(msg, include_timestamp=True, include_emotion=True))
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
    
    # DEBUG: Print the complete prompt
    logger.info("=" * 80)
    logger.info("TRIGGER ANALYSIS PROMPT:")
    logger.info(prompt)
    logger.info("=" * 80)
    
    try:
        # Get model settings
        model_settings = get_model_settings('trigger_analysis', 'TRIGGER_ANALYSIS_MODEL')
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
            trigger_id = result.get('id', 'neutral')
            justification = result.get('justification', 'No justification provided')
            
            logger.info(f"Detected trigger: {trigger_id}")
            logger.info(f"Justification: {justification}")
            
            # Return detected trigger
            return {
                'detected_trigger': {
                    'id': trigger_id,
                    'justification': justification
                },
                'current_node': 'trigger_analysis'
            }
            
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
