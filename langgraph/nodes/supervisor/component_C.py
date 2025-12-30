"""
Component C: Personality Analysis Node (Big Five / OCEAN Model)

Analyzes personality traits for participants based on their messages.
Runs 5 parallel API calls (one per trait) and saves results to memory.
"""
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional, Tuple
from langchain_core.messages import HumanMessage
from langchain.chat_models import init_chat_model

# utilities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils import load_prompt, get_model_settings, format_message_for_prompt, is_agent_sender, load_agent_personas
from logs.logfire_config import get_logger
from logs import log_node_start, log_prompt, log_node_output

# Memory system
from memory import (
    get_participant_data,
    save_personality_analysis,
    initialize_participants,
    list_participants
)

# Configure logging
logger = get_logger(__name__)

# Load supervisor config
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "supervisor_config.json"
with open(CONFIG_PATH, 'r') as f:
    CONFIG = json.load(f)

PERSONALITY_CONFIG = CONFIG.get("personality_analysis", {})
MIN_MESSAGES_FOR_ANALYSIS = PERSONALITY_CONFIG.get("min_messages_for_analysis", 1)
CONFIDENCE_THRESHOLDS = PERSONALITY_CONFIG.get("confidence_thresholds", {})
CONFIDENCE_PENALTY_CONFIG = PERSONALITY_CONFIG.get("message_count_confidence_penalty", {})
STOP_REANALYSIS_WHEN_CONFIDENT = PERSONALITY_CONFIG.get("stop_reanalysis_when_confident", True)
MAX_RECENT_MESSAGES = CONFIG.get("polling", {}).get("max_recent_messages", 50)

# Big Five traits
BIG5_TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]



def build_username_userid_mapping(messages: List[Dict]) -> Dict[str, str]:
    """
    Build a mapping from display name -> user_id from messages.
    Uses the same name format as format_message_for_prompt (first_name + last_name).
    
    Args:
        messages: List of message dicts with sender info and sender_id
        
    Returns:
        Dict mapping display name (lowercase) to user_id
    """
    mapping = {}
    for msg in messages:
        user_id = str(msg.get("sender_id", "")).strip()
        if not user_id:
            continue
        
        # Use same logic as format_message_for_prompt
        first_name = msg.get("sender_first_name", "").strip()
        last_name = msg.get("sender_last_name", "").strip()
        username = msg.get("sender_username", "").strip()
        
        if first_name and last_name:
            display_name = f"{first_name} {last_name}"
        elif first_name:
            display_name = first_name
        elif username:
            display_name = username
        else:
            continue
        
        mapping[display_name.lower()] = user_id
    
    return mapping


def count_user_messages(messages: List[Dict]) -> Dict[str, int]:
    """
    Count messages per user by display name.
    Uses the same name format as format_message_for_prompt.
    
    Args:
        messages: List of message dicts
        
    Returns:
        Dict mapping display name (lowercase) to message count
    """
    counts = {}
    for msg in messages:
        first_name = msg.get("sender_first_name", "").strip()
        last_name = msg.get("sender_last_name", "").strip()
        username = msg.get("sender_username", "").strip()
        
        if first_name and last_name:
            display_name = f"{first_name} {last_name}"
        elif first_name:
            display_name = first_name
        elif username:
            display_name = username
        else:
            continue
        
        key = display_name.lower()
        counts[key] = counts.get(key, 0) + 1
    
    return counts


def format_conversation_for_prompt(messages: List[Dict]) -> str:
    """
    Format messages into conversation string for the prompt.
    Uses the shared format_message_for_prompt utility.
    
    Args:
        messages: List of message dicts
        
    Returns:
        Formatted conversation string
    """
    lines = []
    for msg in messages:
        # Use utility function - no emotion since we're analyzing personality, not emotions
        formatted = format_message_for_prompt(
            msg, 
            include_timestamp=True, 
            include_emotion=False
        )
        lines.append(formatted)
    
    return "\n".join(lines)


