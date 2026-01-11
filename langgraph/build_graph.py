import json
import logging
from pathlib import Path
from typing import Dict, Any, Literal

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

# Import state definitions
from states.supervisor_state import SupervisorState
from states.agent_state import AgentState

# Import supervisor nodes
from nodes.supervisor.component_B import emotion_analysis_node
from nodes.supervisor.component_C import personality_analysis_node
from nodes.supervisor.scheduler import scheduler_node
from nodes.supervisor.executor import executor_node

# Import agent nodes
from nodes.agent.orchestrator import orchestrator_node, route_from_orchestrator
from nodes.agent.trigger_analysis import trigger_analysis_node
from nodes.agent.decision_maker import decision_maker_node
from nodes.agent.component_E1 import text_generator_node
from nodes.agent.component_E2 import styler_node
from nodes.agent.validator import validator_node

# Import utilities
from utils import *
from logs.logfire_config import get_logger

logger = get_logger(__name__)

# Configuration paths
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
SUPERVISOR_CONFIG_PATH = CONFIG_DIR / "supervisor_config.json"


def load_agent_config(agent_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load all configuration for a single agent.
    
    Args:
        agent_config: Agent configuration from supervisor_config.json
        
    Returns:
        Dictionary with persona, triggers, actions, prompt, and goal
    """
    agent_type = agent_config["type"]
    
    # Load persona
    persona_path = BASE_DIR / agent_config["persona_file"]
    persona = load_json_file(persona_path)
    
    # Load triggers
    triggers_path = BASE_DIR / "triggers" / agent_type / f"{agent_type}_triggers.json"
    triggers = load_json_file(triggers_path)
    
    # For off_radar type: dynamically add support_your_comrades trigger if other agents exist
    if agent_type == "off_radar":
        supervisor_config = load_json_file(SUPERVISOR_CONFIG_PATH)
        # Build list of other agents with their details
        other_agents = [
            {
                "agent_name": agent["name"],
                "agent_type": agent["type"],
                "agent_goal": agent["agent_goal"]
            }
            for agent in supervisor_config["agents"]
            if agent["name"] != agent_config["name"]
        ]
        
        # Only add support_your_comrades trigger if there are other agents
        if other_agents:
            support_trigger_path = BASE_DIR / "triggers" / "off_radar" / "support_your_comrades.json"
            support_trigger = load_json_file(support_trigger_path)
            support_trigger["agents_in_group"] = other_agents
            triggers["triggers"].append(support_trigger)
            logger.info(f"Added support_your_comrades trigger with agents: {[a['agent_name'] for a in other_agents]}")
    
    # Load actions
    actions_path = BASE_DIR / "actions" / agent_type / f"{agent_type}_actions.json"
    actions = load_json_file(actions_path)
    
    # Load agent prompt
    # prompt_path = BASE_DIR / "prompts" / "agent_types" / f"{agent_type}_prompt.txt"
    agent_prompt = load_prompt(f"agent_types/{agent_type}_prompt.txt")
    
    return {
        "persona": persona,
        "triggers": triggers,
        "actions": actions,
        "agent_prompt": agent_prompt,
        "agent_goal": agent_config["agent_goal"],
        "agent_type": agent_type,
        "name": agent_config["name"]
    }


def build_agent_graph(agent_config: Dict[str, Any]) -> StateGraph:
    """
    Build a single agent subgraph.
    
    Flow:
    START → orchestrator → trigger_analysis → orchestrator → decision_maker → 
    orchestrator → text_generator → orchestrator → styler → orchestrator → 
    validator → orchestrator → END (or back to text_generator on retry)
    
    Args:
        agent_config: Configuration dict with persona, triggers, actions, etc.
        
    Returns:
        Compiled StateGraph for the agent
    """
    agent_type = agent_config["agent_type"]
    agent_name = agent_config["name"]
    logger.info(f"Building agent graph for type: {agent_type}, name: {agent_name}")
    
    # Create agent graph
    agent_builder = StateGraph(AgentState)
    
    # Adding orchestrator node (routing hub)
    agent_builder.add_node("orchestrator", orchestrator_node)
    
    # Adding agent processing nodes
    agent_builder.add_node("trigger_analysis", trigger_analysis_node)
    agent_builder.add_node("decision_maker", decision_maker_node)
    agent_builder.add_node("text_generator", text_generator_node)
    agent_builder.add_node("styler", styler_node)
    agent_builder.add_node("validator", validator_node)
    
    # Entry point: START → orchestrator
    agent_builder.add_edge(START, "orchestrator")
    
    # Orchestrator uses conditional routing based on next_node
    agent_builder.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {
            "trigger_analysis": "trigger_analysis",
            "decision_maker": "decision_maker",
            "text_generator": "text_generator",
            "styler": "styler",
            "validator": "validator",
            END: END
        }
    )
    
    # All nodes return to orchestrator for routing decisions
    agent_builder.add_edge("trigger_analysis", "orchestrator")
    agent_builder.add_edge("decision_maker", "orchestrator")
    agent_builder.add_edge("text_generator", "orchestrator")
    agent_builder.add_edge("styler", "orchestrator")
    agent_builder.add_edge("validator", "orchestrator")
    
    return agent_builder.compile()


def create_agent_node(agent_name: str, agent_graph: StateGraph, agent_config: Dict[str, Any]):
    """
    Create a supervisor node that wraps an agent subgraph.
    
    This node:
    1. Copies relevant state from SupervisorState to AgentState
    2. Invokes the agent subgraph
    3. Extracts the result and formats it for the supervisor
    4. Updates agents_recent_actions with new action record if one was created
    
    Args:
        agent_name: Name of the agent (e.g., "Tamar", "Matan")
        agent_graph: Compiled agent subgraph
        agent_config: Agent configuration dict
        
    Returns:
        Node function for the supervisor graph
    """
    def agent_node(state: SupervisorState) -> Command[Literal["scheduler"]]:
        """
        Agent node in supervisor graph.
        Runs the agent subgraph and returns selected_action.
        """
        logger.info(f"Running agent: {agent_name}")
        
        # Get this agent's recent actions from supervisor state
        agents_recent_actions = state.get("agents_recent_actions", {})
        agent_recent_actions = agents_recent_actions.get(agent_name, [])
        
        # Build AgentState from SupervisorState
        agent_state: AgentState = {
            # Copy from supervisor
            "recent_messages": state["recent_messages"],
            "group_sentiment": state["group_sentiment"],
            "group_metadata": state["group_metadata"],
            
            # Agent configuration
            "selected_persona": agent_config["persona"],
            "agent_type": agent_config["agent_type"],
            "agent_goal": agent_config["agent_goal"],
            "triggers": agent_config["triggers"],
            "actions": agent_config["actions"],
            "agent_prompt": agent_config["agent_prompt"],
            
            # Initialize processing state
            "detected_trigger": None,
            "selected_action": None,
            "generated_response": None,
            "styled_response": None,
            "validation": None,
            "validation_feedback": None,
            "retry_count": 0,
            "current_node": None,
            "next_node": None,
            
            # Action history
            "recent_actions": agent_recent_actions
        }
        
        # Run the agent subgraph
        result = agent_graph.invoke(agent_state)
        
        # Extract selected_action and detected_trigger from result
        selected_action = result.get("selected_action")
        detected_trigger = result.get("detected_trigger", {})
        
        # Check if action should be ignored (neutral trigger or error)
        if not selected_action or selected_action.get("status") == "no_action_needed":
            logger.info(f"Agent {agent_name}: No action needed (neutral trigger)")
            return Command(
                update={},
                goto="scheduler"
            )
        
        # Format action for supervisor's selected_actions list
        action_entry = {
            "agent_name": agent_config["persona"].get("first_name", agent_name),
            "agent_type": agent_config["agent_type"],
            "selected_action": selected_action,
            "styled_response": result.get("styled_response", ""),
            "phone_number": agent_config["persona"].get("phone_number", ""),
            "status": selected_action.get("status", "success")
        }
        
        logger.info(f"Agent {agent_name}: Action selected - {selected_action.get('id', 'unknown')}")
        
        # Build update dict
        update_dict = {
            "selected_actions": [action_entry]
        }
        
        # Build action record for history tracking (only for approved actions)
        if selected_action.get("status") == "approved by validator":
            action_record = {
                "trigger_id": detected_trigger.get("id", ""),
                "trigger_justification": detected_trigger.get("justification", ""),
                "target_message": selected_action.get("target_message"),
                "action_id": selected_action.get("id", ""),
                "action_purpose": selected_action.get("purpose", ""),
                "action_content": result.get("styled_response", ""),
                "action_timestamp": None  # Will be filled by executor after sending
            }
            update_dict["agents_recent_actions"] = {agent_name: [action_record]}
            logger.info(f"Agent {agent_name}: Recording action - trigger: {action_record.get('trigger_id')}, action: {action_record.get('action_id')}")
        
        # Append to selected_actions using Command
        return Command(
            update=update_dict,
            goto="scheduler"
        )
    
    return agent_node


def build_supervisor_graph(config_path: Path = SUPERVISOR_CONFIG_PATH) -> StateGraph:
    """
    Build the main Supervisor graph with embedded agent subgraphs.
    
    Flow:
    START → component_B → component_C → [agent1, agent2, ...] (parallel) → scheduler → executor → END
    
    Args:
        config_path: Path to supervisor_config.json
        
    Returns:
        Compiled StateGraph for the supervisor
    """
    # Load supervisor configuration
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    
    # Create supervisor graph
    supervisor_builder = StateGraph(SupervisorState)
    
    # Add Component B (emotion analysis)
    supervisor_builder.add_node("component_B", emotion_analysis_node)
    
    # Add Component C (personality analysis)
    supervisor_builder.add_node("component_C", personality_analysis_node)
    
    # Build and add agent subgraphs
    agent_nodes = []
    for agent_config in config["agents"]:
        agent_type = agent_config["type"]
        agent_full_config = load_agent_config(agent_config)
        
        # Build agent subgraph
        agent_graph = build_agent_graph(agent_full_config)
        
        # Create wrapper node for supervisor
        # Extract name from persona for consistency
        persona = agent_full_config["persona"]
        first_name = persona.get("first_name", "")
        last_name = persona.get("last_name", "")
        
        if first_name and last_name:
            full_name = f"{first_name}_{last_name}"
        elif first_name:
            full_name = first_name
        else:
            # Fallback to config name if persona is missing names
            full_name = agent_full_config["name"].replace(" ", "_")
            
        safe_agent_name = full_name.replace(" ", "_")
        agent_node_name = f"agent_{agent_type}_{safe_agent_name}"
        
        # Use first name for logging/display
        agent_display_name = first_name if first_name else agent_full_config["name"]
        
        agent_node = create_agent_node(agent_display_name, agent_graph, agent_full_config)
        
        supervisor_builder.add_node(agent_node_name, agent_node)
        agent_nodes.append(agent_node_name)
        
        logger.info(f"Added agent node: {agent_node_name} ({agent_display_name})")
    
    # Add scheduler node
    supervisor_builder.add_node("scheduler", scheduler_node)
    
    # Add executor node
    supervisor_builder.add_node("executor", executor_node)
    
    # Define edges
    # START → component_B
    supervisor_builder.add_edge(START, "component_B")
    
    # component_B → component_C
    supervisor_builder.add_edge("component_B", "component_C")
    
    # component_C → all agents (parallel execution)
    for agent_node_name in agent_nodes:
        supervisor_builder.add_edge("component_C", agent_node_name)
    
    # All agents already route to scheduler via Command(goto="scheduler")
    # No explicit edges needed due to Command-based routing
    
    # scheduler → executor
    supervisor_builder.add_edge("scheduler", "executor")
    
    # executor → END
    supervisor_builder.add_edge("executor", END)
    
    return supervisor_builder.compile()


if __name__ == "__main__":
    # Test building the graph
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    
    try:
        graph = build_supervisor_graph()
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
