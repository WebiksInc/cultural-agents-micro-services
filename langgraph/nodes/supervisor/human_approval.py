"""
Human Approval Node - Interrupt point for operator approval

This node pauses the graph execution after the scheduler has prepared
the execution queue. It presents all pending messages to the operator
for approval and waits for their decision.

Flow:
    scheduler → human_approval (interrupt HERE) → executor

The operator can:
1. Approve a message (send as-is or with edits)
2. Reject a message (log reason, optionally send replacement)

Configuration:
    Set hitl.enabled = false in supervisor_config.json to bypass approval
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Literal
from langgraph.types import interrupt, Command
from logs.logfire_config import get_logger
from logs import log_node_start

logger = get_logger(__name__)

# Load HITL config
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "supervisor_config.json"


def is_hitl_enabled() -> bool:
    """Check if HITL is enabled in supervisor_config.json."""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get("hitl", {}).get("enabled", True)
    except Exception:
        return True  # Default to enabled if config can't be read


def build_approval_request(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the approval request payload from the current state.
    This payload will be shown to the operator in the Streamlit UI.
    
    Args:
        state: SupervisorState containing execution_queue, recent_messages, etc.
        
    Returns:
        JSON-serializable dict with all context for operator decision
    """
    execution_queue = state.get('execution_queue', [])
    recent_messages = state.get('recent_messages', [])
    group_metadata = state.get('group_metadata', {})
    
    # Build pending messages list for approval
    pending_messages = []
    for action in execution_queue:
        if action.get('status') == 'pending':
            pending_item = {
                "agent_name": action.get('agent_name', 'Unknown'),
                "agent_type": action.get('agent_type', 'Unknown'),
                "proposed_message": action.get('action_content', ''),
                "action_id": action.get('action_id', 'unknown'),
                "action_purpose": action.get('action_purpose', ''),
                "trigger_id": action.get('trigger_id', ''),
                "trigger_justification": action.get('trigger_justification', ''),
                "phone_number": action.get('phone_number', ''),
            }
            
            # Add target message info if available
            target_msg = action.get('target_message')
            if target_msg and isinstance(target_msg, dict):
                pending_item["target_message"] = {
                    "sender_name": target_msg.get('sender_first_name', '') or target_msg.get('sender_username', '') or target_msg.get('sender_name', 'Unknown'),
                    "sender_first_name": target_msg.get('sender_first_name', ''),
                    "sender_username": target_msg.get('sender_username', ''),
                    "text": target_msg.get('text', ''),
                    "timestamp": target_msg.get('timestamp', ''),
                    "message_id": target_msg.get('message_id', '')
                }
            else:
                pending_item["target_message"] = None
                
            pending_messages.append(pending_item)
    
    # Build recent messages context (all messages from current batch)
    # Convert to simple serializable format
    context_messages = []
    for msg in recent_messages:
        context_messages.append({
            "sender_name": msg.get('sender_first_name', '') or msg.get('sender_username', '') or 'Unknown',
            "sender_first_name": msg.get('sender_first_name', ''),
            "sender_username": msg.get('sender_username', ''),
            "text": msg.get('text', ''),
            "timestamp": msg.get('timestamp', ''),
            "message_emotion": msg.get('message_emotion', ''),
        })
    
    return {
        "pending_messages": pending_messages,
        "group_info": {
            "name": group_metadata.get('name', 'Unknown Group'),
            "id": group_metadata.get('id', ''),
            "members": group_metadata.get('members', 0),
            "topic": group_metadata.get('topic', '')
        },
        "context_messages": context_messages,
        "total_pending": len(pending_messages)
    }


