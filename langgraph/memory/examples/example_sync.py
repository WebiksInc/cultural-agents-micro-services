"""
Example: Sync group messages from Telegram API.

This unified function handles both:
- Initial fetch (when no messages exist)
- Incremental sync (when messages exist)

Always fetches maximum messages (1000 - API limit) to capture all unsaved messages.
The function automatically detects which mode is needed and deduplicates.
"""
from .. import sync_group_messages

# Configuration
PHONE = "+37379276083"
CHAT_ID = "3389864729"

# Sync messages (auto-detects initial vs incremental, always fetches max)
result = sync_group_messages(
    phone=PHONE,
    chat_id=CHAT_ID,
    verbose=True
)

if result['success']:
    mode = "INITIAL FETCH" if result['is_initial_fetch'] else "INCREMENTAL SYNC"
    print(f"\n✅ SUCCESS - {mode}")
    print(f"   Group: {result['chat_title']}")
    print(f"   Total fetched: {result['total_fetched']}")
    print(f"   New messages saved: {result['new_messages']}")
    print(f"   Data location: data/{CHAT_ID}/")
else:
    print(f"\n❌ FAILED: {result.get('error')}")

