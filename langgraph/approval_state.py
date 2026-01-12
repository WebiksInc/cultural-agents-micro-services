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
REJECTION_LOG_PATH = Path(__file__).parent / "logs" / "rejection_log.json"


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


def log_rejection(
    agent_name: str,
    proposed_message: str,
    rejection_reason: str,
    replacement_message: Optional[str] = None,
    trigger_id: Optional[str] = None,
    action_id: Optional[str] = None,
    group_id: Optional[str] = None,
    group_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a rejection to the rejection log file.
    
    Args:
        agent_name: Name of the agent whose message was rejected
        proposed_message: The message that was rejected
        rejection_reason: Operator's reason for rejection
        replacement_message: Optional replacement message from operator
        trigger_id: The trigger that led to this message
        action_id: The action type that was taken
        group_id: The group ID this was for
        group_name: The group name this was for
        context: Additional context about the rejection
    """
    # Load existing log
    existing_log = []
    if REJECTION_LOG_PATH.exists():
        try:
            with open(REJECTION_LOG_PATH, 'r', encoding='utf-8') as f:
                existing_log = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_log = []
    
    # Add new entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent_name": agent_name,
        "proposed_message": proposed_message,
        "rejection_reason": rejection_reason,
        "replacement_message": replacement_message,
        "trigger_id": trigger_id,
        "action_id": action_id,
        "group_id": group_id,
        "group_name": group_name,
        "context": context
    }
    existing_log.append(entry)
    
    # Ensure directory exists
    REJECTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Write back
    with open(REJECTION_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(existing_log, f, indent=2)


# Global singleton instance
approval_state = ApprovalState()
