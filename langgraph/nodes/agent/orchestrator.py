"""
Agent Orchestrator Node

Manages the flow and transitions between agent nodes.
Acts as the central routing logic for the agent graph.
"""

import logging
from typing import Dict, Any
from logs.logfire_config import get_logger
from logs import log_flow_transition

# Configure logging
logger = get_logger(__name__)

# Constants
MAX_RETRIES = 3
END = "__end__"


def orchestrator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent Orchestrator Node
    
    Routes between agent nodes based on the current state.
    Returns updates to next_node to indicate where the flow should go.
    
    Flow:
    1. Entry (from supervisor) → trigger_analysis
    2. After trigger_analysis → decision_maker OR END (if no trigger)
    3. After decision_maker → text_generator OR END (if no action)
    4. After text_generator → styler
    5. After styler → validator
    6. After validator → text_generator (retry) OR END (approved/max retries)
    
    Args:
        state: AgentState dict
        
    Returns:
        Dict with current_node and next_node updates
    """
    current_node = state.get('current_node')
        
    # Entry point - first node to run
    if current_node is None or current_node == 'orchestrator':
        log_flow_transition("orchestrator", "trigger_analysis", "entry point")
        return {
            'current_node': 'orchestrator',
            'next_node': 'trigger_analysis'
        }
    
    # After trigger analysis
    if current_node == 'trigger_analysis':
        detected_trigger = state.get('detected_trigger')
        agent_type = state.get('agent_type', 'unknown')
        agent_name = state.get('selected_persona', {}).get('agent_name', 'unknown')
        
        if detected_trigger is None:
            logger.info("→ No trigger detected - routing to END (no action needed)")
            log_flow_transition("trigger_analysis", "END", "no trigger detected")
            return {
                'selected_action': {
                    "status": "no_action_needed",
                    "reason": "no_trigger_detected",
                    "agent_type": agent_type,
                    "agent_name": agent_name
                },
                'current_node': 'orchestrator',
                'next_node': END
            }
        
        # Check for neutral trigger
        trigger_id = detected_trigger.get('id', '')
        if trigger_id == 'neutral' or 'neutral' in trigger_id.lower():
            logger.info("→ Neutral trigger detected - routing to END (no action needed)")
            log_flow_transition("trigger_analysis", "END", "neutral trigger")
            return {
                'selected_action': {
                    "status": "no_action_needed",
                    "reason": "neutral_trigger",
                    "agent_type": agent_type,
                    "agent_name": agent_name
                },
                'current_node': 'orchestrator',
                'next_node': END
            }
        
        logger.info(f"→ Trigger detected: {trigger_id} - routing to decision_maker")
        log_flow_transition("trigger_analysis", "decision_maker", f"trigger: {trigger_id}")
        return {
            'current_node': 'orchestrator',
            'next_node': 'decision_maker'
        }
    
    # After decision maker
    if current_node == 'decision_maker':
        selected_action = state.get('selected_action')
        agent_type = state.get('agent_type', 'unknown')
        agent_name = state.get('selected_persona', {}).get('agent_name', 'unknown')
        
        if selected_action is None:
            logger.info("→ No action selected - routing to END (no action needed)")
            log_flow_transition("decision_maker", "END", "no action selected")
            return {
                'selected_action': {
                    "status": "no_action_needed",
                    "reason": "no_action_selected",
                    "agent_type": agent_type,
                    "agent_name": agent_name
                },
                'current_node': 'orchestrator',
                'next_node': END
            }
        
        action_id = selected_action.get('id', '')
        logger.info(f"→ Action selected: {action_id} - routing to text_generator")
        log_flow_transition("decision_maker", "text_generator", f"action: {action_id}")
        return {
            'current_node': 'orchestrator',
            'next_node': 'text_generator'
        }
    
    # After text generator (E.1)
    if current_node == 'text_generator':
        generated_response = state.get('generated_response')
        agent_type = state.get('agent_type', 'unknown')
        agent_name = state.get('selected_persona', {}).get('agent_name', 'unknown')
        
        if not generated_response:
            logger.error("→ Text generation failed - routing to END with error")
            return {
                'selected_action': {
                    "status": "error",
                    "reason": "text_generation_failed",
                    "error": "No response generated by E.1",
                    "agent_type": agent_type,
                    "agent_name": agent_name
                },
                'current_node': 'orchestrator',
                'next_node': END
            }
        
        logger.info("→ Text generated successfully - routing to styler")
        log_flow_transition("text_generator", "styler", "text generated")
        return {
            'current_node': 'orchestrator',
            'next_node': 'styler'
        }
    
    # After styler (E.2)
    if current_node == 'styler':
        styled_response = state.get('styled_response')
        agent_type = state.get('agent_type', 'unknown')
        agent_name = state.get('selected_persona', {}).get('agent_name', 'unknown')
        
        if not styled_response:
            logger.error("→ Styling failed - routing to END with error")
            return {
                'selected_action': {
                    "status": "error",
                    "reason": "styling_failed",
                    "error": "No styled response generated by E.2",
                    "agent_type": agent_type,
                    "agent_name": agent_name
                },
                'current_node': 'orchestrator',
                'next_node': END
            }
        
        logger.info("→ Response styled successfully - routing to validator")
        log_flow_transition("styler", "validator", "styled response ready")
        return {
            'current_node': 'orchestrator',
            'next_node': 'validator'
        }
    
    # After validator
    if current_node == 'validator':
        validation = state.get('validation', {})
        approved = validation.get('approved', False)
        retry_count = state.get('retry_count', 0)
        agent_type = state.get('agent_type', 'unknown')
        agent_name = state.get('selected_persona', {}).get('agent_name', 'unknown')
        
        if approved:
            logger.info("✓ Validation PASSED - routing to END")
            log_flow_transition("validator", "END", "validation approved")
            # Ensure selected_action has the final styled_response and agent info
            selected_action = state.get('selected_action', {})
            selected_persona = state.get('selected_persona', {})
            
            selected_action['status'] = 'success'
            selected_action['styled_response'] = state.get('styled_response')
            selected_action['agent_type'] = agent_type
            selected_action['agent_name'] = agent_name
            selected_action['phone_number'] = selected_persona.get('phone_number', '')
            
            return {
                'selected_action': selected_action,
                'retry_count': 0,
                'current_node': 'orchestrator',
                'next_node': END
            }
        
        # Validation failed - check retry count
        explanation = validation.get('explanation', 'Unknown validation failure')
        
        if retry_count >= MAX_RETRIES:
            logger.warning(f"✗ Max retries ({MAX_RETRIES}) reached - routing to END with last attempt")
            # Return the last attempt even though it failed validation
            selected_action = state.get('selected_action', {})
            selected_action['status'] = 'max_retries_reached'
            selected_action['styled_response'] = state.get('styled_response')
            selected_action['validation_note'] = f"Failed validation after {MAX_RETRIES} attempts"
            selected_action['agent_type'] = agent_type
            selected_action['agent_name'] = agent_name
            
            return {
                'selected_action': selected_action,
                'retry_count': 0,
                'current_node': 'orchestrator',
                'next_node': END
            }
        
        logger.warning(f"✗ Validation FAILED (attempt {retry_count}/{MAX_RETRIES}): {explanation}")
        logger.info("→ Routing back to text_generator for retry")
        log_flow_transition("validator", "text_generator", f"retry {retry_count+1}/{MAX_RETRIES}")
        return {
            'current_node': 'orchestrator',
            'next_node': 'text_generator'
        }
    
    # Unknown state - error handling
    logger.error(f"→ Unknown current_node: {current_node} - routing to END with error")
    agent_type = state.get('agent_type', 'unknown')
    agent_name = state.get('selected_persona', {}).get('agent_name', 'unknown')
    return {
        'selected_action': {
            "status": "error",
            "reason": "unknown_state",
            "error": f"Orchestrator encountered unknown state: {current_node}",
            "agent_type": agent_type,
            "agent_name": agent_name
        },
        'current_node': 'orchestrator',
        'next_node': END
    }


def route_from_orchestrator(state: Dict[str, Any]) -> str:
    """
    Routing function for LangGraph conditional edges.
    Returns the next_node value set by the orchestrator.
    
    Args:
        state: AgentState dict
        
    Returns:
        str: Next node name or END
    """
    next_node = state.get('next_node', END)
    logger.info(f"Routing from orchestrator to: {next_node}")
    return next_node
