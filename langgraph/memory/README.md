# Memory System

Long-term storage for Telegram group data without a database. All data is fetched from the Telegram API and stored in JSON files.

## Table of Contents
- [Installation](#installation)
- [Data Structure](#data-structure)
- [Group Functions](#group-functions)
- [Participant Functions](#participant-functions)
- [Action Functions](#action-functions)
- [Complete Workflow Example](#complete-workflow-example)

---

## Installation

```python
from memory import (
    # Group functions
    sync_group_messages,
    get_group_messages,
    get_group_metadata,
    
    # Participant functions
    get_participant_messages,
    initialize_participants,
    save_personality_analysis,
    list_participants,
    get_participant_data,
    
    # Action functions
    save_action,
    get_agent_actions,
    get_all_actions,
    get_actions_by_trigger,
    list_agents,
    get_action_statistics
)
```

---

## Data Structure

```
data/
│
├── [telegram_group_id]/              
│   │
│   ├── group_metadata.json           # Group info (name, last_sync, last_message_id)
│   │
│   ├── group_history.json            # Full chat history (all messages)
│   │
│   ├── actions/                      # Agent action logs
│   │   ├── [agent_name_1].json       # Actions by agent 1
│   │   ├── [agent_name_2].json       # Actions by agent 2
│   │   └── ...
│   │
│   └── participant/                  # Individual participant data
│       ├── [user_id_1].json          # User analysis (username, personality_snapshots)
│       ├── [user_id_2].json
│       └── ...
```

---

## Group Functions

### 1. `sync_group_messages(phone, chat_id, verbose=True)`

**Purpose:** Sync messages from Telegram API. Handles both initial fetch and incremental updates automatically.

**Behavior:**
- Always fetches maximum messages (1000 - API limit)
- Uses `last_message_id` to filter already-saved messages
- Deduplicates automatically
- Updates metadata with sync timestamp

**Parameters:**
- `phone` (str): Phone number for authentication (e.g., "+37379276083")
- `chat_id` (str): Telegram chat ID (e.g., "3389864729")
- `verbose` (bool): Print progress messages

**Returns:**
```python
{
    "success": bool,
    "chat_title": str,
    "total_fetched": int,
    "new_messages": int,
    "is_initial_fetch": bool
}
```

**Example:**
```python
from memory import sync_group_messages

# First run: Initial fetch (up to 1000 messages)
result = sync_group_messages(
    phone="+37379276083",
    chat_id="3389864729"
)

# Subsequent runs: Incremental sync (fetches all, filters by last_message_id)
result = sync_group_messages(
    phone="+37379276083",
    chat_id="3389864729"
)

if result["success"]:
    print(f"Chat: {result['chat_title']}")
    print(f"New messages: {result['new_messages']}")
```

---

### 2. `get_group_messages(chat_id, limit=None)`

**Purpose:** Get stored group messages from local storage.

**Parameters:**
- `chat_id` (str): Telegram chat ID
- `limit` (int, optional): Maximum number of messages to return (returns all if None)

**Returns:** List of message dictionaries

**Example:**
```python
from memory import get_group_messages

# Get all messages
messages = get_group_messages("3389864729")
print(f"Total messages: {len(messages)}")

# Get latest 50 messages
recent = get_group_messages("3389864729", limit=50)

# Access message fields
for msg in messages[:5]:
    print(f"[{msg['date']}] {msg['senderUsername']}: {msg['text']}")
```

**Message Fields:**
- `id`: Message ID
- `date`: ISO timestamp
- `text`: Message text
- `senderId`: Sender's user ID
- `senderUsername`: Sender's username
- `senderFirstName`: Sender's first name
- `senderLastName`: Sender's last name
- `isOutgoing`: Boolean
- `isForwarded`: Boolean
- `replyToMessageId`: ID of replied message (if any)
- `media`: Media information (if any)
- `reactions`: List of reactions
- `views`: View count
- `forwards`: Forward count

---

### 3. `get_group_metadata(chat_id)`

**Purpose:** Get group metadata (name, sync info, etc.)

**Parameters:**
- `chat_id` (str): Telegram chat ID

**Returns:** Metadata dictionary or None

**Example:**
```python
from memory import get_group_metadata

metadata = get_group_metadata("3389864729")

if metadata:
    print(f"Group: {metadata['name']}")
    print(f"Last sync: {metadata['last_sync']}")
    print(f"Last message ID: {metadata['last_message_id']}")
    print(f"Created at: {metadata['created_at']}")
```

**Metadata Fields:**
- `id`: Chat ID
- `name`: Group name
- `created_at`: When metadata was first created
- `last_sync`: Last sync timestamp
- `last_message_id`: ID of most recent message
- `total_messages`: Total message count (set on initial fetch)

---

### 4. `save_group_metadata(chat_id, chat_title=None, **additional_fields)`

**Purpose:** Save or update group metadata (usually called internally by sync_group_messages)

**Parameters:**
- `chat_id` (str): Telegram chat ID
- `chat_title` (str, optional): Chat title
- `**additional_fields`: Any additional metadata fields

**Example:**
```python
from memory import save_group_metadata

# Update metadata
save_group_metadata(
    chat_id="3389864729",
    chat_title="My Group",
    custom_field="custom_value"
)
```

---

### 5. `save_group_messages(chat_id, messages)`

**Purpose:** Save messages to group history (usually called internally by sync_group_messages)

**Parameters:**
- `chat_id` (str): Telegram chat ID
- `messages` (list): List of message dictionaries

**Returns:**
```python
{
    "new_count": int,
    "last_message_id": int
}
```

**Example:**
```python
from memory import save_group_messages

messages = [
    {"id": 100, "date": "2025-12-22T10:00:00", "text": "Hello"},
    {"id": 101, "date": "2025-12-22T10:01:00", "text": "World"}
]

result = save_group_messages("3389864729", messages)
print(f"Saved {result['new_count']} new messages")
print(f"Last message ID: {result['last_message_id']}")
```

---

## Participant Functions

### 1. `initialize_participants(chat_id, verbose=True)`

**Purpose:** Create JSON file for every participant in the group (if doesn't exist). Extracts participant info from group_history.

**Parameters:**
- `chat_id` (str): Telegram chat ID
- `verbose` (bool): Print progress

**Returns:**
```python
{
    "success": bool,
    "participants_created": int,
    "participants_existing": int,
    "total_participants": int
}
```

**Example:**
```python
from memory import initialize_participants

# Create participant files (run this once after syncing group messages)
result = initialize_participants("3389864729")

if result["success"]:
    print(f"Created: {result['participants_created']}")
    print(f"Existing: {result['participants_existing']}")
    print(f"Total: {result['total_participants']}")
```

**Notes:**
- Automatically extracts all unique participants from group_history.json
- Creates empty participant files with just user_id, username, and empty personality_snapshots
- Safe to run multiple times (won't overwrite existing files)

---

### 2. `get_participant_messages(chat_id, user_id)`

**Purpose:** Get all messages a user sent in the group (from group_history). Does NOT save to participant JSON.

**Parameters:**
- `chat_id` (str): Telegram chat ID
- `user_id` (str): User ID

**Returns:** List of message dictionaries

**Example:**
```python
from memory import get_participant_messages

# Get messages for specific user
messages = get_participant_messages(
    chat_id="3389864729",
    user_id="526622223"
)

print(f"User sent {len(messages)} messages")

# Show messages
for msg in messages[:5]:
    print(f"[{msg['date']}] {msg['text'][:50]}")
```

**Message Fields:**
- `date`: ISO timestamp
- `text`: Message text
- `emotion`: Emotion analysis (currently "neutral", TODO: implement)

**Why messages aren't saved in participant files:**
- Messages are already in group_history.json (single source of truth)
- Avoids data duplication
- Participant files only store analysis results (personality snapshots)
- Messages can be queried dynamically when needed

---

### 3. `save_personality_analysis(chat_id, user_id, big5_values=None, verbose=True)`

**Purpose:** Save Big5 personality analysis for a participant. Adds new snapshot without erasing previous analyses.

**Parameters:**
- `chat_id` (str): Telegram chat ID
- `user_id` (str): User ID
- `big5_values` (dict, optional): Big5 traits dict. If None, generates random values
- `verbose` (bool): Print progress

**Big5 Values Format:**
```python
{
    "openness": float (0.0-1.0),
    "conscientiousness": float (0.0-1.0),
    "extraversion": float (0.0-1.0),
    "agreeableness": float (0.0-1.0),
    "neuroticism": float (0.0-1.0)
}
```

**Returns:**
```python
{
    "success": bool,
    "user_id": str,
    "username": str,
    "messages_analyzed": int,
    "confidence": float,
    "total_snapshots": int
}
```

**Example:**
```python
from memory import save_personality_analysis

# Save with random values (for testing)
result = save_personality_analysis(
    chat_id="3389864729",
    user_id="526622223"
)

# Save with custom Big5 values
result = save_personality_analysis(
    chat_id="3389864729",
    user_id="526622223",
    big5_values={
        "openness": 0.85,
        "conscientiousness": 0.75,
        "extraversion": 0.60,
        "agreeableness": 0.80,
        "neuroticism": 0.30
    }
)

if result["success"]:
    print(f"Analyzed {result['messages_analyzed']} messages")
    print(f"Confidence: {result['confidence']}")
    print(f"Total snapshots: {result['total_snapshots']}")
```

**Notes:**
- Each call adds a new snapshot (cumulative, not overwriting)
- Confidence increases with message count
- Automatically counts messages using `get_participant_messages`
- Requires participant file to exist (run `initialize_participants` first)

---

### 4. `get_participant_data(chat_id, user_id)`

**Purpose:** Get participant data including all personality snapshots.

**Parameters:**
- `chat_id` (str): Telegram chat ID
- `user_id` (str): User ID

**Returns:** Participant data dictionary or None

**Example:**
```python
from memory import get_participant_data

data = get_participant_data("3389864729", "526622223")

if data:
    print(f"Username: {data['username']}")
    print(f"User ID: {data['user_id']}")
    print(f"Snapshots: {len(data['personality_snapshots'])}")
    
    # Show latest personality analysis
    if data['personality_snapshots']:
        latest = data['personality_snapshots'][-1]
        print(f"\nLatest analysis ({latest['analysis_date']}):")
        print(f"  Messages: {latest['messages_analyzed_count']}")
        print(f"  Confidence: {latest['confidence']}")
        
        big5 = latest['personality_analysis']['big5']
        print(f"  Big5 traits:")
        for trait, value in big5.items():
            print(f"    {trait}: {value}")
```

**Participant Data Structure:**
```python
{
    "user_id": "526622223",
    "username": "Yair",
    "personality_snapshots": [
        {
            "analysis_date": "2025-12-22T14:41:00.889050",
            "messages_analyzed_count": 27,
            "personality_analysis": {
                "big5": {
                    "openness": 0.43,
                    "conscientiousness": 0.51,
                    "extraversion": 0.58,
                    "agreeableness": 0.62,
                    "neuroticism": 0.84
                }
            },
            "confidence": 0.44
        }
    ]
}
```

---

### 5. `list_participants(chat_id)`

**Purpose:** List all participants in a group with summary info.

**Parameters:**
- `chat_id` (str): Telegram chat ID

**Returns:** List of participant summary dictionaries

**Example:**
```python
from memory import list_participants

participants = list_participants("3389864729")

print(f"Total participants: {len(participants)}")

for p in participants:
    print(f"{p['username']:<20} (ID: {p['user_id']})")
    print(f"  Messages: {p['message_count']}")
    print(f"  Snapshots: {p['snapshots_count']}")
```

**Participant Summary Fields:**
- `user_id`: User ID
- `username`: Username
- `message_count`: Number of messages sent (dynamically counted)
- `snapshots_count`: Number of personality snapshots

---

## Action Functions

### 1. `save_action(chat_id, agent_name, group_name, trigger_detected, triggered_by_msg, action_reason, action_id, action_content, timestamp=None)`

**Purpose:** Save an action performed by an agent in the group.

**Parameters:**
- `chat_id` (str): Telegram chat ID
- `agent_name` (str): Name of the agent that performed the action
- `group_name` (str): Name of the group
- `trigger_detected` (str): Type of trigger that was detected (e.g., "direct_mention", "detect_partisan_stance")
- `triggered_by_msg` (str): The message that triggered the action
- `action_reason` (str): Reason for the action (specific content that caused trigger)
- `action_id` (str): ID/type of the action performed (e.g., "answer_direct_mention", "strawman")
- `action_content` (str): Content of the action (e.g., message sent by agent)
- `timestamp` (str, optional): ISO timestamp (auto-generated if None)

**Returns:**
```python
{
    "success": bool,
    "agent_name": str,
    "action_id": str,
    "total_actions": int
}
```

**Example:**
```python
from memory import save_action

# Save agent action
result = save_action(
    chat_id="3389864729",
    agent_name="SandraK9",
    group_name="Dev Community Israel",
    trigger_detected="direct_mention",
    triggered_by_msg="hey @SandraK9, what do you think?",
    action_reason="User directly mentioned Sandra asking for opinion",
    action_id="answer_direct_mention",
    action_content="I think it's a great idea! Let's discuss more.",
    timestamp="2025-12-22T14:30:00"  # Optional
)

print(f"Saved action for {result['agent_name']}")
print(f"Total actions: {result['total_actions']}")
```

**Action Structure:**
```python
{
    "agent_name": "SandraK9",
    "group_name": "Dev Community Israel",
    "trigger_detected": "direct_mention",
    "triggered_by_msg": "hey @SandraK9, what do you think?",
    "action_reason": "User directly mentioned Sandra asking for opinion",
    "action_id": "answer_direct_mention",
    "action_content": "I think it's a great idea!",
    "timestamp": "2025-12-22T14:30:00"
}
```

---

### 2. `get_agent_actions(chat_id, agent_name, limit=None)`

**Purpose:** Get all actions for a specific agent.

**Parameters:**
- `chat_id` (str): Telegram chat ID
- `agent_name` (str): Name of the agent
- `limit` (int, optional): Maximum number of actions to return (most recent first)

**Returns:** List of action dictionaries (sorted by timestamp, most recent first)

**Example:**
```python
from memory import get_agent_actions

# Get all actions for Sandra
actions = get_agent_actions("3389864729", "SandraK9")
print(f"Total actions: {len(actions)}")

# Get latest 10 actions
recent = get_agent_actions("3389864729", "SandraK9", limit=10)

for action in recent:
    print(f"[{action['timestamp']}] {action['action_id']}")
    print(f"  Trigger: {action['trigger_detected']}")
    print(f"  Content: {action['action_content']}")
```

---

### 3. `get_all_actions(chat_id, limit=None)`

**Purpose:** Get all actions from all agents in a group.

**Parameters:**
- `chat_id` (str): Telegram chat ID
- `limit` (int, optional): Maximum number of actions to return (most recent first)

**Returns:** List of action dictionaries from all agents (sorted by timestamp)

**Example:**
```python
from memory import get_all_actions

# Get all actions
all_actions = get_all_actions("3389864729")
print(f"Total actions from all agents: {len(all_actions)}")

# Get latest 50 actions
recent = get_all_actions("3389864729", limit=50)

for action in recent:
    print(f"{action['agent_name']}: {action['action_id']}")
```

---

### 4. `get_actions_by_trigger(chat_id, trigger_type, limit=None)`

**Purpose:** Get all actions filtered by trigger type.

**Parameters:**
- `chat_id` (str): Telegram chat ID
- `trigger_type` (str): Type of trigger to filter by
- `limit` (int, optional): Maximum number of actions to return

**Returns:** List of action dictionaries matching the trigger type

**Example:**
```python
from memory import get_actions_by_trigger

# Get all actions triggered by direct mentions
mentions = get_actions_by_trigger("3389864729", "direct_mention")
print(f"Actions triggered by direct mentions: {len(mentions)}")

for action in mentions:
    print(f"{action['agent_name']}: {action['action_content']}")

# Get partisan stance actions
partisan = get_actions_by_trigger("3389864729", "detect_partisan_stance", limit=10)
```

---

### 5. `list_agents(chat_id)`

**Purpose:** List all agents that have performed actions with statistics.

**Parameters:**
- `chat_id` (str): Telegram chat ID

**Returns:** List of agent summary dictionaries (sorted by total actions)

**Example:**
```python
from memory import list_agents

agents = list_agents("3389864729")

for agent in agents:
    print(f"{agent['agent_name']}")
    print(f"  Total actions: {agent['total_actions']}")
    print(f"  Unique triggers: {agent['unique_triggers']}")
    print(f"  Triggers: {', '.join(agent['triggers'])}")
    print(f"  Last action: {agent['last_action']}")
```

**Agent Summary Fields:**
- `agent_name`: Agent name
- `total_actions`: Total number of actions performed
- `unique_triggers`: Number of unique trigger types
- `triggers`: List of trigger types used
- `last_action`: Timestamp of most recent action

---

### 6. `get_action_statistics(chat_id)`

**Purpose:** Get comprehensive statistics about all actions in a group.

**Parameters:**
- `chat_id` (str): Telegram chat ID

**Returns:** Dictionary with statistics

**Example:**
```python
from memory import get_action_statistics

stats = get_action_statistics("3389864729")

print(f"Total actions: {stats['total_actions']}")
print(f"Total agents: {stats['total_agents']}")
print(f"Most active agent: {stats['most_active_agent']}")
print(f"Latest action: {stats['latest_action']}")

print("\nActions by trigger:")
for trigger, count in stats['actions_by_trigger'].items():
    print(f"  {trigger}: {count}")

print("\nActions by type:")
for action_type, count in stats['actions_by_type'].items():
    print(f"  {action_type}: {count}")
```

**Statistics Fields:**
- `total_actions`: Total number of actions across all agents
- `total_agents`: Number of agents that have performed actions
- `actions_by_trigger`: Dict of trigger types and their counts
- `actions_by_type`: Dict of action IDs and their counts
- `most_active_agent`: Name of agent with most actions
- `latest_action`: Timestamp of most recent action

---

## Complete Workflow Example

```python
from memory import (
    sync_group_messages,
    get_group_messages,
    get_group_metadata,
    initialize_participants,
    get_participant_messages,
    save_personality_analysis,
    list_participants,
    get_participant_data,
    save_action,
    get_agent_actions,
    list_agents,
    get_action_statistics
)

PHONE = "+37379276083"
CHAT_ID = "3389864729"

# ========================================
# STEP 1: Sync Group Messages
# ========================================
print("Syncing group messages...")
result = sync_group_messages(PHONE, CHAT_ID)

if result["success"]:
    print(f"✅ Synced {result['new_messages']} new messages")
else:
    print(f"❌ Sync failed: {result.get('error')}")
    exit(1)

# ========================================
# STEP 2: View Group Data
# ========================================
metadata = get_group_metadata(CHAT_ID)
print(f"\nGroup: {metadata['name']}")
print(f"Last sync: {metadata['last_sync']}")

messages = get_group_messages(CHAT_ID)
print(f"Total messages: {len(messages)}")

# ========================================
# STEP 3: Initialize Participants
# ========================================
print("\nInitializing participants...")
result = initialize_participants(CHAT_ID)
print(f"Created {result['participants_created']} participant files")

# ========================================
# STEP 4: List Participants
# ========================================
participants = list_participants(CHAT_ID)
print(f"\nFound {len(participants)} participants:")
for p in participants:
    print(f"  - {p['username']}: {p['message_count']} messages")

# ========================================
# STEP 5: Analyze Participant
# ========================================
if participants:
    user_id = participants[0]['user_id']
    
    # Get messages for analysis
    user_messages = get_participant_messages(CHAT_ID, user_id)
    print(f"\nAnalyzing {participants[0]['username']}...")
    print(f"Message count: {len(user_messages)}")
    
    # Save personality analysis
    result = save_personality_analysis(
        chat_id=CHAT_ID,
        user_id=user_id,
        big5_values={
            "openness": 0.75,
            "conscientiousness": 0.65,
            "extraversion": 0.80,
            "agreeableness": 0.70,
            "neuroticism": 0.40
        }
    )
    
    print(f"✅ Analysis saved (confidence: {result['confidence']})")
    
    # View complete participant data
    data = get_participant_data(CHAT_ID, user_id)
    print(f"\nTotal snapshots: {len(data['personality_snapshots'])}")

# ========================================
# STEP 6: Log Agent Actions
# ========================================
print("\nLogging agent actions...")

# Example: Agent responds to a direct mention
save_action(
    chat_id=CHAT_ID,
    agent_name="SandraK9",
    group_name=metadata['name'],
    trigger_detected="direct_mention",
    triggered_by_msg="@SandraK9 what do you think about this?",
    action_reason="Direct mention from user requesting opinion",
    action_id="answer_direct_mention",
    action_content="I think it's a great idea! Let's discuss more."
)

# View actions
sandra_actions = get_agent_actions(CHAT_ID, "SandraK9")
print(f"SandraK9 actions: {len(sandra_actions)}")

# View all agents
agents = list_agents(CHAT_ID)
print(f"\nActive agents: {len(agents)}")
for agent in agents:
    print(f"  - {agent['agent_name']}: {agent['total_actions']} actions")

# View statistics
stats = get_action_statistics(CHAT_ID)
print(f"\nTotal actions: {stats['total_actions']}")
print(f"Most active: {stats.get('most_active_agent', 'N/A')}")

# ========================================
# STEP 7: Incremental Updates
# ========================================
print("\nRunning incremental sync...")
result = sync_group_messages(PHONE, CHAT_ID)
print(f"New messages: {result['new_messages']}")
```

---

## Notes

### Message Storage
- **Group messages:** Stored in `group_history.json` (single source of truth)
- **Participant messages:** NOT duplicated in participant files
- Use `get_participant_messages()` to dynamically query messages by user

### Personality Analysis
- Snapshots are **cumulative** (never overwritten)
- Each analysis is timestamped
- Confidence increases with message count
- Current implementation uses random Big5 values (TODO: implement real analysis)

### Agent Actions
- Each agent has a separate action log file
- Actions include trigger type, triggering message, reason, and response
- Filter actions by trigger type, agent, or time period
- Statistics available for analyzing agent behavior patterns

### Performance
- `sync_group_messages()` optimizes by tracking `last_message_id`
- Only new messages are processed (skips already-saved messages)
- API limit: 1000 messages per call

### Data Persistence
- All data stored in JSON files (no database required)
- Files are human-readable and easy to inspect
- Located in `data/[chat_id]/` directory
- **Note:** `data/` folder is in .gitignore (not version controlled)

---

## File Locations

```
langgraph/
├── memory/
│   ├── __init__.py          # Package exports
│   ├── storage.py           # Low-level JSON I/O
│   ├── group.py             # Group functions
│   ├── participant.py       # Participant functions
│   ├── actions.py           # Agent action logging
│   ├── README.md            # This file
│   └── examples/
│       ├── example_sync.py
│       ├── example_participants.py
│       ├── example_actions.py
│       └── sync_and_analyze.py
│
└── data/                    # Data storage (gitignored)
    └── [chat_id]/
        ├── group_metadata.json
        ├── group_history.json
        ├── participant/
        │   └── [user_id].json
        └── actions/
            └── [agent_name].json
```