def is_user_confident_enough(
    chat_id: str,
    user_id: str,
    confidence_thresholds: Dict[str, float]
) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if a user already has confident enough personality analysis.
    
    Args:
        chat_id: Telegram chat ID
        user_id: User ID to check
        confidence_thresholds: Dict of trait -> threshold
        
    Returns:
        Tuple of (is_confident_enough, latest_analysis_or_empty)
    """
    participant_data = get_participant_data(chat_id, user_id)
    
    if not participant_data:
        return False, {}
    
    snapshots = participant_data.get("personality_snapshots", [])
    if not snapshots:
        return False, {}
    
    # Get latest snapshot
    latest = snapshots[-1]
    big5 = latest.get("personality_analysis", {}).get("big5", {})
    
    if not big5:
        return False, {}
    
    # Check if all traits meet confidence threshold
    all_confident = True
    for trait in BIG5_TRAITS:
        trait_data = big5.get(trait, {})
        confidence = trait_data.get("confidence", 0)
        threshold = confidence_thresholds.get(trait, 0.9)
        
        if confidence < threshold:
            all_confident = False
            break
    
    return all_confident, big5


def analyze_single_trait(
    trait: str,
    conversation: str,
    model_name: str,
    temperature: float,
    provider: str
) -> Dict[str, Dict[str, Any]]:
    """
    Analyze a single Big5 trait for all users in conversation.
    
    Args:
        trait: Trait name (e.g., "openness")
        conversation: Formatted conversation string
        model_name: LLM model name
        temperature: Model temperature
        provider: Model provider
        
    Returns:
        Dict mapping username -> {score, confidence, justification}
    """
    try:
        # Load prompt template
        prompt_template = load_prompt(f"supervisor_graph/component_C/{trait}.txt")
        prompt = prompt_template.replace("{{CONVERSATION}}", conversation)
        
        # Initialize model
        model = init_chat_model(
            model=model_name,
            model_provider=provider,
            temperature=temperature
        )
        
        # Call LLM
        response = model.invoke([HumanMessage(content=prompt)])
        response_text = response.content
        
        # Parse JSON response
        # Handle potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        result = json.loads(response_text.strip())
        
        logger.info(f"Successfully analyzed {trait} for {len(result)} users")
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON for {trait}: {e}")
        logger.error(f"Response was: {response_text[:500]}...")
        return {}
    except Exception as e:
        logger.error(f"Error analyzing {trait}: {e}")
        return {}


def run_parallel_trait_analysis(
    conversation: str,
    model_name: str,
    temperature: float,
    provider: str,
    state: Dict[str, Any] = None
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Run all 5 Big5 trait analyses in parallel.
    
    Args:
        conversation: Formatted conversation string
        model_name: LLM model name
        temperature: Model temperature
        provider: Model provider
        state: SupervisorState for logging
        
    Returns:
        Dict mapping trait -> username -> {score, confidence, justification}
    """
    results = {}
    
    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for trait in BIG5_TRAITS:
            future = executor.submit(
                analyze_single_trait,
                trait,
                conversation,
                model_name,
                temperature,
                provider
            )
            futures[trait] = future
        
        # Collect results
        for trait, future in futures.items():
            try:
                results[trait] = future.result(timeout=60)
            except Exception as e:
                logger.error(f"Timeout or error for {trait}: {e}")
                results[trait] = {}
    
    return results


