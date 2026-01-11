"""
Test file for Component C - Personality Analysis Node (Big Five / OCEAN Model)

This test demonstrates how Component C works with sample data.
Tests both helper functions and the main node logic.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from unittest.mock import patch

# Add parent directory to Python path so we can import from nodes
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from nodes.supervisor.component_C import (
    personality_analysis_node,
    build_username_userid_mapping,
    count_user_messages,
    format_conversation_for_prompt,
    is_user_confident_enough,
    merge_trait_results_by_user,
    run_parallel_trait_analysis,
    BIG5_TRAITS
)
from utils import get_model_settings, is_agent_sender, load_agent_personas

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# TEST DATA
# ============================================================================

# Sample messages mimicking real conversation
test_messages = [
    {
        'message_id': 'msg_001',
        'sender_id': '12345',
        'sender_username': 'alice_curious',
        'sender_first_name': 'Alice',
        'sender_last_name': 'Wonder',
        'text': 'Has anyone read about quantum computing? I find it absolutely fascinating how qubits can exist in superposition!',
        'date': datetime(2025, 12, 29, 10, 0, 0),
        'message_emotion': {'emotion': 'excited', 'justification': 'Shows enthusiasm'}
    },
    {
        'message_id': 'msg_002',
        'sender_id': '67890',
        'sender_username': 'bob_practical',
        'sender_first_name': 'Bob',
        'sender_last_name': 'Builder',
        'text': 'Sounds like hype to me. I prefer sticking with proven technologies that actually work in production.',
        'date': datetime(2025, 12, 29, 10, 5, 0),
        'message_emotion': {'emotion': 'skeptical', 'justification': 'Dismissive tone'}
    },
    {
        'message_id': 'msg_003',
        'sender_id': '12345',
        'sender_username': 'alice_curious',
        'sender_first_name': 'Alice',
        'sender_last_name': 'Wonder',
        'text': 'But Bob, imagine the possibilities! I started learning watercolor painting last month too - creativity opens so many doors.',
        'date': datetime(2025, 12, 29, 10, 10, 0),
        'message_emotion': {'emotion': 'enthusiastic', 'justification': 'Excited about learning'}
    },
    {
        'message_id': 'msg_004',
        'sender_id': '11111',
        'sender_username': 'charlie_quiet',
        'sender_first_name': 'Charlie',
        'sender_last_name': 'Silent',
        'text': 'Nice.',
        'date': datetime(2025, 12, 29, 10, 15, 0),
        'message_emotion': {'emotion': 'neutral', 'justification': 'Brief response'}
    },
    {
        'message_id': 'msg_005',
        'sender_id': '67890',
        'sender_username': 'bob_practical',
        'sender_first_name': 'Bob',
        'sender_last_name': 'Builder',
        'text': 'Why waste time on painting when you could learn something useful like Excel or database management?',
        'date': datetime(2025, 12, 29, 10, 20, 0),
        'message_emotion': {'emotion': 'dismissive', 'justification': 'Devalues creative pursuits'}
    },
    {
        'message_id': 'msg_006',
        'sender_id': '22222',
        'sender_username': 'SandraK9',  # This is an agent username from config!
        'sender_first_name': 'Sandra',
        'sender_last_name': 'K',
        'text': 'I think both perspectives have merit. Technology and art can complement each other beautifully.',
        'date': datetime(2025, 12, 29, 10, 25, 0),
        'message_emotion': {'emotion': 'balanced', 'justification': 'Diplomatic response'}
    },
]

# Full test state
test_state = {
    'group_metadata': {
        'name': 'Tech & Creative Minds',
        'id': '3389864729',
        'members': 25,
        'topic': 'Technology, Art, and Innovation'
    },
    'recent_messages': test_messages,
    'group_sentiment': 'Mixed discussion with contrasting viewpoints on innovation vs practicality.',
    'selected_actions': [],
    'execution_queue': [],
    'agents_recent_actions': {},
    'personality_analysis': {},  # Empty cache initially
    'current_nodes': None,
    'next_nodes': None
}


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

def test_is_agent_sender():
    """Test agent detection with name matching."""
    print("\n" + "=" * 60)
    print("TEST: is_agent_sender()")
    print("=" * 60)
    
    agent_personas = load_agent_personas()
    print(f"Loaded {len(agent_personas)} agent personas")
    
    # Test cases
    test_cases = [
        ("sandra", True, "Exact name match"),
        ("Sandra K", True, "First name matches 'sandra'"),
        ("Victor Bastillo", True, "First name matches 'victor'"),
        ("Alice Wonder", False, "Not an agent"),
        ("Bob Builder", False, "Not an agent"),
    ]
    
    all_passed = True
    for display_name, expected, reason in test_cases:
        result = is_agent_sender(display_name=display_name, agent_personas=agent_personas)
        status = "✅" if result == expected else "❌"
        print(f"  {status} is_agent_sender('{display_name}'): {result} (expected {expected}) - {reason}")
        if result != expected:
            all_passed = False
    
    if all_passed:
        print("✅ PASSED: Agent detection works correctly")
    else:
        print("❌ FAILED: Some agent detection cases failed")
    
    return all_passed
    
    return all_passed


def test_build_username_userid_mapping():
    """Test display name to user_id mapping from messages."""
    print("\n" + "=" * 60)
    print("TEST: build_username_userid_mapping()")
    print("=" * 60)
    
    mapping = build_username_userid_mapping(test_messages)
    print(f"Display Name -> User ID mapping:")
    for name, user_id in sorted(mapping.items()):
        print(f"  {name} -> {user_id}")
    
    # Check full name mapping (what LLM returns now)
    assert mapping.get('alice wonder') == '12345', "Alice full name mapping incorrect"
    assert mapping.get('bob builder') == '67890', "Bob full name mapping incorrect"
    assert mapping.get('charlie silent') == '11111', "Charlie full name mapping incorrect"
    assert mapping.get('sandra k') == '22222', "Sandra full name mapping incorrect"
    
    print("✅ PASSED: Display name to user_id mapping works correctly")
    return True


def test_count_user_messages():
    """Test message counting per user by display name."""
    print("\n" + "=" * 60)
    print("TEST: count_user_messages()")
    print("=" * 60)
    
    counts = count_user_messages(test_messages)
    print(f"Message counts per user:")
    for name, count in sorted(counts.items()):
        print(f"  {name}: {count} messages")
    
    assert counts.get('alice wonder') == 2, "Alice should have 2 messages"
    assert counts.get('bob builder') == 2, "Bob should have 2 messages"
    assert counts.get('charlie silent') == 1, "Charlie should have 1 message"
    assert counts.get('sandra k') == 1, "Sandra (agent) should have 1 message"
    
    print("✅ PASSED: Message counting works correctly")
    return True


def test_format_conversation_for_prompt():
    """Test conversation formatting for prompts."""
    print("\n" + "=" * 60)
    print("TEST: format_conversation_for_prompt()")
    print("=" * 60)
    
    formatted = format_conversation_for_prompt(test_messages)
    print("Formatted conversation (first 500 chars):")
    print("-" * 40)
    print(formatted[:500])
    print("-" * 40)
    
    # Should contain usernames and text
    assert 'Alice' in formatted or 'alice' in formatted.lower(), "Should contain Alice"
    assert 'quantum' in formatted.lower(), "Should contain 'quantum'"
    
    print("✅ PASSED: Conversation formatting works correctly")
    return True


def test_merge_trait_results_by_user():
    """Test reorganizing trait results from trait->user to user->trait format."""
    print("\n" + "=" * 60)
    print("TEST: merge_trait_results_by_user()")
    print("=" * 60)
    
    # Simulate LLM output (trait -> username -> data)
    mock_trait_results = {
        'openness': {
            'Alice': {'score': 5, 'confidence': 0.85, 'justification': 'Shows curiosity'},
            'Bob': {'score': 2, 'confidence': 0.78, 'justification': 'Prefers practical'}
        },
        'conscientiousness': {
            'Alice': {'score': 3, 'confidence': 0.6, 'justification': 'Moderate'},
            'Bob': {'score': 4, 'confidence': 0.7, 'justification': 'Organized'}
        }
    }
    
    user_results = merge_trait_results_by_user(mock_trait_results)
    print(f"Merged results (user -> trait):")
    for user, traits in user_results.items():
        print(f"  {user}:")
        for trait, data in traits.items():
            print(f"    {trait}: score={data['score']}, confidence={data['confidence']}")
    
    # Check structure is correct
    assert 'alice' in user_results, "Should have alice (lowercase)"
    assert 'bob' in user_results, "Should have bob (lowercase)"
    assert 'openness' in user_results['alice'], "Alice should have openness trait"
    assert user_results['alice']['openness']['score'] == 5, "Alice openness should be 5"
    
    print("✅ PASSED: Trait result merging works correctly")
    return True


# ============================================================================
# MAIN NODE TEST (with real LLM calls)
# ============================================================================

def test_llm_trait_analysis():
    """Test the LLM trait analysis directly (without memory system)."""
    print("\n" + "=" * 60)
    print("TEST: LLM Trait Analysis (Raw Results)")
    print("=" * 60)
    
    # Format conversation
    conversation = format_conversation_for_prompt(test_messages)
    print("\nConversation sent to LLM:")
    print("-" * 40)
    print(conversation)
    print("-" * 40)
    
    # Get model settings
    model_settings = get_model_settings('component_C', 'COMPONENT_C_MODEL')
    print(f"\nUsing model: {model_settings['model']}")
    print(f"Temperature: {model_settings['temperature']}")
    
    print("\n" + "-" * 60)
    print("Running 5 parallel trait analyses...")
    print("-" * 60)
    
    # Run parallel trait analysis
    trait_results = run_parallel_trait_analysis(
        conversation,
        model_settings['model'],
        model_settings['temperature'],
        model_settings['provider']
    )
    
    print("\n" + "=" * 60)
    print("RAW LLM RESULTS (per trait)")
    print("=" * 60)
    
    for trait in BIG5_TRAITS:
        print(f"\n📊 {trait.upper()}")
        results = trait_results.get(trait, {})
        if not results:
            print("   (no results)")
        else:
            for username, data in results.items():
                score = data.get('score', 'N/A')
                conf = data.get('confidence', 'N/A')
                just = data.get('justification', 'N/A')
                print(f"   {username}: score={score}, confidence={conf}")
                print(f"      └─ {just}")
    
    # Merge by user
    user_results = merge_trait_results_by_user(trait_results)
    
    print("\n" + "=" * 60)
    print("MERGED RESULTS (per user)")
    print("=" * 60)
    
    agent_personas = load_agent_personas()
    
    for username, traits in user_results.items():
        is_agent = is_agent_sender(display_name=username, agent_personas=agent_personas)
        agent_tag = " 🤖 (AGENT - would be skipped)" if is_agent else ""
        print(f"\n👤 {username}{agent_tag}")
        for trait, data in traits.items():
            score = data.get('score', 'N/A')
            conf = data.get('confidence', 'N/A')
            print(f"   {trait}: {score}/5 (confidence: {conf})")
    
    print("\n✅ LLM analysis completed successfully")
    return True


def test_personality_analysis_node():
    """Test the main personality analysis node with real LLM calls."""
    print("\n" + "=" * 60)
    print("TEST: personality_analysis_node() - FULL NODE TEST")
    print("=" * 60)
    
    print("\nInitial State:")
    print(f"  Group: {test_state['group_metadata']['name']}")
    print(f"  Messages: {len(test_state['recent_messages'])}")
    print(f"  Personality cache: {test_state.get('personality_analysis', {})}")
    
    print("\nUsers in conversation:")
    for msg in test_state['recent_messages']:
        print(f"  - {msg['sender_username']} (ID: {msg['sender_id']}): {msg['text'][:50]}...")
    
    print("\n" + "-" * 60)
    print("Running personality_analysis_node()...")
    print("(This will make 5 parallel API calls - one per Big Five trait)")
    print("-" * 60)
    
    try:
        # Mock save_personality_analysis to always succeed so we can verify message updates
        with patch('nodes.supervisor.component_C.save_personality_analysis') as mock_save:
            # Return a dummy success response
            mock_save.return_value = {
                "success": True,
                "trait_results": {
                    "openness": {"score": 3, "confidence": 0.5, "justification": "Mocked"},
                    "conscientiousness": {"score": 3, "confidence": 0.5, "justification": "Mocked"},
                    "extraversion": {"score": 3, "confidence": 0.5, "justification": "Mocked"},
                    "agreeableness": {"score": 3, "confidence": 0.5, "justification": "Mocked"},
                    "neuroticism": {"score": 3, "confidence": 0.5, "justification": "Mocked"}
                },
                "overall_confidence": 0.5
            }
            
            result = personality_analysis_node(test_state)
        
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        
        personality_cache = result.get('personality_analysis', {})
        
        if not personality_cache:
            print("⚠️  No personality analysis results returned")
            print("   (This might be expected if participants aren't initialized in memory)")
        else:
            print(f"\nPersonality analysis for {len(personality_cache)} users:")
            for user_id, traits in personality_cache.items():
                print(f"\n  User ID: {user_id}")
                for trait_name, trait_data in traits.items():
                    if isinstance(trait_data, dict):
                        score = trait_data.get('score', 'N/A')
                        conf = trait_data.get('confidence', 'N/A')
                        just = trait_data.get('justification', 'N/A')[:60]
                        print(f"    {trait_name}: score={score}, confidence={conf}")
                        print(f"      Justification: {just}...")
            
            # Check if recent_messages were updated
            updated_messages = result.get('recent_messages', [])
            print(f"\nChecking updated messages ({len(updated_messages)}):")
            updated_count = 0
            for msg in updated_messages:
                if msg.get('sender_personality'):
                    updated_count += 1
                    print(f"  ✅ Message {msg['message_id']} from {msg['sender_username']} has personality data")
            
            if updated_count > 0:
                print(f"  ✅ Successfully updated {updated_count} messages with personality data")
            else:
                print("  ⚠️  No messages were updated with personality data")

        print("\n✅ Node executed successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("COMPONENT C - PERSONALITY ANALYSIS (BIG FIVE) TEST SUITE")
    print("=" * 70)
    
    results = {}
    
    # Run helper function tests first (no LLM calls)
    print("\n" + "#" * 70)
    print("# PART 1: HELPER FUNCTION TESTS (No LLM calls)")
    print("#" * 70)
    
    results['is_agent_sender'] = test_is_agent_sender()
    results['build_username_userid_mapping'] = test_build_username_userid_mapping()
    results['count_user_messages'] = test_count_user_messages()
    results['format_conversation_for_prompt'] = test_format_conversation_for_prompt()
    results['merge_trait_results_by_user'] = test_merge_trait_results_by_user()
    
    # Ask before running LLM tests
    print("\n" + "#" * 70)
    print("# PART 2: FULL NODE TEST (Makes LLM API calls)")
    print("#" * 70)
    
    run_llm_test = input("\nRun LLM tests? (y/n): ").strip().lower()
    
    if run_llm_test == 'y':
        results['llm_trait_analysis'] = test_llm_trait_analysis()
        
        run_full_node = input("\nAlso run full node test (requires memory system)? (y/n): ").strip().lower()
        if run_full_node == 'y':
            results['personality_analysis_node'] = test_personality_analysis_node()
        else:
            results['personality_analysis_node'] = None
    else:
        print("Skipping LLM tests.")
        results['llm_trait_analysis'] = None
        results['personality_analysis_node'] = None
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results.items():
        if passed is True:
            status = "✅ PASSED"
        elif passed is False:
            status = "❌ FAILED"
        else:
            status = "⏭️  SKIPPED"
        print(f"  {test_name}: {status}")
    
    passed_count = sum(1 for v in results.values() if v is True)
    failed_count = sum(1 for v in results.values() if v is False)
    skipped_count = sum(1 for v in results.values() if v is None)
    
    print(f"\nTotal: {passed_count} passed, {failed_count} failed, {skipped_count} skipped")
    print("=" * 70)


if __name__ == "__main__":
    main()
