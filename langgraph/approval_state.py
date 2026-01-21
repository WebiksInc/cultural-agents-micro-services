"""
Approval State - File-based shared state for Human-in-the-Loop approval

This module provides file-based persistence for communication between:
- The LangGraph polling loop (writes pending approvals, reads responses)
- The Streamlit UI (reads pending approvals, writes responses)

Since Streamlit runs in a separate process, we use JSON files for IPC.

Usage:
    from approval_state import approval_state
    
    # In polling loop:
    approval_state.set_pending(config, interrupt_data)
    while not approval_state.has_response():
        time.sleep(2)
    response = approval_state.get_response()
    
    # In Streamlit:
    pending = approval_state.get_pending()
    approval_state.set_response(operator_decision)
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Paths for file-based IPC
STATE_DIR = Path(__file__).parent / "data" / "hitl_state"
PENDING_FILE = STATE_DIR / "pending.json"
RESPONSE_FILE = STATE_DIR / "response.json"
OPERATOR_DECISIONS_DIR = Path(__file__).parent / "logs" / "operator_decisions"


class ApprovalState:
    """File-based state for managing pending approvals and responses."""
    
    def __init__(self):
        # Ensure state directory exists
        STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    def _read_json(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Read JSON file safely."""
        if not filepath.exists():
            return None
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    return None
                return json.loads(content)
        except (json.JSONDecodeError, IOError):
            return None
    
    def _write_json(self, filepath: Path, data: Optional[Dict[str, Any]]) -> None:
        """Write JSON file safely."""
        if data is None:
            # Delete file if data is None
            if filepath.exists():
                filepath.unlink()
            return
        try:
            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        except IOError as e:
            print(f"Error writing to {filepath}: {e}")
    
    def set_pending(self, config: Dict[str, Any], interrupt_data: Dict[str, Any]) -> None:
        """
        Set a pending approval request.
        
        Args:
            config: The graph config containing thread_id
            interrupt_data: The data from the interrupt (pending messages info)
        """
        pending = {
            "config": config,
            "data": interrupt_data,
            "timestamp": datetime.now().isoformat()
        }
        self._write_json(PENDING_FILE, pending)
        # Clear any stale response
        self._write_json(RESPONSE_FILE, None)
    
    def get_pending(self) -> Optional[Dict[str, Any]]:
        """Get the current pending approval request, if any."""
        return self._read_json(PENDING_FILE)
    
    def has_pending(self) -> bool:
        """Check if there's a pending approval."""
        return PENDING_FILE.exists() and self._read_json(PENDING_FILE) is not None
    
    def set_response(self, response: Dict[str, Any]) -> None:
        """
        Set the operator's response to the pending approval.
        
        Args:
            response: The operator's decision (approved/rejected with details)
        """
        response_data = {
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        self._write_json(RESPONSE_FILE, response_data)
    
    def get_response(self) -> Optional[Dict[str, Any]]:
        """Get the operator's response (does not consume it)."""
        response_data = self._read_json(RESPONSE_FILE)
        if response_data:
            return response_data.get("response")
        return None
    
    def has_response(self) -> bool:
        """Check if the operator has submitted a response."""
        return RESPONSE_FILE.exists() and self._read_json(RESPONSE_FILE) is not None
    
    def clear(self) -> None:
        """Clear both pending and response state after processing."""
        self._write_json(PENDING_FILE, None)
        self._write_json(RESPONSE_FILE, None)


def log_decision(
    decision_type: str,
    operator_name: str,
    agent_name: str,
    proposed_message: str,
    group_id: str,
    group_name: Optional[str] = None,
    rejection_reason: Optional[str] = None,
    replacement_message: Optional[str] = None,
    trigger_id: Optional[str] = None,
    action_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an operator decision (approval or rejection) to the group's decision log.
    
    Args:
        decision_type: 'approved' or 'rejected'
        operator_name: Name of the operator who made the decision
        agent_name: Name of the agent whose message was reviewed
        proposed_message: The message that was reviewed
        group_id: The Telegram group ID (used for folder structure)
        group_name: The group name for display
        rejection_reason: Operator's reason for rejection (if rejected)
        replacement_message: Optional replacement message from operator
        trigger_id: The trigger that led to this message
        action_id: The action type that was taken
        context: Additional context about the decision
    """
    # Build path: logs/operator_decisions/{group_id}/decisions.json
    group_dir = OPERATOR_DECISIONS_DIR / str(group_id)
    decisions_file = group_dir / "decisions.json"
    
    # Load existing log with approved/rejected structure
    existing_log = {"approved": [], "rejected": []}
    if decisions_file.exists():
        try:
            with open(decisions_file, 'r', encoding='utf-8') as f:
                existing_log = json.load(f)
                # Ensure both keys exist
                if "approved" not in existing_log:
                    existing_log["approved"] = []
                if "rejected" not in existing_log:
                    existing_log["rejected"] = []
        except (json.JSONDecodeError, IOError):
            existing_log = {"approved": [], "rejected": []}
    
    # Build entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "operator_name": operator_name,
        "agent_name": agent_name,
        "message": proposed_message,
        "group_name": group_name,
        "trigger_id": trigger_id,
        "action_id": action_id
    }
    
    # Add rejection-specific fields
    if decision_type == "rejected":
        entry["rejection_reason"] = rejection_reason
        entry["replacement_message"] = replacement_message
        entry["context"] = context
    
    # Append to appropriate list
    if decision_type == "approved":
        existing_log["approved"].append(entry)
    else:
        existing_log["rejected"].append(entry)
    
    # Ensure directory exists
    group_dir.mkdir(parents=True, exist_ok=True)
    
    # Write back
    with open(decisions_file, 'w', encoding='utf-8') as f:
        json.dump(existing_log, f, indent=2)


# Global singleton instance
approval_state = ApprovalState()
