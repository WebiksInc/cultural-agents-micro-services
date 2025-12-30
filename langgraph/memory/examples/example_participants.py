"""
Example: Participant management with 3-step workflow.

This example shows how to:
1. Get participant messages (without saving)
2. Initialize participant JSON files
3. Save personality analysis (cumulative snapshots)
"""
from .. import (
    get_participant_messages,
    initialize_participants,
    save_personality_analysis,
    list_participants,
    get_participant_data
)

# Configuration
CHAT_ID = "3389864729"

if __name__ == "__main__":
    print("\n" + "="*70)
    print("PARTICIPANT MANAGEMENT EXAMPLE")
    print("="*70)
    
    # Step 1: Initialize participants (creates JSON files if don't exist)
    print("\n[STEP 1] Initialize participants...")
    result = initialize_participants(
        chat_id=CHAT_ID,
        verbose=True
    )
    
    if not result["success"]:
        print(f"\n❌ FAILED: {result.get('error')}\n")
        exit(1)
    
    # Step 2: List participants
    print(f"\n{'='*70}")
    print("[STEP 2] List all participants")
    print("-" * 70)
    participants = list_participants(CHAT_ID)
    for p in participants:
        print(f"  {p['username']:<20} (ID: {p['user_id']})")
        print(f"    Messages: {p['message_count']}, Snapshots: {p['snapshots_count']}")
    
    # Step 3: Get messages for specific participant (without saving)
    if participants:
        print(f"\n{'='*70}")
        print("[STEP 3] Get messages for specific participant")
        print("-" * 70)
        sample_user = participants[0]
        user_id = sample_user['user_id']
        
        messages = get_participant_messages(CHAT_ID, user_id)
        print(f"User: {sample_user['username']}")
        print(f"Total messages: {len(messages)}")
        print(f"\nFirst 3 messages:")
        for msg in messages[:3]:
            print(f"  [{msg['date']}] {msg['text'][:60]}...")
    
    # Step 4: Save personality analysis (adds new snapshot)
    if participants:
        print(f"\n{'='*70}")
        print("[STEP 4] Save personality analysis")
        print("-" * 70)
        
        # Save for first participant
        user_id = participants[0]['user_id']
        result = save_personality_analysis(
            chat_id=CHAT_ID,
            user_id=user_id,
            # big5_values=None  # Random values
            verbose=True
        )
        
        # Save again to show cumulative behavior
        print("\nSaving second analysis for same user...")
        result2 = save_personality_analysis(
            chat_id=CHAT_ID,
            user_id=user_id,
            verbose=True
        )
        
        # Show cumulative snapshots
        print(f"\n{'='*70}")
        print("CUMULATIVE SNAPSHOTS (previous analyses preserved)")
        print("-" * 70)
        data = get_participant_data(CHAT_ID, user_id)
        for i, snapshot in enumerate(data['personality_snapshots'], 1):
            print(f"\nSnapshot {i}:")
            print(f"  Date: {snapshot['analysis_date']}")
            print(f"  Confidence: {snapshot['confidence']}")
            print(f"  Big5: {snapshot['personality_analysis']['big5']}")
    
    print(f"\n{'='*70}\n")
