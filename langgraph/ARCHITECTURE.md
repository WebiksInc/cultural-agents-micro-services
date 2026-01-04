# LangGraph Architecture - Cultural Agents System

A comprehensive guide to understanding the hierarchical LangGraph implementation powering autonomous AI agents in Telegram groups.

## Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [State Management](#state-management)
- [Graph Flow](#graph-flow)
- [Components Deep Dive](#components-deep-dive)
- [Configuration](#configuration)
- [Execution Flow Example](#execution-flow-example)
- [Key Concepts](#key-concepts)

---

## Overview

This system implements **autonomous AI agents** that monitor Telegram group conversations and participate naturally based on their personas, triggers, and goals. The architecture uses **LangGraph** to create a hierarchical state machine with:

- **1 Supervisor Graph**: Analyzes messages, manages agent execution
- **N Agent Subgraphs**: Each agent runs independently to detect triggers and generate responses

### Core Features

✅ **Multi-Agent System**: Multiple agents with different personalities and behaviors  
✅ **Trigger-Based Actions**: Agents respond to specific conversation patterns  
✅ **Emotion Analysis**: Enriches messages with sentiment data  
✅ **Validation Loop**: Ensures responses meet quality standards before sending  
✅ **Telegram Integration**: Real-time polling and message execution  

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    run_supervisor.py                         │
│                   (Main Entry Point)                         │
│  - Polls Telegram for new messages every 60s                │
│  - Manages message history and deduplication                │
│  - Invokes Supervisor Graph when new messages arrive        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   SUPERVISOR GRAPH                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Component B  │ →  │   Agents     │ →  │  Scheduler   │  │
│  │ (Emotion     │    │  (Parallel)  │    │              │  │
│  │  Analysis)   │    │              │    │              │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                            ↓                     ↓           │
│                      ┌──────────────┐    ┌──────────────┐  │
│                      │  Agent 1     │    │  Executor    │  │
│                      │  Subgraph    │    │ (Send to     │  │
│                      │              │    │  Telegram)   │  │
│                      └──────────────┘    └──────────────┘  │
│                      ┌──────────────┐           ↓           │
│                      │  Agent 2     │         END           │
│                      │  Subgraph    │                       │
│                      └──────────────┘                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     AGENT SUBGRAPH                           │
│  (Runs for each agent independently)                        │
│                                                              │
│  START → Orchestrator → Trigger Analysis → Orchestrator     │
│              ↓                                               │
│        Decision Maker → Orchestrator                        │
│              ↓                                               │
│        Text Generator (E.1) → Orchestrator                  │
│              ↓                                               │
│        Styler (E.2) → Orchestrator                          │
│              ↓                                               │
│        Validator → Orchestrator                             │
│              ↓ (if approved)                                │
│            END                                               │
│              ↓ (if rejected & retries < MAX)                │
│        Back to Text Generator                               │
└─────────────────────────────────────────────────────────────┘
```

---

## State Management

### SupervisorState

The global state for the supervisor graph:

```python
class SupervisorState(TypedDict):
    # Group Analysis
    group_sentiment: str              # 2-3 sentence summary of group mood
    group_metadata: dict              # {"name": ..., "id": ..., "members": ..., "topic": ...}
    
    # Message History
    recent_messages: List[Message]   # Messages from Telegram (enriched with emotions)
    
    # Action Tracking
    selected_actions: List[dict]     # Actions selected by agents
    execution_queue: List[dict]      # Actions ready to execute
    
    # Internal Tracking
    current_nodes: Optional[List[str]]
    next_nodes: Optional[List[str]]
```

**Key Points:**
- `recent_messages` is shared across all agents (read-only)
- `selected_actions` uses a special `add_or_clear` reducer (can append or clear)
- Messages are enriched with `message_emotion` by Component B

### AgentState

The state for each agent subgraph:

```python
class AgentState(TypedDict):
    # Copied from Supervisor
    recent_messages: List[Message]
    group_sentiment: str
    group_metadata: dict
    
    # Agent Configuration (loaded from JSON files)
    selected_persona: dict           # Personality, background, writing style
    agent_type: str                  # "active", "chaos", "off_radar"
    agent_goal: str                  # What the agent is trying to achieve
    triggers: dict                   # Trigger definitions
    actions: dict                    # Available actions
    agent_prompt: str                # System prompt for this agent type
    
    # Processing Outputs
    detected_trigger: Optional[dict]      # From Trigger Analysis
    selected_action: Optional[dict]       # From Decision Maker
    generated_response: Optional[str]     # From Text Generator (E.1)
    styled_response: Optional[str]        # From Styler (E.2)
    validation: Optional[dict]            # From Validator
    validation_feedback: Optional[str]    # Feedback for retry
    retry_count: int                      # Validation retry counter
    
    # Internal Routing
    current_node: Optional[str]
    next_node: Optional[str]
```

### Message Structure

```python
class Message(TypedDict):
    message_id: str
    sender_id: str
    sender_username: str
    sender_first_name: str
    sender_last_name: str
    text: str
    date: datetime
    timestamp: str                        # ISO format
    reactions: Optional[List[dict]]       # [{"emoji": "👍", "count": 2, "users": [...]}]
    message_emotion: Optional[str]        # Added by Component B
    sender_personality: Optional[dict]    # Added by Component C (on-demand)
    processed: Optional[bool]             # Tracking flag
    replyToMessageId: Optional[int]       # For threaded conversations
```

---

## Graph Flow

### Supervisor Graph Flow

```
START 
  ↓
Component B (Emotion Analysis)
  │
  ├─→ Analyzes unclassified messages
  ├─→ Adds message_emotion to each message
  └─→ Generates group_sentiment summary
  ↓
[Agent 1, Agent 2, ...] (Parallel Execution)
  │
  ├─→ Each agent runs its subgraph
  └─→ Agents return selected_action to supervisor
  ↓
Scheduler
  │
  ├─→ Collects all selected_actions
  ├─→ Filters out "no_action_needed"
  └─→ Builds execution_queue (FIFO)
  ↓
Executor
  │
  ├─→ Gets ready actions from queue
  ├─→ Sends to Telegram API
  │   ├─→ send_message (for text)
  │   ├─→ add_reaction (for emoji)
  │   └─→ send_typing (for realism)
  └─→ Clears execution_queue and selected_actions
  ↓
END
```

### Agent Subgraph Flow

Each agent follows this flow:

```
START
  ↓
Orchestrator (Entry)
  ↓
Trigger Analysis
  │
  ├─→ Analyzes recent_messages against agent's triggers
  ├─→ Returns detected_trigger with justification
  └─→ Back to Orchestrator
  ↓
Orchestrator (Route)
  ├─→ If no trigger: END (no_action_needed)
  └─→ If trigger detected: → Decision Maker
  ↓
Decision Maker
  │
  ├─→ Selects action from suggested_actions
  ├─→ Defines purpose for this action
  └─→ Back to Orchestrator
  ↓
Orchestrator (Route)
  ├─→ If no action: END (no_action_needed)
  └─→ If action selected: → Text Generator
  ↓
Text Generator (E.1)
  │
  ├─→ Generates response content based on action
  ├─→ Uses agent_prompt + persona + context
  └─→ Back to Orchestrator
  ↓
Orchestrator (Route)
  ├─→ If action_id == "add_reaction": → Validator (skip Styler)
  └─→ Otherwise: → Styler
  ↓
Styler (E.2)
  │
  ├─→ Applies persona's writing style
  ├─→ Adds linguistic patterns, typos, etc.
  └─→ Back to Orchestrator
  ↓
Orchestrator (Route)
  ↓
Validator
  │
  ├─→ Checks if response meets quality standards
  ├─→ Validates against agent_goal and action purpose
  └─→ Back to Orchestrator
  ↓
Orchestrator (Final Route)
  ├─→ If approved OR retry_count >= MAX_RETRIES: END ✓
  └─→ If rejected AND retry_count < MAX_RETRIES: → Text Generator (retry)
```

---

## Components Deep Dive

### 1. run_supervisor.py (Main Entry Point)

**Purpose:** Polling loop that fetches messages and runs the supervisor graph.

**Key Responsibilities:**
- Poll Telegram API every 60 seconds
- Maintain `seen_message_ids` deque (max 1000) to avoid reprocessing
- Filter out agent messages (mark as processed)
- Invoke supervisor graph only when new unprocessed messages exist
- Initialize group metadata on first run

**Important Variables:**
```python
MESSAGE_CHECK_INTERVAL = 60          # Poll every 60 seconds
TELEGRAM_FETCH_LIMIT = 12            # Fetch up to 12 messages
MAX_RECENT_MESSAGES = 12             # Keep last 12 messages in state
seen_message_ids = deque(maxlen=1000) # Deduplication
```

**Flow:**
```python
# Initialization
1. Build supervisor graph
2. Load agent personas
3. Fetch group metadata (once)
4. Fetch initial message history
5. Run graph if unprocessed messages exist

# Main Loop
while True:
    1. Fetch latest messages
    2. Filter new messages (not in seen_message_ids)
    3. Mark agent messages as processed
    4. If actionable messages exist:
        - Invoke supervisor graph
        - Mark all messages as processed
    5. Sleep 30s between checks
```

---

### 2. Component B (Emotion Analysis)

**Purpose:** Enrich messages with emotion/sentiment data.

**Input:**
- `recent_messages` (only unclassified messages, where `message_emotion` is None)
- `group_metadata`

**Output:**
- Updated `recent_messages` with `message_emotion` field
- `group_sentiment` (2-3 sentence summary)

**LLM Prompt Includes:**
- Group name, topic, member count
- Full conversation history (for context)
- Unclassified messages to analyze

**Example Output:**
```python
message['message_emotion'] = "Enthusiastic and positive about Italy"
group_sentiment = "The group is discussing travel destinations with high enthusiasm. Apple vs Samsung debate is ongoing with mixed opinions."
```

---

### 3. Agent Subgraph Components

#### Orchestrator

**Purpose:** Central routing hub for the agent subgraph.

**Routing Logic:**
```python
# Entry point
if current_node is None:
    return next_node = "trigger_analysis"

# After trigger analysis
if detected_trigger is None or neutral:
    return END (no_action_needed)
else:
    return next_node = "decision_maker"

# After decision maker
if selected_action is None:
    return END (no_action_needed)
else:
    return next_node = "text_generator"

# After text generator
if action_id == "add_reaction":
    return next_node = "validator"  # Skip styler for emoji
else:
    return next_node = "styler"

# After validator
if approved OR retry_count >= MAX_RETRIES:
    return END
else:
    return next_node = "text_generator"  # Retry with feedback
```

#### Trigger Analysis

**Purpose:** Detect which trigger (if any) is activated by recent messages.

**Input:**
- `recent_messages` (with emotions)
- `triggers` (JSON definitions)
- `agent_type`, `agent_goal`

**LLM Prompt Includes:**
- Agent name, type, goal
- Recent messages formatted with timestamps and emotions
- Triggers JSON (with descriptions and indicators)
- Special rules (e.g., "don't react to same message twice")

**Output:**
```json
{
  "id": "samsung_vs_apple_debate",
  "justification": "User mentioned preferring Samsung over Apple",
  "target_message": {
    "timestamp": "2025-12-24T10:30:00.000Z",
    "text": "Samsung is better than Apple"
  }
}
```

**Neutral Response:**
```json
{
  "id": "neutral",
  "justification": "No relevant trigger detected"
}
```

#### Decision Maker

**Purpose:** Choose which action to take from suggested actions.

**Input:**
- `detected_trigger` (with id and justification)
- `actions` (JSON definitions)
- `triggers` (to get suggested_actions for this trigger)

**Process:**
1. Get `suggested_actions` from trigger definition
2. Fetch full action details for each suggested action
3. Present to LLM with context
4. LLM selects best action and provides purpose

**Output:**
```json
{
  "id": "send_message",
  "purpose": "Defend Samsung and point out Apple's ecosystem lock-in",
  "target_message": {
    "timestamp": "2025-12-24T10:30:00.000Z",
    "text": "Samsung is better than Apple"
  }
}
```

#### Text Generator (E.1)

**Purpose:** Generate the actual response content.

**Input:**
- `selected_action` (id, purpose, target_message)
- `agent_prompt` (system prompt for agent type)
- `selected_persona` (personality, background, style)
- `recent_messages`, `group_sentiment`
- `validation_feedback` (if retry)

**LLM Prompt Includes:**
- Agent name, goal
- Action id, description, purpose
- Group context (name, topic, sentiment)
- Recent messages (formatted with emotions and "YOU" markers)
- Persona details
- **If retry:** Previous response + validation feedback

**Output:**
```python
generated_response = "Samsung actually has better customization and doesn't lock you into their ecosystem like Apple does. Plus their screens are amazing!"
```

#### Styler (E.2)

**Purpose:** Apply persona's linguistic style to the generated content.

**Input:**
- `generated_response` (raw content)
- `selected_persona` (writing style, patterns)
- `agent_prompt` (system prompt)
- `recent_messages` (for style consistency)

**Output:**
```python
styled_response = "Samsung actually has wayyy better customization and doesn't lock u into their ecosystem like Apple does lol. Plus their screens are amazinggg! 📱✨"
```

**Styling Includes:**
- Typos, abbreviations ("you" → "u")
- Emoji usage patterns
- Punctuation style
- Capitalization patterns
- Slang and filler words

#### Validator

**Purpose:** Ensure response meets quality standards before sending.

**Input:**
- `styled_response`
- `agent_goal`
- `selected_action` (purpose)
- `selected_persona`
- `retry_count`

**Validation Checks:**
- ✅ Aligns with agent_goal
- ✅ Fulfills action purpose
- ✅ Matches persona style
- ✅ Appropriate length and tone
- ✅ No obvious errors

**Output (Approved):**
```json
{
  "approved": true,
  "justification": "Response defends Samsung effectively and matches Sandra's enthusiastic style"
}
```

**Output (Rejected):**
```json
{
  "approved": false,
  "justification": "Response is too aggressive and attacks the user personally instead of focusing on tech"
}
```

**Max Retries:** If `retry_count >= 3`, validator approves by default to prevent infinite loops.

---

### 4. Scheduler

**Purpose:** Build execution queue from selected actions.

**Input:**
- `selected_actions` (from all agents)

**Process:**
1. Filter out actions with `status == "no_action_needed"`
2. Build queue items with all necessary fields
3. Set status to "pending"

**Output:**
```python
execution_queue = [
    {
        "agent_name": "Sandra",
        "agent_type": "active",
        "action_id": "send_message",
        "action_purpose": "Defend Samsung",
        "action_content": "Samsung actually has wayyy better...",
        "phone_number": "+37379276083",
        "target_message": {"timestamp": "...", "text": "..."},
        "status": "pending"
    }
]
```

---

### 5. Executor

**Purpose:** Send actions to Telegram API.

**Input:**
- `execution_queue`
- `group_metadata` (for chat_id)
- `recent_messages` (to determine if reply should be used)

**Process:**
For each action:
1. Determine action type (send_message, add_reaction)
2. Send typing indicator (for realism)
3. Calculate typing duration based on message length
4. Execute action:
   - **send_message:** `send_message(phone, chat_id, content, reply_timestamp)`
   - **add_reaction:** `add_reaction(phone, chat_id, emoji, target_timestamp)`
5. Log to Logfire

**Important Logic:**
- Only use `reply_timestamp` if target message is NOT the most recent
- For most recent messages, send as new message (not reply)
- Add realistic typing delays

**Output:**
- Clears `execution_queue` and `selected_actions`

---

## Configuration

### supervisor_config.json

```json
{
  "telegram": {
    "chat_id": "3389864729",
    "api_host": "telegram2",
    "api_port": 4000
  },
  "polling": {
    "message_check_interval_seconds": 60,
    "telegram_fetch_limit": 12,
    "max_recent_messages": 12
  },
  "agents": [
    {
      "type": "active",
      "name": "Sandra",
      "username": "SandraK9",
      "persona_file": "agents_personas/sandra_persona.json",
      "agent_goal": "Spark Samsung vs Apple debates..."
    }
  ]
}
```

### model_config.json

Defines which LLM models to use for each component:

```json
{
  "component_B": {
    "model": "gpt-4o-mini",
    "provider": "openai",
    "temperature": 0.3
  },
  "trigger_analysis": {
    "model": "gpt-4o",
    "provider": "openai",
    "temperature": 0.4
  },
  "decision_maker": {...},
  "text_generator": {...},
  "styler": {...},
  "validator": {...}
}
```

### Agent Configuration Files

Each agent has:

1. **Persona JSON** (`agents_personas/sandra_persona.json`):
   - Personal details (name, age, occupation)
   - Writing style patterns
   - Background and interests

2. **Triggers JSON** (`triggers/active/active_triggers.json`):
   - Trigger definitions with ids
   - Indicators (what to look for)
   - Suggested actions

3. **Actions JSON** (`actions/active/active_actions.json`):
   - Action definitions with ids
   - Descriptions of what each action does

4. **Agent Prompt** (`prompts/agent_types/active_prompt.txt`):
   - System prompt defining agent behavior

---

## Execution Flow Example

Let's trace a complete example:

### Initial State

**New Message Arrives:**
```
User: "I love my new iPhone! Best purchase ever!"
```

### Step 1: run_supervisor.py

```python
# Polling loop detects new message
new_message = {
    "message_id": "123",
    "sender_username": "john_doe",
    "text": "I love my new iPhone! Best purchase ever!",
    "processed": False
}

# Not an agent message, invoke supervisor graph
state = graph.invoke(state)
```

### Step 2: Component B (Emotion Analysis)

**LLM analyzes message:**
```python
message['message_emotion'] = "Very positive and enthusiastic about iPhone purchase"
group_sentiment = "Group member expressing strong satisfaction with Apple product"
```

### Step 3: Agent Subgraphs (Parallel)

#### Sandra (Active Agent - Samsung advocate)

**Trigger Analysis:**
```json
{
  "id": "samsung_vs_apple_debate",
  "justification": "User expressed strong positive sentiment towards iPhone",
  "target_message": {
    "timestamp": "2025-12-24T14:30:00.000Z",
    "text": "I love my new iPhone! Best purchase ever!"
  }
}
```

**Decision Maker:**
```json
{
  "id": "send_message",
  "purpose": "Playfully challenge the iPhone enthusiasm and highlight Samsung advantages"
}
```

**Text Generator (E.1):**
```
"That's great! Have you tried Samsung's latest Galaxy though? The customization is incredible and you're not locked into one ecosystem."
```

**Styler (E.2):**
```
"omg thats great!! but have u tried Samsung's latest Galaxy tho? the customization is incredibleee and ur not locked into one ecosystem lol 📱✨"
```

**Validator:**
```json
{
  "approved": true,
  "justification": "Response is playful, on-topic, and aligns with Sandra's goal without being aggressive"
}
```

**Return to Supervisor:**
```python
selected_action = {
    "id": "send_message",
    "purpose": "Challenge iPhone enthusiasm",
    "target_message": {...}
}
styled_response = "omg thats great!! but have u tried..."
```

#### Victor (Off-Radar Agent - Quiet observer)

**Trigger Analysis:**
```json
{
  "id": "neutral",
  "justification": "Message doesn't warrant off-radar agent participation"
}
```

**Returns:** `no_action_needed`

### Step 4: Scheduler

```python
execution_queue = [
    {
        "agent_name": "Sandra",
        "action_id": "send_message",
        "action_content": "omg thats great!! but have u tried...",
        "phone_number": "+37379276083",
        "target_message": {"timestamp": "2025-12-24T14:30:00.000Z", ...},
        "status": "pending"
    }
]
```

### Step 5: Executor

```python
# 1. Send typing indicator
send_typing(phone="+37379276083", chat_id="3389864729")

# 2. Calculate typing duration (based on message length)
duration = 5000ms  # ~5 seconds

# 3. Wait (simulating typing)
time.sleep(duration / 1000)

# 4. Send message
send_message(
    phone="+37379276083",
    chat_id="3389864729",
    message="omg thats great!! but have u tried...",
    reply_timestamp="2025-12-24T14:30:00.000Z"
)

# 5. Clear queue
execution_queue = []
selected_actions = []
```

### Result

Sandra's response appears in the Telegram group:
```
Sandra: omg thats great!! but have u tried Samsung's latest Galaxy tho? 
        the customization is incredibleee and ur not locked into one 
        ecosystem lol 📱✨
        ↳ Replying to: "I love my new iPhone! Best purchase ever!"
```

---

## Key Concepts

### 1. Hierarchical State Management

The system uses **two levels of state**:
- **SupervisorState**: Global state shared across all agents
- **AgentState**: Local state for each agent's processing

State is copied from Supervisor → Agent at the start of each agent subgraph, and results are returned via `Command` objects.

### 2. Parallel Agent Execution

All agents run **in parallel** after Component B:
```python
# In build_graph.py
for agent_node_name in agent_nodes:
    supervisor_builder.add_edge("component_B", agent_node_name)
```

Each agent independently decides whether to act. The supervisor doesn't wait for one to finish before starting another.

### 3. Command-Based Routing

Agents don't return to supervisor via explicit edges. Instead, they use `Command` objects:

```python
return Command(
    update={"selected_actions": [action_entry]},
    goto="scheduler"
)
```

This allows dynamic routing and state updates in a single return.

### 4. Validation Retry Loop

The agent subgraph includes a **retry mechanism**:
- Validator rejects → feedback sent to Text Generator
- Text Generator regenerates with feedback
- Max 3 retries, then auto-approve

This ensures quality while preventing infinite loops.

### 5. Message Deduplication

Three mechanisms prevent duplicate processing:
1. **seen_message_ids deque**: Tracks last 1000 message IDs
2. **processed flag**: Marks messages as analyzed
3. **Agent message filtering**: Agents don't respond to their own messages

### 6. Trigger System

Agents use a **trigger → action** pattern:
- **Triggers** define conversation patterns to watch for
- Each trigger has **suggested_actions**
- Decision Maker chooses from suggested actions
- This creates predictable, goal-oriented behavior

### 7. Persona-Driven Styling

Responses are generated in two stages:
1. **Content** (E.1): What to say (factual, clear)
2. **Style** (E.2): How to say it (persona-specific patterns)

This separation ensures content quality while maintaining authentic persona voices.

---

## File Structure Reference

```
langgraph/
├── run_supervisor.py              # Main entry point
├── build_graph.py                 # Graph construction
├── utils.py                       # Helper functions
├── telegram_exm.py                # Telegram API wrapper
│
├── states/
│   ├── supervisor_state.py        # SupervisorState definition
│   └── agent_state.py             # AgentState + Message definition
│
├── nodes/
│   ├── supervisor/
│   │   ├── component_B.py         # Emotion Analysis
│   │   ├── scheduler.py           # Action Queue Builder
│   │   └── executor.py            # Telegram Sender
│   │
│   └── agent/
│       ├── orchestrator.py        # Agent Router
│       ├── trigger_analysis.py    # Trigger Detection
│       ├── decision_maker.py      # Action Selection
│       ├── component_E1.py        # Text Generation
│       ├── component_E2.py        # Style Application
│       └── validator.py           # Quality Check
│
├── config/
│   ├── supervisor_config.json     # Main config
│   └── model_config.json          # LLM settings
│
├── agents_personas/               # Agent personality files
├── triggers/                      # Trigger definitions by type
├── actions/                       # Action definitions by type
├── prompts/                       # LLM prompt templates
└── memory/                        # Data persistence layer
```

---

## Summary

This LangGraph implementation creates a **sophisticated multi-agent system** where:

1. **Supervisor Graph** manages the overall flow and coordinates agents
2. **Agent Subgraphs** independently analyze, decide, generate, and validate responses
3. **State flows hierarchically** from global (Supervisor) to local (Agent) and back
4. **LLMs are used strategically** at key decision points (emotion, triggers, actions, generation, styling, validation)
5. **Quality is maintained** through validation loops and retry mechanisms
6. **Realism is achieved** through persona-driven styling and natural timing

The architecture is **modular**, **scalable**, and **maintainable**, making it easy to add new agents, triggers, or actions without touching core logic.
