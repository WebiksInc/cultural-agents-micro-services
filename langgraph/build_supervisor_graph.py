"""
Supervisor Graph Builder

Builds the complete hierarchical LangGraph system:
- Supervisor graph with Component B and agent subgraphs
- Agent subgraph for Tamar (active agent)
- Infinite loop execution with message polling and action execution
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

# Import state classes
from states.agent_state import AgentState
from states.supervisor_state import SupervisorState

# Import supervisor nodes
from nodes.supervisor.supervisor import supervisor_node, load_agent_personas
from nodes.supervisor.component_B import emotion_analysis_node
from nodes.supervisor.scheduler import scheduler_node

# Import agent nodes
from nodes.agent.orchestrator import orchestrator_node
from nodes.agent.trigger_analysis import trigger_analysis_node
from nodes.agent.decision_maker import decision_maker_node
from nodes.agent.component_E1 import text_generator_node
from nodes.agent.component_E2 import styler_node
from nodes.agent.validator import validator_node

# Configure logging with Logfire
from logs.logfire_config import setup_logfire, get_logger

# Setup Logfire first (captures all subsequent logging)
setup_logfire(service_name="supervisor-graph")

# Configure basic logging format for console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config" / "supervisor_config.json"
with open(CONFIG_PATH, 'r') as f:
    CONFIG = json.load(f)


def load_agent_config(agent_type: str) -> Dict[str, Any]:
    """
    Load triggers, actions, and persona for a specific agent type.
    
    Args:
        agent_type: Type of agent (e.g., "active", "off_the_radar")
        
    Returns:
        Dict with triggers, actions, and persona data
    """
    base_path = Path(__file__).parent
    
    # Load triggers
    triggers_path = base_path / "triggers" / agent_type / f"{agent_type}_triggers.json"
    with open(triggers_path, 'r') as f:
        triggers_data = json.load(f)
    
    # Load actions
    actions_path = base_path / "actions" / agent_type / f"{agent_type}_actions.json"
    with open(actions_path, 'r') as f:
        actions_data = json.load(f)
    
    # Load persona (from config)
    agent_config = next(a for a in CONFIG["agents"] if a["type"] == agent_type)
    persona_path = base_path / agent_config["persona_file"]
    with open(persona_path, 'r') as f:
        persona_data = json.load(f)
    
    logger.info(f"Loaded config for {agent_type} agent: {persona_data.get('first_name', 'Unknown')}")
    
    return {
        "triggers": triggers_data,
        "actions": actions_data,
        "persona": persona_data,
        "agent_type": agent_type
    }


def build_agent_subgraph(agent_type: str, agent_config: Dict[str, Any]) -> StateGraph:
    """
    Build agent subgraph with orchestrator and all processing nodes.
    
    Args:
        agent_type: Type of agent (e.g., "active")
        agent_config: Agent configuration with triggers, actions, persona
        
    Returns:
        Compiled StateGraph for the agent
    """
    logger.info(f"Building agent subgraph for {agent_type}")
    
    # Create agent graph
    agent_graph = StateGraph(AgentState)
    
    # Add all agent nodes
    agent_graph.add_node("orchestrator", orchestrator_node)
    agent_graph.add_node("trigger_analysis", trigger_analysis_node)
    agent_graph.add_node("decision_maker", decision_maker_node)
    agent_graph.add_node("text_generator", text_generator_node)
    agent_graph.add_node("styler", styler_node)
    agent_graph.add_node("validator", validator_node)
    
    # Set entry point - start at orchestrator (which will route to trigger_analysis)
    agent_graph.set_entry_point("orchestrator")
    
    # After trigger_analysis, go to orchestrator to decide next step
    agent_graph.add_edge("trigger_analysis", "orchestrator")
    
    # Add conditional edges based on orchestrator's next_node decision
    def route_from_orchestrator(state: AgentState) -> str:
        """Route based on orchestrator's decision."""
        next_node = state.get("next_node")
        
        # DEBUG
        # logger.info(f"route_from_orchestrator called - next_node={next_node}, current_node={state.get('current_node')}")
        
        # Handle None or empty next_node
        if not next_node:
            logger.warning(f"Orchestrator returned None for next_node, defaulting to END")
            return END
            
        logger.debug(f"Orchestrator routing to: {next_node}")
        return next_node
    
    # Orchestrator routes to all possible next nodes
    agent_graph.add_conditional_edges(
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
    
    # All other nodes (except trigger_analysis which we already connected) return to orchestrator
    agent_graph.add_edge("decision_maker", "orchestrator")
    agent_graph.add_edge("text_generator", "orchestrator")
    agent_graph.add_edge("styler", "orchestrator")
    agent_graph.add_edge("validator", "orchestrator")
    
    # Compile the agent graph
    compiled_agent = agent_graph.compile()
    logger.info(f"Agent subgraph for {agent_type} compiled successfully")
    
    return compiled_agent


def create_agent_wrapper(agent_type: str, agent_config: Dict[str, Any], agent_graph: StateGraph):
    """
    Create a wrapper function that invokes the agent subgraph.
    
    Args:
        agent_type: Type of agent
        agent_config: Agent configuration
        agent_graph: Compiled agent graph
        
    Returns:
        Function that can be used as a node in supervisor graph
    """
    def agent_node(state: SupervisorState) -> SupervisorState:
        """
        Agent wrapper node that copies supervisor state to agent state and runs agent graph.
        
        Args:
            state: Supervisor state
            
        Returns:
            Updated supervisor state with agent's selected_action
        """
        logger.info(f"Running {agent_type} agent ({agent_config['persona']['first_name']})\n")
        
        # Create agent state from supervisor state (COPY data)
        agent_state = AgentState(
            # Data from supervisor
            recent_messages=state["recent_messages"].copy(),
            group_sentiment=state["group_sentiment"],
            group_metadata=state["group_metadata"].copy(),
            
            # Agent configuration
            selected_persona=agent_config["persona"],
            agent_type=agent_type,
            agent_goal=agent_config["persona"].get("agent_goal", "You are an active member of the group."),
            triggers=agent_config["triggers"],
            actions=agent_config["actions"],
            
            # Processing outputs (initialized)
            detected_trigger=None,
            selected_action=None,
            agent_prompt="",
            generated_response=None,
            styled_response=None,
            validation=None,
            validation_feedback=None,
            retry_count=0,
            current_node=None,
            next_node=None
        )
        
        # Run agent graph
        logger.info(f"Invoking {agent_type} agent graph...")
        result = agent_graph.invoke(agent_state)
        
        # Extract selected_action from agent result
        selected_action = result.get("selected_action")
        
        if selected_action:
            logger.info(f"{agent_type} agent produced action: {selected_action.get('id', 'unknown')}")
            
            # Add to supervisor's selected_actions list
            if "selected_actions" not in state:
                state["selected_actions"] = []
            
            state["selected_actions"].append(selected_action)
        else:
            logger.info(f"{agent_type} agent decided not to take action")
        
        return state
    
    return agent_node


def build_supervisor_graph(agent_personas: Dict[str, Dict[str, Any]]) -> StateGraph:
    """
    Build the main supervisor graph with Component B and agent subgraphs.
    
    Args:
        agent_personas: Pre-loaded agent personas
        
    Returns:
        Compiled supervisor StateGraph
    """
    logger.info("Building supervisor graph...\n")
    
    # Create supervisor graph
    supervisor_graph = StateGraph(SupervisorState)
    
    # Build agent subgraphs and create wrapper nodes
    agent_subgraphs = {}
    for agent_config_item in CONFIG["agents"]:
        agent_type = agent_config_item["type"]
        
        # Load agent configuration
        agent_config = load_agent_config(agent_type)
        
        # Build agent subgraph
        agent_graph = build_agent_subgraph(agent_type, agent_config)
        agent_subgraphs[agent_type] = agent_graph
        
        # Create wrapper node for this agent
        agent_wrapper = create_agent_wrapper(agent_type, agent_config, agent_graph)
        supervisor_graph.add_node(f"{agent_type}_agent", agent_wrapper)
    
    # Create supervisor wrapper that passes agent_personas
    def supervisor_wrapper(state: SupervisorState) -> SupervisorState:
        """Wrapper for supervisor_node that includes agent_personas."""
        return supervisor_node(state, agent_personas)
    
    # Add supervisor nodes
    supervisor_graph.add_node("supervisor", supervisor_wrapper)
    supervisor_graph.add_node("component_b", emotion_analysis_node)
    supervisor_graph.add_node("scheduler", scheduler_node)
    
    # Set entry point
    supervisor_graph.set_entry_point("supervisor")
    
    # Define routing logic from supervisor
    def route_from_supervisor(state: SupervisorState) -> str:
        """
        Route from supervisor based on whether there are unprocessed messages or pending actions.
        
        Priority:
        1. If there are pending actions in execution_queue, wait and loop to supervisor to execute them
        2. If there are unprocessed messages, route to component_b to analyze them
        3. Otherwise, loop back to supervisor to poll for new messages
        """
        import time
        
        recent_messages = state.get("recent_messages", [])
        execution_queue = state.get("execution_queue", [])
        
        # Debug logging
        logger.info(f"DEBUG route_from_supervisor: execution_queue has {len(execution_queue)} items")
        if execution_queue:
            for i, action in enumerate(execution_queue):
                logger.info(f"  Action {i+1}: status={action.get('status')}, scheduled={action.get('scheduled_time')}")
        
        # Check for pending actions FIRST - they have priority over message processing
        pending_actions = [a for a in execution_queue if a.get("status") == "pending"]
        if pending_actions:
            logger.info(f"{len(pending_actions)} pending actions - waiting 2s before checking execution queue")
            time.sleep(2)  # Wait for actions to become ready
            return "supervisor"
        
        # Check for unprocessed messages
        unprocessed_messages = [m for m in recent_messages if not m.get('processed', False)]
        if unprocessed_messages:
            logger.info(f"{len(unprocessed_messages)} unprocessed messages detected, routing to component_b")
            return "component_b"
        
        # No pending actions and no unprocessed messages - loop back to supervisor
        # Add delay to prevent tight loop when waiting for new messages
        # This is where we control the polling frequency
        logger.info("No pending actions or unprocessed messages, sleeping 20s before next poll")
        time.sleep(60)  # Wait before next message poll cycle
        logger.info("Looping back to supervisor for next message check\n")
        return "supervisor"
    
    # Conditional edge from supervisor
    supervisor_graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "component_b": "component_b",
            "supervisor": "supervisor"
        }
    )
    
    # From component_b, go to all agent nodes in parallel
    # For now we only have active_agent
    for agent_config_item in CONFIG["agents"]:
        agent_type = agent_config_item["type"]
        supervisor_graph.add_edge("component_b", f"{agent_type}_agent")
    
    # From agent nodes, go to scheduler
    for agent_config_item in CONFIG["agents"]:
        agent_type = agent_config_item["type"]
        supervisor_graph.add_edge(f"{agent_type}_agent", "scheduler")
    
    # From scheduler, loop back to supervisor
    supervisor_graph.add_edge("scheduler", "supervisor")
    
    # Compile supervisor graph
    # Recursion limit will be set at runtime via invoke() config parameter
    compiled_supervisor = supervisor_graph.compile()
    logger.info("Supervisor graph compiled successfully\n")
    
    return compiled_supervisor


