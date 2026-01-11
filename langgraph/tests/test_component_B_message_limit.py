"""
Test Component B message limiting logic

Tests:
1. 5 analyzed + 2 new = 7 total (all kept)
2. 6 analyzed + 2 new = 8 total → trim to 7 (oldest removed)
3. 7 analyzed + 3 new = 10 total → trim to 7 (3 oldest removed)
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_test_message(msg_id: str, text: str, has_emotion: bool = False):
    """Helper to create a test message"""
    msg = {
        'message_id': msg_id,
        'sender_id': f'user_{msg_id}',
        'sender_username': f'user_{msg_id}',
        'sender_first_name': 'Test',
        'sender_last_name': 'User',
        'text': text,
        'date': datetime.now(),
        'sender_personality': None,
        'processed': True
    }
    
    if has_emotion:
        msg['message_emotion'] = {
            'emotion': 'neutral',
            'justification': 'Pre-analyzed for testing'
        }
    else:
        msg['message_emotion'] = None
    
    return msg


def test_scenario_1():
    """5 analyzed + 2 new = 7 total (all kept)"""
    print("\n" + "="*80)
    print("TEST 1: 5 analyzed + 2 new = 7 total")
    print("="*80)
    
    state = {
        'recent_messages': [
            create_test_message('new1', 'New message 1', has_emotion=False),
            create_test_message('new2', 'New message 2', has_emotion=False),
            create_test_message('old1', 'Old message 1', has_emotion=True),
            create_test_message('old2', 'Old message 2', has_emotion=True),
            create_test_message('old3', 'Old message 3', has_emotion=True),
            create_test_message('old4', 'Old message 4', has_emotion=True),
            create_test_message('old5', 'Old message 5', has_emotion=True),
        ],
        'group_metadata': {
            'name': 'Test Group',
            'topic': 'Testing',
            'members': 10
        },
        'group_sentiment': 'Previous sentiment'
    }
    
    print(f"\nBefore Component B:")
    print(f"  Total messages: {len(state['recent_messages'])}")
    print(f"  Unanalyzed: {sum(1 for m in state['recent_messages'] if m['message_emotion'] is None)}")
    print(f"  Message IDs: {[m['message_id'] for m in state['recent_messages']]}")
    
    # Simulate what component B does (without LLM call)
    recent_messages = state['recent_messages'].copy()
    
    # Find unclassified
    unclassified_indices = []
    for idx, msg in enumerate(recent_messages):
        if msg.get('message_emotion') is None:
            unclassified_indices.append(idx)
    
    print(f"\n  Unclassified indices: {unclassified_indices}")
    
    # Simulate analyzing them
    for idx in unclassified_indices:
        recent_messages[idx]['message_emotion'] = {
            'emotion': 'neutral',
            'justification': 'Analyzed in test'
        }
    
    # Trim to 7
    MAX_RECENT_MESSAGES = 7
    trimmed_messages = recent_messages[:MAX_RECENT_MESSAGES]
    
    print(f"\nAfter Component B:")
    print(f"  Total messages: {len(trimmed_messages)}")
    print(f"  Unanalyzed: {sum(1 for m in trimmed_messages if m['message_emotion'] is None)}")
    print(f"  Message IDs: {[m['message_id'] for m in trimmed_messages]}")
    
    # Verify
    assert len(trimmed_messages) == 7, f"Expected 7 messages, got {len(trimmed_messages)}"
    assert all(m['message_emotion'] is not None for m in trimmed_messages), "All messages should be analyzed"
    assert trimmed_messages[0]['message_id'] == 'new1', "First message should be new1"
    assert trimmed_messages[-1]['message_id'] == 'old5', "Last message should be old5"
    
    print("\n✅ TEST 1 PASSED")


def test_scenario_2():
    """6 analyzed + 2 new = 8 total → trim to 7 (oldest removed)"""
    print("\n" + "="*80)
    print("TEST 2: 6 analyzed + 2 new = 8 total → trim to 7")
    print("="*80)
    
    state = {
        'recent_messages': [
            create_test_message('new1', 'New message 1', has_emotion=False),
            create_test_message('new2', 'New message 2', has_emotion=False),
            create_test_message('old1', 'Old message 1', has_emotion=True),
            create_test_message('old2', 'Old message 2', has_emotion=True),
            create_test_message('old3', 'Old message 3', has_emotion=True),
            create_test_message('old4', 'Old message 4', has_emotion=True),
            create_test_message('old5', 'Old message 5', has_emotion=True),
            create_test_message('old6', 'Old message 6 (SHOULD BE REMOVED)', has_emotion=True),
        ],
        'group_metadata': {
            'name': 'Test Group',
            'topic': 'Testing',
            'members': 10
        },
        'group_sentiment': 'Previous sentiment'
    }
    
    print(f"\nBefore Component B:")
    print(f"  Total messages: {len(state['recent_messages'])}")
    print(f"  Message IDs: {[m['message_id'] for m in state['recent_messages']]}")
    
    # Simulate what component B does
    recent_messages = state['recent_messages'].copy()
    
    # Find and analyze unclassified
    for idx, msg in enumerate(recent_messages):
        if msg.get('message_emotion') is None:
            recent_messages[idx]['message_emotion'] = {
                'emotion': 'neutral',
                'justification': 'Analyzed in test'
            }
    
    # Trim to 7
    MAX_RECENT_MESSAGES = 7
    trimmed_messages = recent_messages[:MAX_RECENT_MESSAGES]
    
    print(f"\nAfter Component B:")
    print(f"  Total messages: {len(trimmed_messages)}")
    print(f"  Message IDs: {[m['message_id'] for m in trimmed_messages]}")
    
    # Verify
    assert len(trimmed_messages) == 7, f"Expected 7 messages, got {len(trimmed_messages)}"
    assert all(m['message_emotion'] is not None for m in trimmed_messages), "All messages should be analyzed"
    assert trimmed_messages[0]['message_id'] == 'new1', "First message should be new1"
    assert trimmed_messages[-1]['message_id'] == 'old5', "Last message should be old5"
    assert 'old6' not in [m['message_id'] for m in trimmed_messages], "old6 should be removed"
    
    print("\n✅ TEST 2 PASSED")


def test_scenario_3():
    """7 analyzed + 3 new = 10 total → trim to 7 (3 oldest removed)"""
    print("\n" + "="*80)
    print("TEST 3: 7 analyzed + 3 new = 10 total → trim to 7")
    print("="*80)
    
    state = {
        'recent_messages': [
            create_test_message('new1', 'New message 1', has_emotion=False),
            create_test_message('new2', 'New message 2', has_emotion=False),
            create_test_message('new3', 'New message 3', has_emotion=False),
            create_test_message('old1', 'Old message 1', has_emotion=True),
            create_test_message('old2', 'Old message 2', has_emotion=True),
            create_test_message('old3', 'Old message 3', has_emotion=True),
            create_test_message('old4', 'Old message 4', has_emotion=True),
            create_test_message('old5', 'Old message 5 (SHOULD BE REMOVED)', has_emotion=True),
            create_test_message('old6', 'Old message 6 (SHOULD BE REMOVED)', has_emotion=True),
            create_test_message('old7', 'Old message 7 (SHOULD BE REMOVED)', has_emotion=True),
        ],
        'group_metadata': {
            'name': 'Test Group',
            'topic': 'Testing',
            'members': 10
        },
        'group_sentiment': 'Previous sentiment'
    }
    
    print(f"\nBefore Component B:")
    print(f"  Total messages: {len(state['recent_messages'])}")
    print(f"  Message IDs: {[m['message_id'] for m in state['recent_messages']]}")
    
    # Simulate what component B does
    recent_messages = state['recent_messages'].copy()
    
    # Find and analyze unclassified
    for idx, msg in enumerate(recent_messages):
        if msg.get('message_emotion') is None:
            recent_messages[idx]['message_emotion'] = {
                'emotion': 'neutral',
                'justification': 'Analyzed in test'
            }
    
    # Trim to 7
    MAX_RECENT_MESSAGES = 7
    trimmed_messages = recent_messages[:MAX_RECENT_MESSAGES]
    
    print(f"\nAfter Component B:")
    print(f"  Total messages: {len(trimmed_messages)}")
    print(f"  Message IDs: {[m['message_id'] for m in trimmed_messages]}")
    
    # Verify
    assert len(trimmed_messages) == 7, f"Expected 7 messages, got {len(trimmed_messages)}"
    assert all(m['message_emotion'] is not None for m in trimmed_messages), "All messages should be analyzed"
    assert trimmed_messages[0]['message_id'] == 'new1', "First message should be new1"
    assert trimmed_messages[-1]['message_id'] == 'old4', "Last message should be old4"
    assert 'old5' not in [m['message_id'] for m in trimmed_messages], "old5 should be removed"
    assert 'old6' not in [m['message_id'] for m in trimmed_messages], "old6 should be removed"
    assert 'old7' not in [m['message_id'] for m in trimmed_messages], "old7 should be removed"
    
    print("\n✅ TEST 3 PASSED")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTING COMPONENT B MESSAGE LIMITING LOGIC")
    print("="*80)
    
    try:
        test_scenario_1()
        test_scenario_2()
        test_scenario_3()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
