# Cultural Agents Microservices - Complete Architecture

## Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Service Components](#service-components)
  - [Telegram2 Service](#telegram2-service)
  - [LangGraph Service](#langgraph-service)
- [Communication Flow](#communication-flow)
- [Deployment Architecture](#deployment-architecture)
- [Data Flow](#data-flow)
- [API Integration](#api-integration)
- [State Management](#state-management)
- [Agent System](#agent-system)
- [Security & Authentication](#security--authentication)
- [Monitoring & Logging](#monitoring--logging)

---

## Overview

The Cultural Agents Microservices project is a distributed system that creates **autonomous AI agents** capable of participating naturally in Telegram group conversations. The system consists of two main microservices:

1. **telegram2**: A stateless REST API gateway for Telegram operations
2. **langgraph**: An AI agent orchestration system using LangGraph

### Key Features

✅ **Multi-Agent System**: Multiple AI agents with distinct personalities and behaviors  
✅ **Real-time Telegram Integration**: Continuous monitoring and interaction with Telegram groups  
✅ **Emotion-Aware Responses**: Messages are analyzed for sentiment to inform agent decisions  
✅ **Validation Pipeline**: Multi-stage quality control ensures appropriate responses  
✅ **Persona-Based Styling**: Each agent has unique communication patterns  
✅ **Containerized Deployment**: Docker Compose orchestration for easy deployment  
✅ **Session Persistence**: Maintains authenticated Telegram sessions across restarts  
✅ **Scalable Architecture**: Microservices pattern allows independent scaling  

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DOCKER COMPOSE NETWORK                           │
│                                                                          │
│  ┌────────────────────────┐         ┌─────────────────────────────┐    │
│  │    TELEGRAM2 SERVICE    │         │    LANGGRAPH SERVICE         │    │
│  │   (Node.js/TypeScript)  │◄────────┤   (Python/LangGraph)         │    │
│  │                         │  HTTP   │                              │    │
│  │  Port: 4000             │ Requests│  Environment Variables:      │    │
│  │  Base: Node 20 Alpine   │         │  - TELEGRAM_HOST=telegram2   │    │
│  │                         │         │  - TELEGRAM_PORT=4000        │    │
│  │  ┌──────────────────┐   │         │                              │    │
│  │  │ GramJS (Telegram │   │         │  ┌─────────────────────┐    │    │
│  │  │  Client Library) │   │         │  │  Polling Loop       │    │    │
│  │  │                  │   │         │  │  (60s interval)     │    │    │
│  │  └──────────────────┘   │         │  │                     │    │    │
│  │         ↕                │         │  │  Fetches messages   │    │    │
│  │  ┌──────────────────┐   │         │  │  every 60 seconds   │    │    │
│  │  │ Session Storage  │   │         │  └─────────────────────┘    │    │
│  │  │ (JSON Files)     │   │         │                              │    │
│  │  │ /app/data        │   │         │  ┌─────────────────────┐    │    │
│  │  └──────────────────┘   │         │  │ Supervisor Graph    │    │    │
│  │         ↕                │         │  │                     │    │    │
│  │  Volume: ./volumes/      │         │  │ • Emotion Analysis  │    │    │
│  │          telegram2       │         │  │ • Agent Execution   │    │    │
│  └────────────────────────┘         │  │ • Action Scheduling │    │    │
│         ↕                            │  │ • Telegram Executor │    │    │
│  ┌────────────────────────┐         │  └─────────────────────┘    │    │
│  │   TELEGRAM API         │         │                              │    │
│  │   (External Service)   │         │  ┌─────────────────────┐    │    │
│  │                        │         │  │  Agent Subgraphs    │    │    │
│  │  • Message Delivery    │         │  │  (Run in Parallel)  │    │    │
│  │  • Message Retrieval   │         │  │                     │    │    │
│  │  • Authentication      │         │  │ • Trigger Analysis  │    │    │
│  │  • Reactions/Typing    │         │  │ • Decision Making   │    │    │
│  └────────────────────────┘         │  │ • Text Generation   │    │    │
│                                      │  │ • Style Application │    │    │
│                                      │  │ • Validation Loop   │    │    │
│                                      │  └─────────────────────┘    │    │
│                                      └─────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Service Components

### Telegram2 Service

**Technology Stack:**
- **Runtime**: Node.js 20 (Alpine Linux)
- **Language**: TypeScript
- **Framework**: Express.js
- **Telegram Library**: GramJS (MTProto implementation)

**Purpose:**  
Telegram2 acts as a **stateless REST API gateway** that abstracts Telegram's complex MTProto protocol into simple HTTP endpoints. It maintains authenticated sessions and provides a clean interface for the LangGraph service to interact with Telegram.

#### Directory Structure

```
telegram2/
├── src/
│   ├── server.ts                 # Express server setup & lifecycle
│   ├── vars.ts                   # Environment variable configuration
│   │
│   ├── routes/                   # API endpoint definitions
│   │   ├── index.ts              # Route aggregation
│   │   ├── authRoutes.ts         # Authentication endpoints
│   │   ├── messageRoutes.ts      # Send/receive messages
│   │   ├── chatMessagesRoutes.ts # Fetch chat history
│   │   ├── chatsRoutes.ts        # List chats
│   │   ├── chatParticipantsRoutes.ts # Group member info
│   │   ├── reactionRoutes.ts     # Add emoji reactions
│   │   ├── typingRoutes.ts       # Typing indicators
│   │   └── pollRoutes.ts         # Poll interactions
│   │
│   ├── services/                 # Business logic layer
│   │   ├── sessionManager.ts     # Manage GramJS client instances
│   │   ├── sessionLoader.ts      # Auto-load saved sessions
│   │   ├── messageService.ts     # Send message logic
│   │   ├── chatMessagesService.ts # Fetch & search messages
│   │   ├── chatsService.ts       # List & filter chats
│   │   ├── chatParticipantsService.ts # Fetch group members
│   │   ├── reactionService.ts    # Add reactions to messages
│   │   ├── typingService.ts      # Show typing indicators
│   │   ├── entityResolver.ts     # Resolve usernames/IDs to entities
│   │   └── authErrorHandler.ts   # Handle auth errors
│   │
│   ├── types/                    # TypeScript type definitions
│   │   ├── index.ts
│   │   ├── chats.ts
│   │   ├── messages.ts
│   │   ├── phone.ts
│   │   ├── polls.ts
│   │   └── gramjs.d.ts          # GramJS type declarations
│   │
│   └── utils/                    # Helper utilities
│       ├── logger.ts             # Winston logging
│       ├── validators.ts         # Input validation
│       ├── phoneStorage.ts       # Session file persistence
│       ├── chatMessage.ts        # Message transformation
│       └── reactionExtractor.ts  # Extract reaction details
│
├── data/                         # Session storage (mounted volume)
│   └── phone_+37379276083.json   # Example session file
│
├── Dockerfile                    # Production build (multi-stage)
├── package.json                  # Dependencies & scripts
└── tsconfig.json                 # TypeScript configuration
```

#### Key Features

1. **Session Management**
   - Maintains authenticated GramJS clients in memory
   - Persists session data to JSON files
   - Auto-loads sessions on startup (`AUTO_LOAD_SESSIONS=true`)
   - Graceful connection/disconnection handling

2. **API Endpoints**
   - **Authentication**: Send/verify codes for phone login
   - **Messages**: Send text, replies, fetch history
   - **Chats**: List all chats, filter groups/channels
   - **Participants**: Get group member information
   - **Reactions**: Add emoji reactions by timestamp
   - **Typing**: Show realistic typing indicators
   - **Polls**: Fetch polls and submit votes

3. **Reliability Features**
   - Connection retry logic (configurable retries)
   - Health check endpoint for Docker monitoring
   - Graceful shutdown (disconnects all sessions)
   - Comprehensive error handling & logging

4. **Message Resolution**
   - Converts timestamps to message IDs for replies/reactions
   - Resolves usernames/phone numbers to Telegram entities
   - Fetches detailed reaction information with user lists

---

### LangGraph Service

**Technology Stack:**
- **Language**: Python 3.11+
- **Framework**: LangGraph (state machine orchestration)
- **LLM Integration**: OpenAI GPT-4/GPT-4o-mini
- **Monitoring**: Logfire (observability platform)

**Purpose:**  
LangGraph orchestrates the AI agent system using a hierarchical state machine. It analyzes Telegram conversations, determines when and how agents should respond, generates contextual responses, and executes actions through the Telegram2 API.

#### Directory Structure

```
langgraph/
├── run_supervisor.py             # Main entry point (polling loop)
├── build_graph.py                # Graph construction & compilation
├── telegram_exm.py               # Telegram2 API wrapper functions
├── utils.py                      # Helper utilities
├── auth.py                       # Telegram authentication helpers
│
├── states/                       # State definitions
│   ├── supervisor_state.py       # SupervisorState (global)
│   └── agent_state.py            # AgentState (per-agent)
│
├── nodes/                        # Graph node implementations
│   ├── supervisor/               # Supervisor graph nodes
│   │   ├── component_B.py        # Emotion analysis
│   │   ├── component_C.py        # Participant personality analysis
│   │   ├── scheduler.py          # Build execution queue
│   │   └── executor.py           # Execute actions via Telegram2
│   │
│   └── agent/                    # Agent subgraph nodes
│       ├── orchestrator.py       # Central routing logic
│       ├── trigger_analysis.py   # Detect conversation triggers
│       ├── decision_maker.py     # Select appropriate action
│       ├── component_E1.py       # Generate response content
│       ├── component_E2.py       # Apply persona styling
│       └── validator.py          # Validate response quality
│
├── config/                       # Configuration files
│   ├── supervisor_config.json    # Main system config
│   └── model_config.json         # LLM model settings per component
│
├── agents_personas/              # Agent personality definitions
│   ├── agent_template.json       # Template structure
│   ├── sandra_persona.json       # Active agent (Samsung advocate)
│   ├── victor_persona.json       # Off-radar agent (quiet observer)
│   ├── tamar_persona.json        # Example persona
│   └── [others...]
│
├── triggers/                     # Trigger definitions by agent type
│   ├── active/
│   │   └── active_triggers.json  # Triggers for active agents
│   ├── chaos/
│   │   └── chaos_triggers.json   # Triggers for chaos agents
│   └── off_radar/
│       └── off_radar_triggers.json # Triggers for quiet agents
│
├── actions/                      # Action definitions by agent type
│   ├── active/
│   │   └── active_actions.json   # Actions for active agents
│   ├── chaos/
│   └── off_radar/
│
├── prompts/                      # LLM prompt templates
│   ├── agent_graph/              # Agent subgraph prompts
│   │   ├── trigger_analysis/
│   │   ├── decision_maker/
│   │   ├── E1/                   # Text generation prompts
│   │   ├── E2/                   # Styling prompts
│   │   └── validator/
│   │
│   ├── agent_types/              # Agent type system prompts
│   │   ├── active_prompt.txt
│   │   ├── chaos_prompt.txt
│   │   └── off_radar_prompt.txt
│   │
│   └── supervisor_graph/         # Supervisor node prompts
│       ├── component_B/
│       └── component_C/
│
├── memory/                       # Data persistence layer
│   ├── __init__.py
│   ├── storage.py                # File-based storage
│   ├── group.py                  # Group history management
│   ├── participant.py            # Participant tracking
│   ├── actions.py                # Action history
│   └── examples/                 # Example usage scripts
│
├── logs/                         # Logging configuration
│   ├── logfire_config.py         # Logfire setup
│   └── README.md
│
├── data/                         # Runtime data storage
│   └── 3389864729/               # Chat-specific data
│       ├── group_history.json    # Message history
│       ├── group_metadata.json   # Group info
│       ├── actions/              # Agent action logs
│       │   ├── SandraK9.json
│       │   └── Victor.json
│       └── participant/          # User profiles
│           ├── 526622223.json
│           └── [others...]
│
└── tests/                        # Unit tests
    ├── test_component_B.py
    ├── test_trigger_analysis.py
    ├── test_decision_maker.py
    └── [others...]
```

#### Key Components

1. **Polling System** (`run_supervisor.py`)
   - Polls Telegram2 every 60 seconds for new messages
   - Maintains deduplication queue (last 1000 message IDs)
   - Filters out agent-sent messages
   - Invokes supervisor graph when new messages arrive

2. **Supervisor Graph**
   - **Component B**: Enriches messages with emotion analysis
   - **Agent Nodes**: Runs all agent subgraphs in parallel
   - **Scheduler**: Builds execution queue from agent outputs
   - **Executor**: Sends actions to Telegram2 API

3. **Agent Subgraphs** (One per agent)
   - **Orchestrator**: Routes between components
   - **Trigger Analysis**: Detects relevant conversation patterns
   - **Decision Maker**: Selects appropriate action
   - **Text Generator (E1)**: Creates response content
   - **Styler (E2)**: Applies persona-specific style
   - **Validator**: Quality control with retry loop

4. **Configuration System**
   - `supervisor_config.json`: Chat ID, polling intervals, agent roster
   - `model_config.json`: LLM models per component
   - Agent personas: Personality, writing style, background
   - Triggers: Conversation patterns to detect
   - Actions: Available response types

---

## Communication Flow

### 1. Service-to-Service Communication

**Protocol**: HTTP REST  
**Direction**: LangGraph → Telegram2 (one-way)  
**Network**: Docker Compose internal network  

```
┌─────────────────────────────────────────────────────────────────────┐
│                     COMMUNICATION PATTERN                            │
│                                                                      │
│  LangGraph Service                     Telegram2 Service             │
│  ┌─────────────────┐                  ┌──────────────────┐         │
│  │ run_supervisor  │                  │   Express Server │         │
│  │     .py         │                  │   (Port 4000)    │         │
│  │                 │                  │                  │         │
│  │  Every 60s:     │    HTTP GET      │  Endpoint:       │         │
│  │  Fetch Messages │─────────────────►│  /api/chat-      │         │
│  │                 │  telegram2:4000  │   messages       │         │
│  │                 │                  │                  │         │
│  │                 │◄─────────────────│  Returns: JSON   │         │
│  │                 │  Response: Array │  {success, msgs} │         │
│  │                 │  of Messages     │                  │         │
│  └─────────────────┘                  └──────────────────┘         │
│          │                                      ▲                   │
│          │ Process through                     │                   │
│          │ LangGraph                            │                   │
│          ▼                                      │                   │
│  ┌─────────────────┐                           │                   │
│  │   Executor      │      HTTP POST            │                   │
│  │   Node          │──────────────────────────►│  Endpoint:        │
│  │                 │  telegram2:4000           │  /api/messages/   │
│  │  Actions:       │                           │   send            │
│  │  • Send Message │                           │                   │
│  │  • Add Reaction │  HTTP POST                │  Endpoint:        │
│  │  • Show Typing  │──────────────────────────►│  /api/reactions   │
│  │                 │                           │                   │
│  │                 │  HTTP POST                │  Endpoint:        │
│  │                 │──────────────────────────►│  /api/typing      │
│  └─────────────────┘                           └──────────────────┘
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. API Endpoints Used

#### Fetching Messages

**Endpoint**: `GET /api/chat-messages`  
**Caller**: `run_supervisor.py` → `get_chat_messages()`  
**Frequency**: Every 60 seconds  

```python
# langgraph/telegram_exm.py
def get_chat_messages(phone=None, chat_id=None, limit=100):
    phone_encoded = phone.replace("+", "%2B")
    url = f"http://telegram2:4000/api/chat-messages?phone={phone_encoded}&chatId={chat_id}&limit={limit}"
    response = requests.get(url)
    return response.json()
```

**Request:**
```http
GET /api/chat-messages?phone=%2B37379276083&chatId=3389864729&limit=12
```

**Response:**
```json
{
  "success": true,
  "chatId": "3389864729",
  "chatTitle": "Petach Tikva Group",
  "messagesCount": 12,
  "messages": [
    {
      "id": 12345,
      "senderId": "123456789",
      "senderUsername": "john_doe",
      "senderFirstName": "John",
      "senderLastName": "Doe",
      "text": "I love my new iPhone!",
      "date": "2025-12-29T10:30:00.000Z",
      "reactions": [
        {
          "emoji": "👍",
          "count": 2,
          "users": [{"firstName": "Alice", "username": "alice"}]
        }
      ]
    }
  ]
}
```

#### Sending Messages

**Endpoint**: `POST /api/messages/send`  
**Caller**: `executor.py` → `send_telegram_message()`  

```python
# langgraph/telegram_exm.py
def send_telegram_message(from_phone, to_target, content_value, reply_to_timestamp=None):
    url = f"http://telegram2:4000/api/messages/send"
    payload = {
        "fromPhone": from_phone,
        "toTarget": to_target,
        "content": {"type": "text", "value": content_value}
    }
    if reply_to_timestamp:
        payload["replyToTimestamp"] = reply_to_timestamp
    
    response = requests.post(url, json=payload)
    return response.json()
```

**Request:**
```json
POST /api/messages/send
{
  "fromPhone": "+37379276083",
  "toTarget": "3389864729",
  "content": {
    "type": "text",
    "value": "Samsung has better customization!"
  },
  "replyToTimestamp": "2025-12-29T10:30:00.000Z"
}
```

**Response:**
```json
{
  "success": true,
  "sentTo": "Petach Tikva Group",
  "messageId": 12346
}
```

#### Adding Reactions

**Endpoint**: `POST /api/reactions`  
**Caller**: `executor.py` → `add_reaction_to_message()`  

```python
# langgraph/telegram_exm.py
def add_reaction_to_message(phone, chat_id, message_timestamp, emoji):
    url = f"http://telegram2:4000/api/reactions"
    payload = {
        "phone": phone,
        "chatId": chat_id,
        "messageTimestamp": message_timestamp,
        "emoji": emoji
    }
    response = requests.post(url, json=payload)
    return response.json()
```

**Request:**
```json
POST /api/reactions
{
  "phone": "+37379276083",
  "chatId": "3389864729",
  "messageTimestamp": "2025-12-29T10:30:00.000Z",
  "emoji": "👍"
}
```

#### Showing Typing Indicators

**Endpoint**: `POST /api/typing`  
**Caller**: `executor.py` → `show_typing_indicator()`  

```python
def show_typing_indicator(phone, chatId, duration):
    url = f"http://telegram2:4000/api/typing"
    payload = {
        "phone": phone,
        "chatId": chatId,
        "duration": duration  # milliseconds
    }
    response = requests.post(url, json=payload)
    return response.json()
```

**Request:**
```json
POST /api/typing
{
  "phone": "+37379276083",
  "chatId": "3389864729",
  "duration": 5000
}
```

#### Fetching Group Participants

**Endpoint**: `GET /api/participants`  
**Caller**: `run_supervisor.py` → `get_all_group_participants()`  

```python
def get_all_group_participants(phone, chat_id):
    phone_encoded = phone.replace("+", "%2B")
    url = f"http://telegram2:4000/api/participants?phone={phone_encoded}&chatId={chat_id}"
    response = requests.get(url)
    return response.json()
```

**Response:**
```json
{
  "success": true,
  "chatId": "3389864729",
  "chatTitle": "Petach Tikva Group",
  "participantsCount": 15,
  "participants": [
    {
      "userId": "123456789",
      "firstName": "John",
      "lastName": "Doe",
      "username": "john_doe",
      "isBot": false,
      "isSelf": false
    }
  ]
}
```

---

## Deployment Architecture

### Docker Compose Configuration

```yaml
# docker-compose.yml
services:
  telegram2:
    build: ./telegram2
    image: telegram2:0.1.0
    ports:
      - "4000:4000"
    volumes:
      - ./volumes/telegram2:/app/data
    environment:
      - NODE_ENV=production
      - PORT=4000
      - AUTO_LOAD_SESSIONS=true
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:4000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  langgraph:
    image: langgraph:0.1.8
    env_file:
      - ./langgraph/.env
    environment:
      - TELEGRAM_PORT=4000
      - TELEGRAM_HOST=telegram2  # Docker network hostname
    depends_on:
      telegram2:
        condition: service_healthy
```

### Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         Docker Compose Default Bridge Network               │
│                                                              │
│  ┌──────────────────┐                 ┌─────────────────┐  │
│  │   telegram2      │                 │   langgraph     │  │
│  │   Container      │                 │   Container     │  │
│  │                  │                 │                 │  │
│  │   Internal IP:   │◄───────────────┤   TELEGRAM_HOST │  │
│  │   172.x.x.2      │   Resolves to  │   =telegram2    │  │
│  │                  │                 │                 │  │
│  │   Hostname:      │                 │   TELEGRAM_PORT │  │
│  │   telegram2      │                 │   =4000         │  │
│  └──────────────────┘                 └─────────────────┘  │
│          │                                                   │
│          │ Port Mapping                                     │
│          │ 4000:4000                                        │
│          ▼                                                   │
│  ┌──────────────────┐                                       │
│  │   Host Machine   │                                       │
│  │   localhost:4000 │                                       │
│  └──────────────────┘                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Volume Mounts

**Telegram2 Session Persistence:**
```
Host: ./volumes/telegram2/
Container: /app/data/

Files:
- phone_+37379276083.json (Tamar's session)
- phone_+1234567890.json (Other agents)
```

**Why Volume Mounting is Critical:**
- Sessions contain authentication tokens
- Without volumes, agents must re-authenticate after container restart
- Telegram has rate limits on authentication requests
- Sessions enable instant reconnection

---

## Data Flow

### Complete Message Processing Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                      TELEGRAM ECOSYSTEM                               │
│  User sends message: "I love my new iPhone!"                         │
│  Message stored on Telegram servers                                  │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    TELEGRAM2 SERVICE (Always Ready)                   │
│  • Maintains persistent connection to Telegram                       │
│  • Session authenticated for phone: +37379276083                     │
│  • Waiting for API requests from LangGraph                           │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH POLLING LOOP                             │
│  run_supervisor.py - Main Loop (60s interval)                        │
│                                                                       │
│  STEP 1: Fetch Messages                                              │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ messages = get_chat_messages(                              │     │
│  │     phone="+37379276083",                                  │     │
│  │     chat_id="3389864729",                                  │     │
│  │     limit=12                                               │     │
│  │ )                                                          │     │
│  └────────────────────────────────────────────────────────────┘     │
│                              │                                        │
│                              ▼                                        │
│  STEP 2: Filter New Messages                                         │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ for msg in messages:                                       │     │
│  │     if msg['message_id'] not in seen_message_ids:         │     │
│  │         new_messages.append(msg)                           │     │
│  │         seen_message_ids.append(msg['message_id'])         │     │
│  └────────────────────────────────────────────────────────────┘     │
│                              │                                        │
│                              ▼                                        │
│  STEP 3: Filter Agent Messages                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ for msg in new_messages:                                   │     │
│  │     if is_agent_message(msg, agent_personas):              │     │
│  │         msg['processed'] = True  # Skip own messages       │     │
│  └────────────────────────────────────────────────────────────┘     │
│                              │                                        │
│                              ▼                                        │
│  STEP 4: Check if Action Needed                                      │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ unprocessed = [m for m in new_messages                     │     │
│  │                if not m.get('processed')]                  │     │
│  │                                                            │     │
│  │ if unprocessed:                                            │     │
│  │     state = graph.invoke(state)  # Run supervisor graph   │     │
│  └────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    SUPERVISOR GRAPH EXECUTION                         │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ Component B: Emotion Analysis                              │     │
│  │                                                            │     │
│  │ Input: recent_messages (unclassified)                     │     │
│  │ Process: LLM analyzes each message                        │     │
│  │ Output:                                                    │     │
│  │   message['message_emotion'] = "Very positive about       │     │
│  │                                  iPhone purchase"          │     │
│  │   group_sentiment = "Enthusiastic tech discussion"        │     │
│  └────────────────────────────────────────────────────────────┘     │
│                              │                                        │
│                              ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ Agent Execution (Parallel)                                 │     │
│  │                                                            │     │
│  │ For each agent: Sandra, Victor                            │     │
│  │   Run Agent Subgraph ──────────────────────┐              │     │
│  └────────────────────────────────────────────┼──────────────┘     │
│                                               │                      │
│         ┌─────────────────────────────────────┘                      │
│         │                                                            │
│         ▼                                                            │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ SANDRA'S AGENT SUBGRAPH                                    │     │
│  │                                                            │     │
│  │ 1. Trigger Analysis                                        │     │
│  │    ├─ Input: recent_messages, triggers.json               │     │
│  │    ├─ LLM: "Detect Samsung vs Apple trigger?"             │     │
│  │    └─ Output: detected_trigger = {                        │     │
│  │         "id": "samsung_vs_apple_debate",                  │     │
│  │         "justification": "User praised iPhone",           │     │
│  │         "target_message": {...}                           │     │
│  │       }                                                    │     │
│  │                                                            │     │
│  │ 2. Decision Maker                                          │     │
│  │    ├─ Input: detected_trigger, actions.json               │     │
│  │    ├─ LLM: "Choose action from suggested_actions"         │     │
│  │    └─ Output: selected_action = {                         │     │
│  │         "id": "send_message",                             │     │
│  │         "purpose": "Challenge iPhone enthusiasm"          │     │
│  │       }                                                    │     │
│  │                                                            │     │
│  │ 3. Text Generator (E1)                                     │     │
│  │    ├─ Input: action, persona, context                     │     │
│  │    ├─ LLM: "Generate response content"                    │     │
│  │    └─ Output: generated_response =                        │     │
│  │         "Have you tried Samsung's latest Galaxy?          │     │
│  │          The customization is incredible..."              │     │
│  │                                                            │     │
│  │ 4. Styler (E2)                                             │     │
│  │    ├─ Input: generated_response, persona.style            │     │
│  │    ├─ LLM: "Apply Sandra's writing patterns"              │     │
│  │    └─ Output: styled_response =                           │     │
│  │         "omg have u tried Samsung's latest Galaxy tho?    │     │
│  │          the customization is incredibleee 📱✨"          │     │
│  │                                                            │     │
│  │ 5. Validator                                               │     │
│  │    ├─ Input: styled_response, agent_goal                  │     │
│  │    ├─ LLM: "Does this meet quality standards?"            │     │
│  │    └─ Output: validation = {                              │     │
│  │         "approved": true,                                 │     │
│  │         "justification": "Playful & on-topic"             │     │
│  │       }                                                    │     │
│  │                                                            │     │
│  │ 6. Return to Supervisor                                    │     │
│  │    └─ Command(update={"selected_actions": [{              │     │
│  │         "agent_name": "Sandra",                           │     │
│  │         "action_id": "send_message",                      │     │
│  │         "action_content": "omg have u tried...",          │     │
│  │         "phone_number": "+37379276083",                   │     │
│  │         "target_message": {...}                           │     │
│  │       }]})                                                 │     │
│  └────────────────────────────────────────────────────────────┘     │
│                              │                                        │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ VICTOR'S AGENT SUBGRAPH                                    │     │
│  │                                                            │     │
│  │ 1. Trigger Analysis                                        │     │
│  │    └─ Output: detected_trigger = {"id": "neutral"}        │     │
│  │                                                            │     │
│  │ 2. Orchestrator: Return END (no action)                   │     │
│  └────────────────────────────────────────────────────────────┘     │
│                              │                                        │
│                              ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ Scheduler: Build Execution Queue                           │     │
│  │                                                            │     │
│  │ Input: selected_actions = [Sandra's action]               │     │
│  │ Process: Filter & format for execution                    │     │
│  │ Output: execution_queue = [                               │     │
│  │   {                                                        │     │
│  │     "agent_name": "Sandra",                               │     │
│  │     "action_id": "send_message",                          │     │
│  │     "action_content": "omg have u tried...",              │     │
│  │     "phone_number": "+37379276083",                       │     │
│  │     "target_message": {                                   │     │
│  │       "timestamp": "2025-12-29T10:30:00.000Z",            │     │
│  │       "text": "I love my new iPhone!"                     │     │
│  │     },                                                     │     │
│  │     "status": "pending"                                   │     │
│  │   }                                                        │     │
│  │ ]                                                          │     │
│  └────────────────────────────────────────────────────────────┘     │
│                              │                                        │
│                              ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ Executor: Send to Telegram                                 │     │
│  │                                                            │     │
│  │ For each action in execution_queue:                       │     │
│  │                                                            │     │
│  │ STEP 1: Show Typing Indicator                             │     │
│  │ ┌──────────────────────────────────────────────────────┐  │     │
│  │ │ typing_duration = calculate_duration(content)        │  │     │
│  │ │ show_typing_indicator(                               │  │     │
│  │ │     phone="+37379276083",                            │  │     │
│  │ │     chatId="3389864729",                             │  │     │
│  │ │     duration=5000  # 5 seconds                       │  │     │
│  │ │ )                                                    │  │     │
│  │ └──────────────────────────────────────────────────────┘  │     │
│  │   ─────► HTTP POST to telegram2:4000/api/typing           │     │
│  │                                                            │     │
│  │ STEP 2: Send Message                                       │     │
│  │ ┌──────────────────────────────────────────────────────┐  │     │
│  │ │ send_telegram_message(                               │  │     │
│  │ │     from_phone="+37379276083",                       │  │     │
│  │ │     to_target="3389864729",                          │  │     │
│  │ │     content_value="omg have u tried...",             │  │     │
│  │ │     reply_to_timestamp="2025-12-29T10:30:00.000Z"    │  │     │
│  │ │ )                                                    │  │     │
│  │ └──────────────────────────────────────────────────────┘  │     │
│  │   ─────► HTTP POST to telegram2:4000/api/messages/send    │     │
│  │                                                            │     │
│  │ STEP 3: Clear Queue                                        │     │
│  │ ┌──────────────────────────────────────────────────────┐  │     │
│  │ │ execution_queue = []                                 │  │     │
│  │ │ selected_actions = []                                │  │     │
│  │ └──────────────────────────────────────────────────────┘  │     │
│  └────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    TELEGRAM2 SERVICE PROCESSING                       │
│                                                                       │
│  POST /api/messages/send received                                    │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ messageService.sendMessage()                               │     │
│  │                                                            │     │
│  │ 1. Validate phone & target                                │     │
│  │ 2. Get authenticated client for +37379276083              │     │
│  │ 3. Resolve timestamp to message ID                        │     │
│  │    ├─ chatMessagesService.findMessageIdByTimestamp()     │     │
│  │    ├─ Fetch messages around timestamp                    │     │
│  │    └─ Match exact timestamp → messageId = 12345          │     │
│  │ 4. Resolve entity for chat "3389864729"                  │     │
│  │ 5. Send via GramJS:                                       │     │
│  │    client.sendMessage(entity, {                           │     │
│  │        message: "omg have u tried...",                    │     │
│  │        replyTo: 12345                                     │     │
│  │    })                                                      │     │
│  │ 6. Return success with new messageId                     │     │
│  └────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    TELEGRAM SERVERS                                   │
│  Message delivered to group chat                                     │
│  Users see:                                                          │
│    Sandra: omg have u tried Samsung's latest Galaxy tho?            │
│            the customization is incredibleee 📱✨                    │
│            ↳ Replying to: "I love my new iPhone!"                   │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    NEXT POLLING CYCLE (60s later)                     │
│  Sandra's message is fetched, marked as processed                    │
│  Cycle continues...                                                  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## API Integration

### Environment Configuration

**LangGraph Service** (`.env` file):
```env
# Telegram2 Service Connection
TELEGRAM_HOST=telegram2        # Docker service name
TELEGRAM_PORT=4000             # Internal port

# OpenAI API
OPENAI_API_KEY=sk-...

# Logfire Monitoring
LOGFIRE_TOKEN=...
```

**Telegram2 Service** (environment variables):
```env
# Telegram API Credentials
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abc123...

# Server Configuration
PORT=4000
NODE_ENV=production
AUTO_LOAD_SESSIONS=true

# Data Persistence
DATA_DIR=/app/data
```

### API Wrapper Layer

**File**: `langgraph/telegram_exm.py`

This module provides Python wrapper functions for all Telegram2 endpoints:

```python
# Connection configuration
TELEGRAM_HOST = os.environ.get('TELEGRAM_HOST', 'localhost')
TELEGRAM_PORT = os.environ.get('TELEGRAM_PORT', '4000')
TELEGRAM_API_URL = f"http://{TELEGRAM_HOST}:{TELEGRAM_PORT}"

# Wrapper functions
def get_chat_messages(phone, chat_id, limit):
    """Fetch chat messages from Telegram2 API"""
    
def send_telegram_message(from_phone, to_target, content_value, reply_to_timestamp):
    """Send message via Telegram2 API"""
    
def add_reaction_to_message(phone, chat_id, message_timestamp, emoji):
    """Add emoji reaction via Telegram2 API"""
    
def show_typing_indicator(phone, chatId, duration):
    """Show typing indicator via Telegram2 API"""
    
def get_all_group_participants(phone, chat_id):
    """Fetch group participants via Telegram2 API"""
```

### Error Handling

**LangGraph Side:**
```python
try:
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()
except requests.RequestException as e:
    logger.error(f"Error sending message: {e}")
    return {"success": False, "error": str(e)}
```

**Telegram2 Side:**
```typescript
try {
    const result = await sendMessage(phone, target, content);
    res.json({ success: true, ...result });
} catch (err) {
    if (err.message.includes('No authenticated session')) {
        return res.status(401).json({ success: false, error: err.message });
    }
    res.status(500).json({ success: false, error: err.message });
}
```

---

## State Management

### SupervisorState (Global State)

**Definition**: `langgraph/states/supervisor_state.py`

```python
class SupervisorState(TypedDict):
    # Message History
    recent_messages: List[Message]    # Messages from Telegram (enriched)
    
    # Group Context
    group_sentiment: str              # 2-3 sentence mood summary
    group_metadata: dict              # {id, name, topic, members}
    
    # Action Tracking
    selected_actions: List[dict]      # Actions from all agents
    execution_queue: List[dict]       # Actions ready to execute
    
    # Routing
    current_nodes: Optional[List[str]]
    next_nodes: Optional[List[str]]
```

**State Flow:**
1. `run_supervisor.py` initializes state
2. Component B enriches `recent_messages` with emotions
3. Agents append to `selected_actions`
4. Scheduler builds `execution_queue`
5. Executor clears queue after sending

### AgentState (Per-Agent State)

**Definition**: `langgraph/states/agent_state.py`

```python
class AgentState(TypedDict):
    # Copied from Supervisor
    recent_messages: List[Message]
    group_sentiment: str
    group_metadata: dict
    
    # Agent Configuration
    selected_persona: dict            # From persona JSON
    agent_type: str                   # "active", "chaos", "off_radar"
    agent_goal: str                   # From config
    triggers: dict                    # From triggers JSON
    actions: dict                     # From actions JSON
    agent_prompt: str                 # System prompt
    
    # Processing Outputs
    detected_trigger: Optional[dict]
    selected_action: Optional[dict]
    generated_response: Optional[str]
    styled_response: Optional[str]
    validation: Optional[dict]
    retry_count: int
    
    # Routing
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
    timestamp: str                    # ISO format from Telegram2
    reactions: Optional[List[dict]]   # Emoji reactions with users
    message_emotion: Optional[str]    # Added by Component B
    processed: Optional[bool]         # Deduplication flag
    replyToMessageId: Optional[int]   # For threaded replies
```

---

## Agent System

### Agent Types

1. **Active Agents**
   - **Goal**: Spark debates, engage actively
   - **Example**: Sandra (Samsung advocate)
   - **Behavior**: Frequent participation, opinionated responses

2. **Chaos Agents**
   - **Goal**: Disrupt patterns, introduce randomness
   - **Behavior**: Unpredictable timing, tangential topics

3. **Off-Radar Agents**
   - **Goal**: Minimal presence, blend into background
   - **Example**: Victor (quiet observer)
   - **Behavior**: Short messages, rare participation

### Trigger-Action System

**Triggers** (`triggers/{type}/{type}_triggers.json`):
```json
{
  "samsung_vs_apple_debate": {
    "id": "samsung_vs_apple_debate",
    "description": "Activated when iPhone/Apple products are mentioned",
    "indicators": [
      "User mentions iPhone, Apple, iOS positively",
      "Comparison between phone brands",
      "Discussion about tech ecosystems"
    ],
    "suggested_actions": ["send_message", "add_reaction"]
  }
}
```

**Actions** (`actions/{type}/{type}_actions.json`):
```json
{
  "send_message": {
    "id": "send_message",
    "description": "Send a text message to the group",
    "type": "message"
  },
  "add_reaction": {
    "id": "add_reaction",
    "description": "Add emoji reaction to a message",
    "type": "reaction"
  }
}
```

### Persona Configuration

**Example**: `agents_personas/sandra_persona.json`

```json
{
  "phone_number": "+37379276083",
  "user_name": "SandraK9",
  "first_name": "Sandra",
  "last_name": "Klein",
  "age": 28,
  "occupation": "Software Developer",
  "personality": {
    "traits": [
      "Tech-savvy and opinionated about Android",
      "Enthusiastic about customization",
      "Dislikes restrictive ecosystems"
    ]
  },
  "writing_style": {
    "patterns": [
      "Uses 'lol', 'omg', 'tho' frequently",
      "Multiple vowel repetition: 'sooo', 'amazinggg'",
      "Emoji usage: 📱✨💯",
      "Casual capitalization"
    ]
  }
}
```

---

## Security & Authentication

### Telegram Authentication Flow

**Initial Setup** (One-time per phone number):

1. **Send Verification Code**
   ```bash
   POST /api/auth/send-code
   {
     "phone": "+37379276083",
     "apiId": 25872607,
     "apiHash": "d6b4e90157370c68eefd02872c165541"
   }
   ```

2. **Receive SMS Code** (User receives from Telegram)

3. **Verify Code**
   ```bash
   POST /api/auth/verify-code
   {
     "phone": "+37379276083",
     "code": "12345"
   }
   ```

4. **Session Created**
   - GramJS creates session file
   - Saved to: `data/phone_+37379276083.json`
   - Contains encrypted auth tokens

5. **Auto-Load on Restart**
   - Docker volume persists session files
   - `AUTO_LOAD_SESSIONS=true` reconnects automatically

### Session Security

**Session Files** (`data/phone_*.json`):
```json
{
  "sessionData": "encrypted_auth_token...",
  "dcId": 2,
  "port": 443,
  "serverAddress": "149.154.167.51"
}
```

**Important Security Notes:**
- Session files are **sensitive** - treat like passwords
- Never commit to version control (`.gitignore`)
- Volume mount ensures persistence without exposure
- Sessions expire if unused for extended periods

### API Key Management

**LangGraph** (`.env`):
```env
OPENAI_API_KEY=sk-proj-...
LOGFIRE_TOKEN=...
```

**Telegram2** (environment variables):
```env
TELEGRAM_API_ID=12345678        # From my.telegram.org
TELEGRAM_API_HASH=abc123...     # From my.telegram.org
```

---

## Monitoring & Logging

### Logfire Integration (LangGraph)

**Setup**: `langgraph/logs/logfire_config.py`

```python
import logfire

def setup_logfire(service_name: str):
    logfire.configure(
        service_name=service_name,
        token=os.environ.get("LOGFIRE_TOKEN")
    )
    
def get_logger(name: str):
    return logfire.get_logger(name)
```

**Usage Throughout System:**
```python
from logs.logfire_config import get_logger

logger = get_logger(__name__)

# Structured logging
logger.info("Message sent", {
    "agent_name": "Sandra",
    "action_id": "send_message",
    "chat_id": "3389864729"
})
```

**Logged Events:**
- Message fetching & parsing
- Agent graph execution
- Trigger detections
- Action selections
- Message generation
- Validation results
- Telegram API calls
- Errors & exceptions

### Winston Logging (Telegram2)

**Setup**: `telegram2/src/utils/logger.ts`

```typescript
import winston from 'winston';

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'error.log', level: 'error' })
  ]
});
```

**Logged Events:**
- API requests & responses
- GramJS operations
- Session connect/disconnect
- Message send/receive
- Error conditions
- Authentication events

### Health Monitoring

**Docker Health Check**:
```yaml
healthcheck:
  test: ["CMD", "wget", "--spider", "http://localhost:4000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

**Health Endpoint** (`GET /health`):
```json
{
  "success": true,
  "version": "0.1.0",
  "environment": "production",
  "port": 4000
}
```

---

## Configuration Summary

### Critical Configuration Files

| File | Purpose | Key Settings |
|------|---------|--------------|
| `docker-compose.yml` | Service orchestration | Port mappings, volume mounts, dependencies |
| `langgraph/.env` | LangGraph environment | API keys, Telegram2 connection |
| `langgraph/config/supervisor_config.json` | Agent configuration | Chat ID, agents, polling intervals |
| `langgraph/config/model_config.json` | LLM settings | Models per component, temperature |
| `telegram2/.env` | Telegram2 environment | Telegram API credentials |
| `agents_personas/*.json` | Agent personalities | Traits, style, background |
| `triggers/*/*.json` | Conversation triggers | Detection patterns |
| `actions/*/*.json` | Available actions | Action definitions |

### Runtime Parameters

**Polling Configuration** (`supervisor_config.json`):
```json
{
  "polling": {
    "message_check_interval_seconds": 60,
    "telegram_fetch_limit": 12,
    "max_recent_messages": 12
  }
}
```

**LLM Configuration** (`model_config.json`):
```json
{
  "component_B": {
    "model": "gpt-4o-mini",
    "provider": "openai",
    "temperature": 0.3
  },
  "trigger_analysis": {
    "model": "gpt-4o",
    "temperature": 0.4
  }
}
```

---

## System Flow Summary

1. **Initialization**
   - Docker Compose starts both services
   - Telegram2 loads saved sessions
   - LangGraph builds supervisor & agent graphs

2. **Continuous Loop**
   - Every 60 seconds, LangGraph polls Telegram2
   - Fetches latest messages from target chat
   - Filters new, non-agent messages

3. **Message Processing**
   - Component B analyzes emotions
   - All agents run in parallel
   - Each agent checks triggers → selects action → generates response

4. **Execution**
   - Scheduler builds queue
   - Executor sends to Telegram2
   - Telegram2 forwards to Telegram servers

5. **Persistence**
   - Message history saved to `data/` directory
   - Agent actions logged
   - Sessions persist across restarts

---

## Dependencies Between Services

```
LangGraph DEPENDS ON Telegram2 for:
├─ Fetching messages (polling)
├─ Sending messages (execution)
├─ Adding reactions
├─ Showing typing indicators
└─ Fetching group metadata

Telegram2 DEPENDS ON External Telegram API for:
├─ Authentication
├─ Message delivery
├─ Message retrieval
└─ Real-time updates

Docker Compose ENSURES:
├─ Telegram2 starts first (healthcheck)
├─ LangGraph waits for healthy Telegram2
├─ Network connectivity between services
└─ Volume persistence for sessions
```

---

## Conclusion

This architecture creates a **robust, scalable, and maintainable** system for autonomous AI agents in Telegram groups. The microservices pattern allows independent development, deployment, and scaling of each component while maintaining clear separation of concerns:

- **Telegram2**: Handles all Telegram protocol complexity
- **LangGraph**: Orchestrates AI decision-making and agent behavior

The communication layer is simple HTTP REST, making it easy to debug, monitor, and extend with additional services in the future.
