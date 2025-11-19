"""
Centralized Logfire Configuration

Sets up Pydantic Logfire for the entire langgraph system.
Call setup_logfire() once at application startup.
"""

import os
import logging
from typing import Optional, Any
import logfire
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

_logfire_configured = False


def setup_logfire(service_name: str = "cultural-agents") -> None:
    """
    Configure Logfire for the application.
    
    This should be called once at application startup.
    
    Args:
        service_name: Name of the service for Logfire UI organization
    """
    global _logfire_configured
    
    if _logfire_configured:
        return
    
    # Get Logfire token from environment
    logfire_token = os.getenv("LOGFIRE_TOKEN")
    
    if not logfire_token:
        logging.warning("LOGFIRE_TOKEN not found in environment. Logfire will not be configured.")
        logging.warning("Add LOGFIRE_TOKEN to your .env file to enable Logfire integration.")
        return
    
    try:
        # Configure Logfire - this should automatically connect to Logfire cloud
        # Disable scrubbing to see full prompts and outputs
        logfire.configure(
            token=logfire_token,
            service_name=service_name,
            scrubbing=False,
        )
        
        _logfire_configured = True
        
        # Also log to console
        logging.info(f"✓ Logfire configured successfully for service: {service_name}")
        logging.info(f"✓ Check your Logfire dashboard at: https://logfire.pydantic.dev/")
        
    except Exception as e:
        logging.error(f"Failed to configure Logfire: {e}", exc_info=True)
        logging.warning("Continuing without Logfire integration")


class LogfireLogger:
    """
    Logger wrapper that sends logs to both standard logging and Logfire.
    """
    def __init__(self, name: str):
        self.name = name
        self._logger = logging.getLogger(name)
        
    def info(self, msg: str, **kwargs: Any) -> None:
        """Log info message to both logging and Logfire."""
        # Always log to console
        self._logger.info(msg)
        # Send to Logfire if configured
        if _logfire_configured:
            try:
                logfire.info(msg, **{"logger": self.name, **kwargs})
            except Exception as e:
                self._logger.debug(f"Failed to send to Logfire: {e}")
    
    def error(self, msg: str, **kwargs: Any) -> None:
        """Log error message to both logging and Logfire."""
        self._logger.error(msg)
        if _logfire_configured:
            try:
                logfire.error(msg, **{"logger": self.name, **kwargs})
            except Exception as e:
                self._logger.debug(f"Failed to send to Logfire: {e}")
    
    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log warning message to both logging and Logfire."""
        self._logger.warning(msg)
        if _logfire_configured:
            try:
                logfire.warn(msg, **{"logger": self.name, **kwargs})
            except Exception as e:
                self._logger.debug(f"Failed to send to Logfire: {e}")
    
    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log debug message to both logging and Logfire."""
        self._logger.debug(msg)
        if _logfire_configured:
            try:
                logfire.debug(msg, **{"logger": self.name, **kwargs})
            except Exception as e:
                self._logger.debug(f"Failed to send to Logfire: {e}")
    
    # Maintain compatibility with standard logger interface
    warn = warning


def get_logger(name: str) -> LogfireLogger:
    """
    Get a logger instance that sends to both standard logging and Logfire.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        LogfireLogger instance
    """
    return LogfireLogger(name)


def log_node_start(node_name: str, state_summary: dict = None, agent_name: str = None):
    """
    Log the start of a node execution to Logfire.
    Creates a collapsible span in the UI.
    
    Args:
        node_name: Name of the node being executed
        state_summary: Optional summary of state (e.g., message count, current values)
        agent_name: Optional agent name to display in brackets
    """
    if _logfire_configured:
        try:
            attrs = {"node": node_name}
            if state_summary:
                attrs.update(state_summary)
            if agent_name:
                attrs["agent_name"] = agent_name
            display_name = f"{node_name} ({agent_name})" if agent_name else node_name
            logfire.info(f"▶️ Starting {display_name}", **attrs)
        except Exception:
            pass


def log_prompt(component_name: str, prompt: str, model: str = None, temperature: float = None, agent_name: str = None):
    """
    Log a prompt being sent to an LLM.
    
    Args:
        component_name: Name of the component sending the prompt
        prompt: The full prompt text
        model: Model name (e.g., "gpt-4o-mini")
        temperature: Temperature setting
        agent_name: Optional agent name to display in brackets
    """
    if _logfire_configured:
        try:
            attrs = {
                "component": component_name,
                "prompt": prompt,
                "prompt_length": len(prompt)
            }
            if model:
                attrs["model"] = model
            if temperature is not None:
                attrs["temperature"] = temperature
            if agent_name:
                attrs["agent_name"] = agent_name
            
            display_name = f"{component_name} ({agent_name})" if agent_name else component_name
            logfire.info(f"📝 Prompt for {display_name}", **attrs)
        except Exception:
            pass


def log_state(node_name: str, state: dict, state_type: str = "agent"):
    """
    Log full state to Logfire with expandable fields.
    
    Args:
        node_name: Name of the node logging the state
        state: The full state dictionary
        state_type: "agent" or "supervisor"
    """
    if _logfire_configured:
        try:
            # Create a structured log with expandable fields
            attrs = {
                "node": node_name,
                "state_type": state_type,
                "state": state,  # Logfire will make this expandable in UI
            }
            first_name = state.get('selected_persona', {}).get('first_name', 'Unknown')
            last_name = state.get('selected_persona', {}).get('last_name', 'Unknown')
            
            if first_name != "Unknown" or last_name != "Unknown":
                agent_name = first_name + (" " + last_name if last_name else "")
                attrs["agent_name"] = agent_name
            # Add quick summary fields for easy filtering
            if "recent_messages" in state:
                attrs["message_count"] = len(state.get("recent_messages", []))
            if "current_node" in state:
                attrs["current_node"] = state.get("current_node")
            if "next_node" in state:
                attrs["next_node"] = state.get("next_node")
            if "detected_trigger" in state:
                trigger = state.get("detected_trigger")
                if trigger:
                    attrs["trigger_id"] = trigger.get("id")
            if "selected_action" in state:
                action = state.get("selected_action")
                if action:
                    attrs["action_id"] = action.get("id")
            
            logfire.info(f"📊 State snapshot at {node_name} ({attrs["agent_name"]})", **attrs)
        except Exception as e:
            logging.debug(f"Failed to log state: {e}")


def log_node_output(node_name: str, output_data: dict, agent_name: str = None):
    """
    Log the output of a node.
    
    Args:
        node_name: Name of the node
        output_data: Dictionary of output fields (e.g., generated_response, styled_response)
        agent_name: Optional agent name to display in brackets
    """
    if _logfire_configured:
        try:
            attrs = {"node": node_name, **output_data}
            if agent_name:
                attrs["agent_name"] = agent_name
            display_name = f"{node_name} ({agent_name})" if agent_name else node_name
            logfire.info(f"✅ Output from {display_name}", **attrs)
        except Exception:
            pass


def log_flow_transition(from_node: str, to_node: str, reason: str = None, agent_name: str = None):
    """
    Log a flow transition between nodes.
    
    Args:
        from_node: Current node
        to_node: Next node
        reason: Optional reason for transition
        agent_name: Optional agent name to display in brackets
    """
    if _logfire_configured:
        try:
            attrs = {
                "from_node": from_node,
                "to_node": to_node
            }
            if reason:
                attrs["reason"] = reason
            if agent_name:
                attrs["agent_name"] = agent_name
            
            logfire.info(f"➡️ Flow: {from_node} → {to_node} ({agent_name})", **attrs)
        except Exception:
            pass