def process_approval_response(
    state: Dict[str, Any], 
    response: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process the operator's approval response and update the execution queue.
    
    Args:
        state: Current SupervisorState
        response: Operator's decisions
                  Format: {"decisions": [
                      {"agent_name": str, "decision": "approved"|"rejected", 
                       "edited_content": str|None, "rejection_reason": str|None,
                       "replacement_message": str|None}, ...
                  ]}
    
    Returns:
        Updated execution_queue with only approved actions
    """
    from approval_state import log_rejection
    
    execution_queue = state.get('execution_queue', [])
    group_metadata = state.get('group_metadata', {})
    group_name = group_metadata.get('name', 'Unknown Group')
    
    decisions = response.get('decisions', [])
    
    # Build lookup for decisions by agent_name
    decision_lookup = {d.get('agent_name'): d for d in decisions}
    
    approved_actions = []
    
    for action in execution_queue:
        if action.get('status') != 'pending':
            continue
            
        agent_name = action.get('agent_name', 'Unknown')
        decision = decision_lookup.get(agent_name, {})
        decision_type = decision.get('decision', 'rejected')  # Default to rejected if no decision
        
        if decision_type == 'approved':
            # Check if operator edited the content
            edited_content = decision.get('edited_content')
            if edited_content:
                action['action_content'] = edited_content
                logger.info(f"Operator edited message for {agent_name}")
            
            approved_actions.append(action)
            logger.info(f"Approved action from {agent_name}: {action.get('action_id')}")
            
        elif decision_type == 'rejected':
            rejection_reason = decision.get('rejection_reason', 'No reason provided')
            replacement_message = decision.get('replacement_message')
            
            # Log the rejection
            log_rejection(
                agent_name=agent_name,
                group_name=group_name,
                proposed_message=action.get('action_content', ''),
                trigger_id=action.get('trigger_id', 'unknown'),
                rejection_reason=rejection_reason,
                replacement_message=replacement_message,
                context={
                    "action_id": action.get('action_id'),
                    "action_purpose": action.get('action_purpose'),
                    "trigger_justification": action.get('trigger_justification')
                }
            )
            logger.info(f"Rejected action from {agent_name}: {rejection_reason}")
            
            # If operator provided a replacement message, create a new action
            if replacement_message:
                replacement_action = action.copy()
                replacement_action['action_content'] = replacement_message
                replacement_action['action_id'] = 'operator_replacement'
                replacement_action['action_purpose'] = f"Operator replacement for: {action.get('action_purpose', '')}"
                approved_actions.append(replacement_action)
                logger.info(f"Using operator replacement message for {agent_name}")
    
    return approved_actions


def human_approval_node(state: Dict[str, Any]) -> Command[Literal["executor"]]:
    """
    Human Approval Node
    
    Pauses the graph for operator approval of pending messages.
    Uses LangGraph's interrupt() function to pause and wait for external input.
    
    If hitl.enabled = false in config, auto-approves all actions.
    
    Args:
        state: SupervisorState with execution_queue populated by scheduler
        
    Returns:
        Command to proceed to executor with approved actions
    """
    log_node_start("human_approval", {
        "execution_queue_count": len(state.get('execution_queue', []))
    }, supervisor_state=state)
    
    execution_queue = state.get('execution_queue', [])
    
    # If no pending actions, skip approval and go directly to executor
    pending_actions = [a for a in execution_queue if a.get('status') == 'pending']
    if not pending_actions:
        logger.info("Human Approval: No pending actions, skipping approval")
        return Command(
            goto="executor",
            update={}
        )
    
    # Check if HITL is enabled in config
    if not is_hitl_enabled():
        logger.info(f"Human Approval: HITL disabled, auto-approving {len(pending_actions)} actions")
        # Keep status as 'pending' so executor can pick them up
        # (get_ready_actions looks for status == 'pending')
        return Command(
            goto="executor",
            update={"execution_queue": pending_actions}
        )
    
    logger.info(f"Human Approval: {len(pending_actions)} actions awaiting approval")
    
    # Build the approval request payload (JSON-serializable)
    approval_request = build_approval_request(state)
    
    # INTERRUPT - Graph pauses here and waits for operator response
    # The approval_request is surfaced via result["__interrupt__"]
    operator_response = interrupt(approval_request)
    
    # When we resume, operator_response contains the decisions
    # Process the response and filter approved actions
    approved_actions = process_approval_response(state, operator_response)
    
    logger.info(f"Human Approval: {len(approved_actions)} actions approved for execution")
    
    # Update execution queue with only approved actions
    return Command(
        goto="executor",
        update={"execution_queue": approved_actions}
    )