def run_supervisor_graph():
    """
    Main entry point: Load personas, build graph, and run infinite loop.
    """
    logger.info("=" * 80)
    logger.info("STARTING SUPERVISOR GRAPH SYSTEM")
    logger.info("=" * 80)
    
    # Load agent personas once at startup
    # logger.info("Loading agent personas...")
    agent_personas = load_agent_personas()
    
    # Build the complete graph
    logger.info("Building supervisor graph with agent subgraphs...")
    supervisor_graph = build_supervisor_graph(agent_personas)
    
    # Initialize supervisor state
    initial_state = SupervisorState(
        recent_messages=[],
        group_sentiment="neutral",
        group_metadata=CONFIG["group_metadata"].copy(),
        selected_actions=[],
        execution_queue=[],
        current_nodes=None,
        next_nodes=None
    )
    
    # logger.info("=" * 80)
    logger.info("GRAPH BUILT SUCCESSFULLY - STARTING INFINITE LOOP")
    # logger.info("Press Ctrl+C to stop")
    # logger.info("=" * 80)
    
    # Run for 2 iterations (for testing)
    state = initial_state
    iteration = 0
    MAX_ITERATIONS = 2
    
    try:
        while iteration < MAX_ITERATIONS:
            iteration += 1
            logger.info(f"\n{'=' * 80}")
            logger.info(f"ITERATION {iteration} of {MAX_ITERATIONS}")
            logger.info(f"{'=' * 80}")
            
            # Invoke the graph with increased recursion limit
            # The supervisor loops continuously (supervisor -> supervisor), so we need a higher limit
            # With the sleep delays added, each loop takes ~5 seconds, so 100 iterations = ~500 seconds
            state = supervisor_graph.invoke(
                state, 
                config={"recursion_limit": 100}
            )
            
            # Brief sleep to avoid tight loop
            import time
            time.sleep(1)
        
        logger.info(f"\n{'=' * 80}")
        logger.info(f"COMPLETED {MAX_ITERATIONS} ITERATIONS SUCCESSFULLY")
        logger.info(f"{'=' * 80}")
            
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 80)
        logger.info("SUPERVISOR STOPPED BY USER (Ctrl+C)")
        logger.info(f"Total iterations: {iteration}")
        logger.info("=" * 80)
    except Exception as e:
        logger.error(f"ERROR in supervisor loop: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_supervisor_graph()
