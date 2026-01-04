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
from utils import (
    load_prompt, 
    get_model_settings, 
    format_message_for_prompt, 
    is_agent_sender, 
    load_agent_personas,
    get_agent_display_names,
    build_display_name
)
from logs.logfire_config import get_logger
from logs import log_node_start, log_prompt, log_node_output

# Memory system
from memory import (
    get_participant_data,
    get_participant_messages,
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


def apply_confidence_penalty(
    big5_results: Dict[str, Dict[str, Any]], 
    message_count: int, 
    penalty_config: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """
    Apply confidence penalty based on message count.
    
    Business logic: When analyzing personality with fewer than the minimum required messages,
    apply a penalty to reduce confidence scores proportionally.
    
    Args:
        big5_results: Dict of trait -> {score, confidence, justification}
        message_count: Number of messages analyzed
        penalty_config: Config dict with min_messages_full_confidence and penalty_factor
        
    Returns:
        Modified big5_results with adjusted confidence scores
    """
    min_messages = penalty_config.get("min_messages_full_confidence", 15)
    penalty_factor = penalty_config.get("penalty_factor", 0.03)
    
    # Only apply penalty if below threshold
    if message_count >= min_messages:
        return big5_results
    
    # Apply penalty to each trait
    penalty = (min_messages - message_count) * penalty_factor
    
    for trait, data in big5_results.items():
        raw_confidence = data.get("confidence", 0)
        # Store raw confidence for transparency
        data["raw_confidence"] = raw_confidence
        # Apply penalty (cannot go below 0)
        data["confidence"] = round(max(0, raw_confidence - penalty), 2)
    
    return big5_results


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
        
        # Build display name using shared utility
        display_name = build_display_name(
            first_name=msg.get("sender_first_name", ""),
            last_name=msg.get("sender_last_name", ""),
            username=msg.get("sender_username", "")
        )
        if not display_name:
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
        # Build display name using shared utility
        display_name = build_display_name(
            first_name=msg.get("sender_first_name", ""),
            last_name=msg.get("sender_last_name", ""),
            username=msg.get("sender_username", "")
        )
        if not display_name:
            continue
        
        key = display_name.lower()
        counts[key] = counts.get(key, 0) + 1
    
    return counts


def format_conversation_for_prompt(messages: List[Dict]) -> str:
    """
    Format messages into conversation string for the prompt.
    Uses the shared format_message_for_prompt utility.
    Adds [NEW] suffix to unprocessed messages.
    
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
        # Add [NEW] suffix for unprocessed messages
        if not msg.get('processed', False):
            formatted = f"{formatted} [NEW]"
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


def build_constraints_string(
    agent_names: List[str],
    users_to_analyze: List[str] = None
) -> str:
    """
    Build the constraints section for the prompt.
    
    Args:
        agent_names: List of agent display names to exclude
        users_to_analyze: List of user display names to analyze (if None, analyze all non-agents)
        
    Returns:
        Constraints string for prompt injection
    """
    constraints = []
    
    # Agent exclusion
    if agent_names:
        agent_list = ", ".join(agent_names)
        constraints.append(
            f"1. **DO NOT** analyze these users: {agent_list}\n"
            f"   - Skip them entirely in your output."
        )
    
    # Target users
    if users_to_analyze:
        user_list = ", ".join(users_to_analyze)
        constraints.append(
            f"2. **ONLY** analyze these specific users (they have new activity): {user_list}\n"
            f"   - Do not include anyone else in your output.\n"
            f"   - If the list is empty or all users are agents, return an empty JSON: {{}}"
        )
    else:
        constraints.append(
            "2. Analyze all human participants in the conversation (excluding agents listed above)."
        )
    
    return "\n\n".join(constraints)


def get_existing_analysis_for_users(
    chat_id: str,
    users_to_analyze: Dict[str, str]
) -> Dict[str, Dict[str, Any]]:
    """
    Get existing personality analysis for users who are being analyzed.
    
    Args:
        chat_id: Telegram chat ID
        users_to_analyze: Dict mapping display_name -> user_id
        
    Returns:
        Dict mapping display_name -> {trait -> {score, justification}} for users with prior analysis
    """
    existing_analysis = {}
    
    for display_name, user_id in users_to_analyze.items():
        participant_data = get_participant_data(chat_id, user_id)
        if not participant_data:
            continue
        
        snapshots = participant_data.get("personality_snapshots", [])
        if not snapshots:
            continue
        
        # Get latest snapshot (most recent is first after our change)
        latest = snapshots[0]
        big5 = latest.get("personality_analysis", {}).get("big5", {})
        
        if big5:
            existing_analysis[display_name] = big5
    
    return existing_analysis


def build_existing_analysis_string(
    trait: str,
    existing_analysis: Dict[str, Dict[str, Any]],
    users_to_analyze: List[str]
) -> str:
    """
    Build the existing analysis section for a specific trait prompt.
    
    Args:
        trait: The trait being analyzed (e.g., "openness")
        existing_analysis: Dict mapping display_name -> {trait -> {score, justification}}
        users_to_analyze: List of display names being analyzed
        
    Returns:
        Existing analysis string for prompt injection (empty if no prior analysis)
    """
    lines = []
    
    for display_name in users_to_analyze:
        if display_name not in existing_analysis:
            continue
        
        user_traits = existing_analysis[display_name]
        if trait not in user_traits:
            continue
        
        trait_data = user_traits[trait]
        score = trait_data.get("score", "N/A")
        justification = trait_data.get("justification", "No justification available")
        
        lines.append(
            f"- **{display_name}**: Previous score = {score}\n"
            f"  Previous justification: \"{justification}\""
        )
    
    if not lines:
        return ""
    
    return (
        "The following users have been analyzed before. Review their previous analysis:\n\n"
        + "\n\n".join(lines) + "\n\n"
        "**How to identify new messages:** Messages ending with **[NEW]** are unprocessed and weren't considered in prior analysis. "
        "Focus on these to determine if they change or support the prior assessment.\n\n"
        "**Instructions for previously analyzed users:**\n"
        "- Only change the score if [NEW] messages provide clear evidence that **contradicts or extends** your previous assessment.\n"
        "- For each previously analyzed user, add these fields **INSIDE their JSON object**:\n"
        "  - `\"changed\": false` if you keep the same score\n"
        "  - `\"changed\": true` if you change the score\n"
        "  - `\"change_reason\"` explaining why (only when changed=true)\n"
        "- For users WITHOUT prior analysis, do NOT include the `changed` field.\n"
        "- Example: `{\"Alice\": {\"score\": 4, \"confidence\": 0.85, \"justification\": \"...\", \"changed\": false}}`"
    )


def identify_users_with_new_messages(
    recent_messages: List[Dict],
    agent_personas: List[Dict]
) -> Tuple[set, Dict[str, str]]:
    """
    Identify users who have unprocessed (new) messages.
    
    Args:
        recent_messages: List of message dicts
        agent_personas: List of agent persona dicts
        
    Returns:
        Tuple of (set of user_ids with new messages, dict of display_name -> user_id for those users)
    """
    users_with_new_messages = set()
    new_user_mapping = {}
    
    for msg in recent_messages:
        # Only consider unprocessed messages as "new"
        if msg.get('processed', False):
            continue
            
        sender_id = str(msg.get('sender_id', '')).strip()
        if not sender_id:
            continue
            
        # Skip agents
        if is_agent_sender(message=msg, agent_personas=agent_personas):
            continue
        
        # Build display name using shared utility
        display_name = build_display_name(
            first_name=msg.get("sender_first_name", ""),
            last_name=msg.get("sender_last_name", ""),
            username=msg.get("sender_username", "")
        )
        if not display_name:
            continue
        
        users_with_new_messages.add(sender_id)
        new_user_mapping[display_name] = sender_id
    
    return users_with_new_messages, new_user_mapping


def analyze_single_trait(
    trait: str,
    conversation: str,
    model_name: str,
    temperature: float,
    provider: str,
    constraints: str = "",
    existing_analysis_str: str = ""
) -> tuple[Dict[str, Dict[str, Any]], str]:
    """
    Analyze a single Big5 trait for specified users in conversation.
    
    Args:
        trait: Trait name (e.g., "openness")
        conversation: Formatted conversation string
        model_name: LLM model name
        temperature: Model temperature
        provider: Model provider
        constraints: Constraints string to inject into prompt
        existing_analysis_str: Previous analysis for this trait (for iterative updates)
        
    Returns:
        Tuple of (Dict mapping username -> {score, confidence, justification, changed?, change_reason?}, raw_llm_output)
    """
    raw_output = ""
    try:
        # Load prompt template
        prompt_template = load_prompt(f"supervisor_graph/component_C/{trait}.txt")
        prompt = prompt_template.replace("{{CONVERSATION}}", conversation)
        prompt = prompt.replace("{{CONSTRAINTS}}", constraints)
        prompt = prompt.replace("{{EXISTING_ANALYSIS}}", existing_analysis_str)
        
        # Initialize model
        model = init_chat_model(
            model=model_name,
            model_provider=provider,
            temperature=temperature
        )
        
        # Call LLM
        response = model.invoke([HumanMessage(content=prompt)])
        response_text = response.content
        raw_output = response_text  # Store raw output before parsing
        
        # Parse JSON response
        # Handle potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        result = json.loads(response_text.strip())
        
        logger.info(f"Successfully analyzed {trait} for {len(result)} users")
        return result, raw_output
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON for {trait}: {e}")
        logger.error(f"Response was: {response_text[:500]}...")
        return {}, raw_output
    except Exception as e:
        logger.error(f"Error analyzing {trait}: {e}")
        return {}, raw_output


def run_parallel_trait_analysis(
    conversation: str,
    model_name: str,
    temperature: float,
    provider: str,
    constraints: str = "",
    existing_analysis: Dict[str, Dict[str, Any]] = None,
    users_to_analyze: List[str] = None,
    state: Dict[str, Any] = None
) -> tuple[Dict[str, Dict[str, Dict[str, Any]]], Dict[str, str]]:
    """
    Run all 5 Big5 trait analyses in parallel.
    
    Args:
        conversation: Formatted conversation string
        model_name: LLM model name
        temperature: Model temperature
        provider: Model provider
        constraints: Constraints string (agent exclusion + target users)
        existing_analysis: Dict mapping display_name -> {trait -> {score, justification}}
        users_to_analyze: List of display names being analyzed
        state: SupervisorState for logging
        
    Returns:
        Tuple of (Dict mapping trait -> username -> {score, confidence, justification, changed?, change_reason?}, Dict mapping trait -> raw_llm_output)
    """
    results = {}
    raw_outputs = {}
    existing_analysis = existing_analysis or {}
    users_to_analyze = users_to_analyze or []
    
    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for trait in BIG5_TRAITS:
            # Build existing analysis string for this specific trait
            existing_analysis_str = build_existing_analysis_string(
                trait, existing_analysis, users_to_analyze
            )
            
            future = executor.submit(
                analyze_single_trait,
                trait,
                conversation,
                model_name,
                temperature,
                provider,
                constraints,
                existing_analysis_str
            )
            futures[trait] = future
        
        # Collect results
        for trait, future in futures.items():
            try:
                parsed_result, raw_output = future.result(timeout=60)
                results[trait] = parsed_result
                raw_outputs[trait] = raw_output
            except Exception as e:
                logger.error(f"Timeout or error for {trait}: {e}")
                results[trait] = {}
                raw_outputs[trait] = f"Error: {e}"
    
    return results, raw_outputs


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
    personality_cache = state.get('personality_analysis', {}) or {}
    
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
    
    # Get agent display names (with "(Agent)" suffix) for constraints
    agent_display_names = get_agent_display_names(include_agent_suffix=True)
    
    # Identify users with NEW (unprocessed) messages
    new_user_ids, new_user_mapping = identify_users_with_new_messages(recent_messages, agent_personas)
    
    logger.info(f"Found {len(username_to_userid)} unique users in recent messages")
    logger.info(f"Users with new messages: {list(new_user_mapping.keys())}")
    
    # Filter out users who are already confident enough
    users_to_analyze = []
    for display_name, user_id in new_user_mapping.items():
        is_confident, existing_analysis = is_user_confident_enough(
            chat_id, user_id, CONFIDENCE_THRESHOLDS
        )
        if STOP_REANALYSIS_WHEN_CONFIDENT and is_confident:
            # Already confident, load existing data to cache
            personality_cache[user_id] = existing_analysis
            logger.debug(f"Skipping {display_name}: already confident enough")
        else:
            users_to_analyze.append(display_name)
    
    # Early exit if no users need analysis
    if not users_to_analyze:
        logger.info("No users require personality analysis (all confident or no new messages).")
        # Still update messages with existing personality data
        updated_messages = []
        for msg in recent_messages:
            sender_id = str(msg.get("sender_id", "")).strip()
            if sender_id and sender_id in personality_cache:
                msg['sender_personality'] = personality_cache[sender_id]
            updated_messages.append(msg)
        
        log_node_output("component_c", {
            "users_analyzed": 0,
            "users_saved": 0,
            "skipped_no_new_messages": len(username_to_userid) - len(new_user_mapping),
            "skipped_confident": len(new_user_mapping) - len(users_to_analyze)
        }, supervisor_state=state)
        
        return {
            'personality_analysis': personality_cache,
            'recent_messages': updated_messages[:MAX_RECENT_MESSAGES]
        }
    
    logger.info(f"Users to analyze: {users_to_analyze}")
    
    # Build constraints string (agent exclusion + target users)
    constraints = build_constraints_string(agent_display_names, users_to_analyze)
    
    # Get existing analysis for users being analyzed (for iterative updates)
    users_to_analyze_mapping = {name: new_user_mapping[name] for name in users_to_analyze if name in new_user_mapping}
    existing_analysis = get_existing_analysis_for_users(chat_id, users_to_analyze_mapping)
    logger.info(f"Users with prior analysis: {list(existing_analysis.keys())}")
    
    # Format conversation for prompt
    conversation = format_conversation_for_prompt(recent_messages)
    
    # Get model settings
    model_settings = get_model_settings('component_C', 'COMPONENT_C_MODEL')
    model_name = model_settings['model']
    temperature = model_settings['temperature']
    provider = model_settings['provider']
    
    # Generate and log prompts for all traits (with constraints and existing analysis)
    prompts = {}
    for trait in BIG5_TRAITS:
        try:
            prompt_template = load_prompt(f"supervisor_graph/component_C/{trait}.txt")
            prompt = prompt_template.replace("{{CONVERSATION}}", conversation)
            prompt = prompt.replace("{{CONSTRAINTS}}", constraints)
            existing_analysis_str = build_existing_analysis_string(trait, existing_analysis, users_to_analyze)
            prompt = prompt.replace("{{EXISTING_ANALYSIS}}", existing_analysis_str)
            prompts[trait] = prompt
        except Exception as e:
            logger.error(f"Failed to generate prompt for {trait}: {e}")
            prompts[trait] = f"Error generating prompt: {e}"
            
    # Log all prompts in one entry
    log_prompt("component_c", prompts, model=model_name, temperature=temperature, supervisor_state=state)
    
    # Run parallel trait analysis
    trait_results, raw_llm_outputs = run_parallel_trait_analysis(
        conversation,
        model_name,
        temperature,
        provider,
        constraints,
        existing_analysis,
        users_to_analyze,
        state
    )
    
    # Merge results by user
    user_results = merge_trait_results_by_user(trait_results)
    
    logger.info(f"Got personality results for {len(user_results)} users")
    
    # Process and save results for users that were analyzed
    saved_count = 0
    skipped_low_messages = 0
    
    for username_lower, big5_data in user_results.items():
        # Find the user_id for this username
        user_id = None
        for name, uid in username_to_userid.items():
            if name.lower() == username_lower:
                user_id = uid
                break
        
        if not user_id:
            # Also check new_user_mapping
            for name, uid in new_user_mapping.items():
                if name.lower() == username_lower:
                    user_id = uid
                    break
        
        if not user_id:
            logger.warning(f"Could not find user_id for {username_lower}")
            continue
        
        # Get cumulative message count from disk (for both MIN check and penalty)
        cumulative_messages = get_participant_messages(chat_id, user_id)
        cumulative_msg_count = len(cumulative_messages)
        
        # Check message count constraints for SAVING new data (use cumulative count)
        if cumulative_msg_count < MIN_MESSAGES_FOR_ANALYSIS:
            logger.debug(f"Skipping {username_lower}: only {cumulative_msg_count} messages (min: {MIN_MESSAGES_FOR_ANALYSIS})")
            skipped_low_messages += 1
            # Load existing data if available
            _, existing_analysis = is_user_confident_enough(chat_id, user_id, CONFIDENCE_THRESHOLDS)
            if existing_analysis:
                personality_cache[user_id] = existing_analysis
            continue
        
        # Ensure all 5 traits have data: preserve previous snapshot for failed traits
        complete_big5 = {}
        participant_data = get_participant_data(chat_id, user_id)
        previous_snapshot = None
        if participant_data:
            snapshots = participant_data.get("personality_snapshots", [])
            if snapshots:
                previous_snapshot = snapshots[0].get("personality_analysis", {}).get("big5", {})
        
        missing_traits = []
        for trait in BIG5_TRAITS:
            if trait in big5_data:
                # New LLM result available
                complete_big5[trait] = big5_data[trait]
            elif previous_snapshot and trait in previous_snapshot:
                # Preserve previous trait data (partial failure recovery)
                complete_big5[trait] = previous_snapshot[trait]
                logger.warning(f"Trait '{trait}' missing for {username_lower}, preserved previous snapshot data")
            else:
                # No current result AND no previous data - skip this trait
                missing_traits.append(trait)
                logger.error(f"Trait '{trait}' missing for {username_lower} and no previous data available")
        
        # If any traits are completely missing, skip this user to avoid incomplete snapshot
        if missing_traits:
            logger.error(f"Skipping {username_lower}: missing traits {missing_traits} with no fallback")
            continue
        
        # Apply confidence penalty based on CUMULATIVE message count (business logic)
        complete_big5 = apply_confidence_penalty(
            big5_results=complete_big5,
            message_count=cumulative_msg_count,
            penalty_config=CONFIDENCE_PENALTY_CONFIG
        )
        
        # Save to memory (file)
        save_result = save_personality_analysis(
            chat_id=chat_id,
            user_id=user_id,
            big5_results=complete_big5,
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
    
    # Load existing personality data for users NOT analyzed in this run
    for username_lower, user_id in username_to_userid.items():
        if user_id not in personality_cache:
            # Skip agents
            if is_agent_sender(display_name=username_lower, agent_personas=agent_personas):
                continue
            # Load from disk
            _, existing_analysis = is_user_confident_enough(chat_id, user_id, CONFIDENCE_THRESHOLDS)
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
    
    # Log summary with raw LLM outputs per trait
    log_node_output("component_c", {
        "users_analyzed": len(user_results),
        "users_saved": saved_count,
        "users_requested": len(users_to_analyze),
        "skipped_low_messages": skipped_low_messages,
        "raw_outputs": {
            "openness": raw_llm_outputs.get("openness", ""),
            "conscientiousness": raw_llm_outputs.get("conscientiousness", ""),
            "extraversion": raw_llm_outputs.get("extraversion", ""),
            "agreeableness": raw_llm_outputs.get("agreeableness", ""),
            "neuroticism": raw_llm_outputs.get("neuroticism", "")
        }
    }, supervisor_state=state)
    
    # Trim recent_messages to configured maximum (keep newest)
    trimmed_messages = updated_messages[:MAX_RECENT_MESSAGES]
    
    return {
        'personality_analysis': personality_cache,
        'recent_messages': trimmed_messages
    }
