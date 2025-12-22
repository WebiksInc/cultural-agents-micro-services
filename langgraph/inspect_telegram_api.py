"""
Test script to see what data Telegram API returns.
Run this to understand the API response structure.
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram_exm_yair import get_all_chats, get_chat_messages

# Configuration
PHONE = "+37379276083"
CHAT_ID = "3389864729"

print("="*70)
print("STEP 1: Fetching all chats to see group metadata")
print("="*70)

chats_response = get_all_chats()
print("\nFull response structure:")
print(json.dumps(chats_response, indent=2, ensure_ascii=False))

# Find our specific chat
if chats_response.get('success') and chats_response.get('chats'):
    for chat in chats_response['chats']:
        if str(chat.get('id')) == CHAT_ID:
            print(f"\n{'='*70}")
            print(f"Found chat {CHAT_ID}:")
            print("="*70)
            print(json.dumps(chat, indent=2, ensure_ascii=False))
            break

print("\n" + "="*70)
print("STEP 2: Fetching messages to see message structure")
print("="*70)

messages_response = get_chat_messages(phone=PHONE, chat_id=CHAT_ID, limit=3)
print("\nFull response structure:")
print(json.dumps(messages_response, indent=2, ensure_ascii=False))

if messages_response.get('success') and messages_response.get('data', {}).get('messages'):
    print(f"\n{'='*70}")
    print("Sample message structure:")
    print("="*70)
    print(json.dumps(messages_response['data']['messages'][0], indent=2, ensure_ascii=False))

print("\n" + "="*70)
print("What fields are available?")
print("="*70)
if messages_response.get('success') and messages_response.get('data', {}).get('messages'):
    msg = messages_response['data']['messages'][0]
    print("\nMessage fields:", list(msg.keys()))