def merge_trait_results_by_user(
    trait_results: Dict[str, Dict[str, Dict[str, Any]]]
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Reorganize trait results from trait->user to user->trait format.
    Cleans up usernames by removing annotations like "(Agent)", "(YOU)".
    
    Args:
        trait_results: Dict mapping trait -> username -> {score, confidence, justification}
        
    Returns:
        Dict mapping username -> trait -> {score, confidence, justification}
    """
    import re
    user_results = {}
    
    for trait, user_scores in trait_results.items():
        for username, data in user_scores.items():
            # Clean username: remove annotations like (Agent), (YOU), etc.
            clean_username = re.sub(r'\s*\([^)]*\)\s*', '', username).strip()
            username_lower = clean_username.lower()
            
            if username_lower not in user_results:
                user_results[username_lower] = {}
            user_results[username_lower][trait] = data
    
    return user_results


def personality_analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Component C: Personality Analysis Node
    
    Analyzes Big Five personality traits for participants based on their messages.
    
    Flow:
    1. Build username->user_id mapping and message counts from recent_messages
    2. Format conversation for prompts
    3. Run 5 parallel API calls (one per trait)
    4. Filter results:
       - Skip agents
       - Skip users already confident enough (if stop_reanalysis_when_confident=True)
       - Skip users with < min_messages_for_analysis
    5. Apply confidence penalty based on message count
    6. Save to files via memory system
    7. Update state cache
    
    Args:
        state: SupervisorState dict containing recent_messages
        
    Returns:
        Dict with updated personality_analysis cache
    """
    log_node_start("component_c", {
        "total_messages": len(state.get('recent_messages', []))
    }, supervisor_state=state)
    
    recent_messages = state.get('recent_messages', [])
    chat_id = CONFIG["telegram"]["chat_id"]
    
    # Early exit if no messages
    if not recent_messages:
        logger.info("No recent messages. Skipping personality analysis.")
        return {}
    
    # Initialize participants in memory if needed
    init_result = initialize_participants(chat_id, verbose=False)
    
    # Build mappings
    username_to_userid = build_username_userid_mapping(recent_messages)
    user_message_counts = count_user_messages(recent_messages)
    agent_personas = load_agent_personas()
    agent_names = [p.get("user_name", "") for p in agent_personas]
    
    logger.info(f"Found {len(username_to_userid)} unique users in recent messages")
    logger.info(f"Agent usernames to skip: {agent_names}")
    
    # Format conversation for prompt
    conversation = format_conversation_for_prompt(recent_messages)
    
    # Get model settings
    model_settings = get_model_settings('component_C', 'COMPONENT_C_MODEL')
    model_name = model_settings['model']
    temperature = model_settings['temperature']
    provider = model_settings['provider']
    
    # Generate and log prompts for all traits
    prompts = {}
    for trait in BIG5_TRAITS:
        try:
            prompt_template = load_prompt(f"supervisor_graph/component_C/{trait}.txt")
            prompts[trait] = prompt_template.replace("{{CONVERSATION}}", conversation)
        except Exception as e:
            logger.error(f"Failed to generate prompt for {trait}: {e}")
            prompts[trait] = f"Error generating prompt: {e}"
            
    # Log all prompts in one entry
    log_prompt("component_c", prompts, model=model_name, temperature=temperature, supervisor_state=state)
    
    # Run parallel trait analysis
    trait_results = run_parallel_trait_analysis(
        conversation,
        model_name,
        temperature,
        provider,
        state
    )
    
    # Merge results by user
    user_results = merge_trait_results_by_user(trait_results)
    
    logger.info(f"Got personality results for {len(user_results)} users")
    
    # Filter and save results
    personality_cache = state.get('personality_analysis', {}) or {}
    saved_count = 0
    skipped_agents = 0
    skipped_confident = 0
    skipped_low_messages = 0
    
    # Iterate over ALL users found in messages to ensure we load existing data
    # even if LLM didn't analyze them in this specific run
    for username_lower, user_id in username_to_userid.items():
        # Skip agents
        if is_agent_sender(display_name=username_lower, agent_personas=agent_personas):
            logger.debug(f"Skipping agent: {username_lower}")
            skipped_agents += 1
            continue
            
        # Check existing data on disk
        is_confident, existing_analysis = is_user_confident_enough(
            chat_id, user_id, CONFIDENCE_THRESHOLDS
        )
        
        # 1. If we already have confident data, use it and skip new analysis
        if STOP_REANALYSIS_WHEN_CONFIDENT and is_confident:
            logger.debug(f"Skipping {username_lower}: already confident enough")
            personality_cache[user_id] = existing_analysis
            skipped_confident += 1
            continue
            
        # 2. Check if we have NEW analysis from this run
        big5_data = user_results.get(username_lower)
        
        if big5_data:
            # Check message count constraints for SAVING new data
            msg_count = user_message_counts.get(username_lower, 0)
            if msg_count < MIN_MESSAGES_FOR_ANALYSIS:
                logger.debug(f"Skipping {username_lower}: only {msg_count} messages (min: {MIN_MESSAGES_FOR_ANALYSIS})")
                skipped_low_messages += 1
                # Fallback to existing data if available
                if existing_analysis:
                    personality_cache[user_id] = existing_analysis
                continue
            
            # Ensure all 5 traits have data
            complete_big5 = {}
            for trait in BIG5_TRAITS:
                if trait in big5_data:
                    complete_big5[trait] = big5_data[trait]
                else:
                    # Default for missing traits
                    complete_big5[trait] = {
                        "score": 3,
                        "confidence": 0.1,
                        "justification": "No data available for this trait"
                    }
            
            # Save to memory (file)
            save_result = save_personality_analysis(
                chat_id=chat_id,
                user_id=user_id,
                big5_results=complete_big5,
                confidence_penalty_config=CONFIDENCE_PENALTY_CONFIG,
                verbose=False
            )
            
            if save_result.get("success"):
                saved_count += 1
                # Update cache with the saved results (includes confidence penalty)
                personality_cache[user_id] = save_result.get("trait_results", complete_big5)
                logger.info(
                    f"Saved personality for {username_lower} (user_id: {user_id}) - "
                    f"confidence: {save_result.get('overall_confidence', 'N/A')}"
                )
            else:
                logger.error(f"Failed to save personality for {username_lower}: {save_result.get('error')}")
        else:
            # No new data (LLM skipped them). Fallback to existing if available.
            if existing_analysis:
                personality_cache[user_id] = existing_analysis
    
    # Update recent_messages with personality data
    updated_messages = []
    updated_count = 0
    for msg in recent_messages:
        sender_id = str(msg.get("sender_id", "")).strip()
        if sender_id and sender_id in personality_cache:
            msg['sender_personality'] = personality_cache[sender_id]
            updated_count += 1
        updated_messages.append(msg)
    
    # Log summary
    log_node_output("component_c", {
        "users_analyzed": len(user_results),
        "users_saved": saved_count,
        "skipped_agents": skipped_agents,
        "skipped_confident": skipped_confident,
        "skipped_low_messages": skipped_low_messages
    }, supervisor_state=state)
    
    # Trim recent_messages to configured maximum (keep newest)
    trimmed_messages = updated_messages[:MAX_RECENT_MESSAGES]
    
    return {
        'personality_analysis': personality_cache,
        'recent_messages': trimmed_messages
    }
