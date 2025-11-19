"""
Test Component E.2 - Styler Node
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from nodes.agent.component_E2 import styler_node
from states.agent_state import AgentState
import logging

logging.basicConfig(level=logging.INFO)


def test_styler():
    """Test the styler node with a sample response."""
    
    # Sample persona - young casual persona
    persona = {
        "agent_type": "troll",
        "persona_id": "troll_18_25_casual",
        "age_group": "18-25",
        "communication_style": "casual_modern",
        "traits": [
            "uses lots of emojis",
            "types in lowercase",
            "uses internet slang",
            "humorous and playful",
            "brief messages"
        ],
        "vocabulary_level": "informal",
        "typical_topics": ["memes", "gaming", "trends"]
    }
    
    # Agent prompt defining identity
    agent_prompt = """You are a young, playful troll agent in a Telegram group.
Your role is to add humor and light-hearted chaos.
You communicate casually with emojis and modern slang.
Stay true to your persona in all interactions."""
    
    # Generated response from E.1 (formal/neutral)
    generated_response = "I appreciate your suggestion about the new restaurant. I have been considering trying it. Would you like to join me this weekend? I think it would be enjoyable."
    
    # Create test state
    state: AgentState = {
        "recent_messages": [],
        "group_sentiment": "",
        "group_metadata": {},
        "selected_persona": persona,
        "agent_type": "troll",
        "agent_goal": "add humor and entertainment",
        "triggers": [],
        "actions": [],
        "detected_trigger": None,
        "selected_action": {
            "id": "engage_casual",
            "purpose": "Join conversation casually"
        },
        "agent_prompt": agent_prompt,
        "generated_response": generated_response,
        "styled_response": None,
        "validation": None,
        "current_node": "styler",
        "next_node": "validator"
    }
    
    print("=" * 50)
    print("TEST: COMPONENT E.2 - STYLER")
    print("=" * 50)
    
    print("\n--- Generated Response (E.1 output) ---")
    print(generated_response)
    
    print("\n--- Persona Traits ---")
    for trait in persona.get('traits', []):
        print(f"  - {trait}")
    
    print("\n--- Running Styler... ---")
    styler_node(state)
    
    print("\n--- Styled Response (E.2 output) ---")
    styled_response = state.get('styled_response')
    if styled_response:
        print(styled_response)
        
        print("\n--- Style Analysis ---")
        # Check for style changes
        if any(emoji in styled_response for emoji in ['😂', '🔥', '👀', '💯', '🤔', '😎', '🎮', '🍕']):
            print("✓ Contains emojis")
        if styled_response.islower() or not styled_response[0].isupper():
            print("✓ Uses lowercase style")
        if any(slang in styled_response.lower() for slang in ['lol', 'tbh', 'ngl', 'fr', 'bet', 'vibes', 'lowkey']):
            print("✓ Uses internet slang")
        
        print("\n--- Content Preservation Check ---")
        key_concepts = ["restaurant", "join", "weekend"]
        preserved = sum(1 for concept in key_concepts if concept.lower() in styled_response.lower())
        print(f"Key concepts preserved: {preserved}/{len(key_concepts)}")
        
    else:
        print("ERROR: No styled response generated")
    
    print("\n" + "=" * 50)


def test_styler_formal_persona():
    """Test styler with formal persona."""
    
    # Sample persona - older formal persona
    persona = {
        "agent_type": "active",
        "persona_id": "active_50_65_formal",
        "age_group": "50-65",
        "communication_style": "formal_professional",
        "traits": [
            "proper grammar and punctuation",
            "thoughtful and measured",
            "uses complete sentences",
            "avoids slang",
            "respectful tone"
        ],
        "vocabulary_level": "sophisticated",
        "typical_topics": ["business", "culture", "current events"]
    }
    
    agent_prompt = """You are a thoughtful, mature active member in a Telegram group.
You contribute meaningful insights and maintain a respectful, professional tone.
Your communication reflects wisdom and life experience."""
    
    # Generated response (casual/neutral)
    generated_response = "hey that's a cool idea! yeah we should totally do that sometime, sounds fun"
    
    # Create test state
    state: AgentState = {
        "recent_messages": [],
        "group_sentiment": "",
        "group_metadata": {},
        "selected_persona": persona,
        "agent_type": "active",
        "agent_goal": "contribute meaningfully",
        "triggers": [],
        "actions": [],
        "detected_trigger": None,
        "selected_action": {
            "id": "support_idea",
            "purpose": "Express support for group idea"
        },
        "agent_prompt": agent_prompt,
        "generated_response": generated_response,
        "styled_response": None,
        "validation": None,
        "current_node": "styler",
        "next_node": "validator"
    }
    
    print("\n\n" + "=" * 50)
    print("TEST: FORMAL PERSONA STYLING")
    print("=" * 50)
    
    print("\n--- Generated Response (casual) ---")
    print(generated_response)
    
    print("\n--- Persona Traits ---")
    for trait in persona.get('traits', []):
        print(f"  - {trait}")
    
    print("\n--- Running Styler... ---")
    styler_node(state)
    
    print("\n--- Styled Response (formal) ---")
    styled_response = state.get('styled_response')
    if styled_response:
        print(styled_response)
        
        print("\n--- Style Analysis ---")
        # Check for formal characteristics
        if styled_response[0].isupper():
            print("✓ Proper capitalization")
        if '.' in styled_response:
            print("✓ Uses proper punctuation")
        if not any(slang in styled_response.lower() for slang in ['hey', 'yeah', 'cool', 'totally']):
            print("✓ Avoids casual slang")
        
        print("\n--- Content Preservation Check ---")
        if "idea" in styled_response.lower():
            print("✓ Core meaning preserved (idea)")
        if any(word in styled_response.lower() for word in ["support", "agree", "favor", "like"]):
            print("✓ Sentiment preserved (positive support)")
        
    else:
        print("ERROR: No styled response generated")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    # Run both test cases
    test_styler()
    test_styler_formal_persona()
