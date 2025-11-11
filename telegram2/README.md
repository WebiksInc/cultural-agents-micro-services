# Telegram2 Service

A TypeScript microservice providing REST API access to Telegram's MTProto client capabilities using GramJS library.

## Overview

This service acts as a **stateless API gateway** to Telegram, designed to be called by other services (like LangGraph agents). It does NOT store any data - it simply fetches from Telegram and returns it. All data persistence should be handled by the calling service.

## Key Features

- **Authentication**: Phone verification with persistent session storage
- **Message Operations**: Send messages, fetch chat messages, get unread messages
-  **Chat Management**: List chats, get participants, filter groups/channels
-  **Poll Operations**: Fetch polls and vote on them
-  **Session Persistence**: Sessions survive server restarts
-  **Stateless Design**: No database - perfect for microservice architecture
-  **Clean Architecture**: Functional TypeScript with clear separation of concerns
-  **Entity Caching**: Automatically warms Telegram entity cache for reliable chat ID resolution



## Architecture

```
telegram2/
├── src/
│   ├── server.ts           # Express server & graceful shutdown
│   ├── vars.ts            # Environment configuration
│   ├── utils/
│   │   ├── logger.ts      # JSON logging utility
│   │   ├── phoneStorage.ts # Per-phone session files
│   │   └── validators.ts  # Input validation
│   ├── services/
│   │   ├── sessionManager.ts      # Session lifecycle management
│   │   ├── entityResolver.ts     # Smart Telegram entity caching
│   │   ├── sendCodeService.ts    # Send verification code
│   │   ├── verifyCodeService.ts  # Verify code & authenticate
│   │   ├── messageService.ts     # Send messages
│   │   ├── chatMessagesService.ts # Fetch chat messages
│   │   ├── chatParticipantsService.ts # Get chat members
│   │   ├── chatsService.ts       # List chats
│   │   ├── pollService.ts        # Fetch polls
│   │   ├── pollVoteService.ts    # Vote on polls
│   │   └── unreadService.ts      # Fetch unread messages
│   ├── routes/
│   │   ├── authRoutes.ts         # Authentication endpoints
│   │   ├── messageRoutes.ts      # Send messages
│   │   ├── chatMessagesRoutes.ts # Chat message history
│   │   ├── chatParticipantsRoutes.ts # Chat members
│   │   ├── chatsRoutes.ts        # List chats
│   │   ├── pollRoutes.ts         # Polls & voting
│   │   ├── unreadRoutes.ts       # Unread messages
│   │   └── index.ts              # Route aggregator
│   └── types/
│       ├── chats.ts              # Chat-related types
│       ├── messages.ts           # Message-related types
│       └── polls.ts              # Poll-related types
└── data/                  # Generated at runtime
    └── phone_+123.json    # Per-phone session storage
```

### Design Principles

- **Stateless**: No database - all data comes from Telegram API
- **Functional**: Pure functions, no classes/OOP
- **Type-Safe**: Full TypeScript with strict typing
- **Validated**: All inputs validated before processing
- **Logged**: JSON-formatted logs for easy parsing
- **Resilient**: Auto-reconnection and entity cache warming

## Running the Service

Install dependencies and start:

```bash
cd telegram2
npm install
npm run dev  # Development mode with hot reload
```

Or for production:

```bash
npm run build
npm start
```

Set `LOG_LEVEL=debug` for verbose logs.

## Setup

### Install Dependencies

```bash
cd telegram2
npm install
```

### Environment Variables Configuration



#### Available Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PORT` | number | `4000` | Port number for the HTTP server |
| `NODE_ENV` | string | `development` | Node.js environment (development/production) |
| `LOG_LEVEL` | string | `info` | Minimum log level: `debug`, `info`, `warn`, `error` |
| `DATA_DIR` | string | `./data` | Directory to store phone session files |
| `CONNECTION_RETRIES` | number | `3` | Number of connection retries for Telegram clients |
| `SHUTDOWN_TIMEOUT` | number | `10000` | Graceful shutdown timeout (milliseconds) |
| `AUTO_LOAD_SESSIONS` | boolean | `true` | Automatically load saved sessions on startup |
| `SESSION_CLEANUP_INTERVAL` | number | `3600000` | Session cleanup interval (milliseconds, 1h default) |
| `TELEGRAM_API_ID` | number | none | Optional: Default Telegram API ID (can be overridden per request) |
| `TELEGRAM_API_HASH` | string | none | Optional: Default Telegram API Hash (can be overridden per request) |

#### Environment Examples

**Development Environment:**
```bash
PORT=4000
NODE_ENV=development
LOG_LEVEL=debug
DATA_DIR=./data
AUTO_LOAD_SESSIONS=true
```



**Docker Environment:**
```bash
PORT=4000
NODE_ENV=production
LOG_LEVEL=warn
DATA_DIR=/app/sessions
AUTO_LOAD_SESSIONS=true
TELEGRAM_API_ID=12345
TELEGRAM_API_HASH=your_api_hash_here
```


#### Data Directory

The `DATA_DIR` variable controls where phone session files are stored:
- Relative paths are resolved from the project root
- Absolute paths are used as-is
- Directory is created automatically if it doesn't exist
- Files are named `phone_+1234567890.json`

#### Default API Credentials

If you set `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`, these will be used as defaults, but can still be overridden in individual API requests to `/api/auth/send-code`.

### Get Telegram API Credentials

1. Visit https://my.telegram.org
2. Log in with your phone number
3. Go to "API development tools"
4. Create an application
5. Copy your `api_id` and `api_hash`
6. (Optional) Add them to `.env` as defaults:
   ```bash
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   ```

## Running the Service

### Development Mode

```bash
npm run dev
```

### Production Mode

```bash
npm run build
npm start
```

Server runs on: `http://localhost:4000`

## API Endpoints

### Base URL
```
http://localhost:4000/api
```

All responses follow a consistent format with `success` boolean and either data or `error` message.

### Quick Reference

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/send-code` | Send verification code to phone | No |
| POST | `/api/auth/verify-code` | Verify code and authenticate | No |
| GET | `/api/auth/debug/active-sessions` | List active sessions | No |
| GET | `/api/chats/all` | Get all chats (users, groups, channels) | Yes |
| GET | `/api/chats/groups` | Get only groups and channels | Yes |
| GET | `/api/chat-messages` | Fetch message history from chat | Yes |
| GET | `/api/chat-participants` | Get all participants in chat | Yes |
| POST | `/api/messages/send` | Send message to target | Yes |
| GET | `/api/messages/unread` | Get unread messages (auto-marks read) | Yes |
| GET | `/api/polls` | Fetch polls from chat | Yes |
| POST | `/api/polls/vote` | Vote on a poll | Yes |
| GET | `/health` | Health check | No |

---

### Authentication

#### 1. Send Verification Code

Initiate authentication by sending a verification code to the phone number via Telegram.

**Endpoint:** `POST /api/auth/send-code`

**Request Body:**
```json
{
  "phone": "+1234567890",
  "apiId": 12345,
  "apiHash": "your_api_hash"
}
```

**Response (200):**
```json
{
  "success": true,
  "phoneCodeHash": "abc123def456..."
}
```

**Errors:**
- `500`: Invalid credentials or Telegram API error

**Call from another service (Python example):**
```python
import requests

response = requests.post(
    "http://localhost:4000/api/auth/send-code",
    json={
        "phone": "+1234567890",
        "apiId": 12345,
        "apiHash": "your_api_hash"
    }
)
data = response.json()
if data["success"]:
    print(f"Code sent! Hash: {data['phoneCodeHash']}")
```

---

#### 2. Verify Code

Complete authentication by verifying the code received on Telegram.

**Endpoint:** `POST /api/auth/verify-code`

**Request Body:**
```json
{
  "phone": "+1234567890",
  "code": "12345"
}
```

**Response (200):**
```json
{
  "success": true,
  "user": "John Doe"
}
```

**Errors:**
- `500`: Invalid code, expired code, or 2FA required

**Call from another service (Python example):**
```python
response = requests.post(
    "http://localhost:4000/api/auth/verify-code",
    json={
        "phone": "+1234567890",
        "code": "12345"
    }
)
```

---

#### 3. Get Active Sessions (Debug)

Check which phone numbers have active sessions.

**Endpoint:** `GET /api/auth/debug/active-sessions`

**Response (200):**
```json
{
  "success": true,
  "count": 2,
  "activePhones": ["+1234567890", "+9876543210"]
}
```

---

### Chats

#### 4. Get All Chats

Retrieve all chats (users, groups, channels, bots) for an authenticated account.

**Endpoint:** `GET /api/chats/all`

**Query Parameters:**
- `accountPhone` (required): URL-encoded phone number (e.g., `%2B1234567890`)

**Example Request:**
```
GET /api/chats/all?accountPhone=%2B1234567890
```

**Response (200):**
```json
{
  "success": true,
  "chats": {
    "John Doe": "123456789",
    "My Group": "987654321",
    "News Channel": "555555555"
  },
  "details": [
    {
      "id": "123456789",
      "name": "John Doe",
      "type": "user",
      "username": "johndoe"
    },
    {
      "id": "987654321",
      "name": "My Group",
      "type": "group",
      "username": null
    },
    {
      "id": "555555555",
      "name": "News Channel",
      "type": "channel",
      "username": "newschannel"
    }
  ]
}
```

**Types:**
- `user`: Direct message with a person
- `bot`: Telegram bot
- `group`: Group chat
- `channel`: Broadcast channel

**Errors:**
- `500`: Authentication or connection error

**Call from another service (Python example):**
```python
import urllib.parse

phone = urllib.parse.quote("+1234567890")
response = requests.get(
    f"http://localhost:4000/api/chats/all?accountPhone={phone}"
)
chats = response.json()

# Store in your database
for chat in chats["details"]:
    db.save_chat({
        "telegram_id": chat["id"],
        "name": chat["name"],
        "type": chat["type"],
        "username": chat.get("username")
    })
```

---

#### 5. Get Groups and Channels Only

Same as Get All Chats, but filters to only groups and channels (excludes users and bots).

**Endpoint:** `GET /api/chats/groups`

**Query Parameters:**
- `accountPhone` (required): URL-encoded phone number

**Example Request:**
```
GET /api/chats/groups?accountPhone=%2B1234567890
```

**Response (200):**
```json
{
  "success": true,
  "chats": {
    "My Group": "987654321",
    "News Channel": "555555555"
  },
  "details": [
    {
      "id": "987654321",
      "name": "My Group",
      "type": "group"
    }
  ]
}
```

---

### Chat Messages

#### 6. Get Chat Messages

Fetch message history from a specific chat.

**Endpoint:** `GET /api/chat-messages`

**Query Parameters:**
- `phone` (required): URL-encoded phone number
- `chatId` (required): Chat ID, username, or phone number
- `limit` (optional): Number of messages (1-1000, default: 100)

**Example Request:**
```
GET /api/chat-messages?phone=%2B1234567890&chatId=987654321&limit=50
```

**Response (200):**
```json
{
  "success": true,
  "chatId": "987654321",
  "chatTitle": "My Group",
  "phone": "+1234567890",
  "messagesCount": 50,
  "messages": [
    {
      "id": 12345,
      "date": "2025-11-10T10:30:00.000Z",
      "text": "Hello everyone!",
      "senderId": "123456",
      "senderUsername": "johndoe",
      "senderFirstName": "John",
      "senderLastName": "Doe",
      "isOutgoing": false,
      "isForwarded": false,
      "replyToMessageId": null,
      "media": null,
      "views": 42,
      "forwards": 5
    },
    {
      "id": 12346,
      "date": "2025-11-10T10:31:00.000Z",
      "text": null,
      "senderId": "789012",
      "senderUsername": "alice",
      "senderFirstName": "Alice",
      "senderLastName": null,
      "isOutgoing": false,
      "isForwarded": false,
      "replyToMessageId": 12345,
      "media": {
        "type": "photo",
        "fileName": null,
        "fileSize": 52438,
        "duration": null,
        "mimeType": null
      },
      "views": 38,
      "forwards": 2
    }
  ]
}
```

**Media Types:**
- `photo`, `video`, `document`, `audio`, `sticker`, `voice`, `video_note`, `animation`, `contact`, `location`, `poll`, `unknown`

**Errors:**
- `400`: Missing parameters or invalid limit
- `401`: No authenticated session
- `403`: Not a member or no permission
- `404`: Chat not found
- `500`: Server error

**Call from another service (Python example):**
```python
import urllib.parse

phone = urllib.parse.quote("+1234567890")
chat_id = "987654321"

response = requests.get(
    f"http://localhost:4000/api/chat-messages",
    params={
        "phone": phone,
        "chatId": chat_id,
        "limit": 100
    }
)

messages = response.json()
if messages["success"]:
    # Store messages in your database
    for msg in messages["messages"]:
        db.save_message({
            "telegram_id": msg["id"],
            "chat_id": chat_id,
            "sender_id": msg["senderId"],
            "text": msg["text"],
            "timestamp": msg["date"],
            "has_media": msg["media"] is not None
        })
```

---

### Chat Participants

#### 7. Get Chat Participants

Retrieve all participants/members in a chat (group, channel, or DM).

**Endpoint:** `GET /api/chat-participants`

**Query Parameters:**
- `phone` (required): URL-encoded phone number
- `chatId` (required): Chat ID, username, or phone number
- `limit` (optional): Number of participants (1-1000, default: 100)

**Example Request:**
```
GET /api/chat-participants?phone=%2B1234567890&chatId=987654321&limit=100
```

**Response (200):**
```json
{
  "success": true,
  "chatId": "987654321",
  "chatTitle": "My Group",
  "chatType": "group",
  "phone": "+1234567890",
  "participantsCount": 42,
  "participants": [
    {
      "userId": "123456",
      "firstName": "John",
      "lastName": "Doe",
      "username": "johndoe",
      "isBot": false,
      "isSelf": false
    },
    {
      "userId": "789012",
      "firstName": "Alice",
      "lastName": null,
      "username": "alice",
      "isBot": false,
      "isSelf": false
    },
    {
      "userId": "345678",
      "firstName": "Bot",
      "lastName": null,
      "username": "mybot",
      "isBot": true,
      "isSelf": false
    }
  ]
}
```

**Chat Types:**
- `user`: Direct message (returns 1 participant)
- `group`: Group chat
- `channel`: Broadcast channel

**Errors:**
- `400`: Missing parameters or invalid limit
- `401`: No authenticated session
- `403`: Not a member or admin privileges required
- `404`: Chat not found
- `500`: Server error

**Call from another service (Python example):**
```python
response = requests.get(
    f"http://localhost:4000/api/chat-participants",
    params={
        "phone": urllib.parse.quote("+1234567890"),
        "chatId": "987654321",
        "limit": 100
    }
)

participants = response.json()
if participants["success"]:
    # Store participants in your database
    for p in participants["participants"]:
        db.save_user({
            "telegram_id": p["userId"],
            "first_name": p["firstName"],
            "last_name": p["lastName"],
            "username": p["username"],
            "is_bot": p["isBot"]
        })
        db.save_chat_member({
            "chat_id": "987654321",
            "user_id": p["userId"]
        })
```

---

### Messages

#### 8. Send Message

Send a message to a user, group, or channel.

**Endpoint:** `POST /api/messages/send`

**Request Body:**
```json
{
  "fromPhone": "+1234567890",
  "toTarget": "+9876543210",
  "content": "Hello from the API!",
  "replyTo": 12345
}
```

**Fields:**
- `fromPhone` (required): Authenticated sender phone number
- `toTarget` (required): Phone number, username, or chat ID
- `content` (required): Message text (string or object with `type` and `value`)
- `replyTo` (optional): Message ID to reply to

**Target Formats:**
- Phone: `+9876543210`
- Username: `@username`
- Chat ID: `987654321`

**Response (200):**
```json
{
  "success": true,
  "sentTo": "+9876543210",
  "messageId": 67890
}
```

**Errors:**
- `400`: Missing parameters or invalid input
- `401`: No authenticated session
- `404`: Target not found
- `500`: Server error

**Call from another service (Python example):**
```python
# Send simple text message
response = requests.post(
    "http://localhost:4000/api/messages/send",
    json={
        "fromPhone": "+1234567890",
        "toTarget": "@username",
        "content": "Hello from LangGraph!"
    }
)

# Send reply to a message
response = requests.post(
    "http://localhost:4000/api/messages/send",
    json={
        "fromPhone": "+1234567890",
        "toTarget": "987654321",
        "content": "This is a reply",
        "replyTo": 12345
    }
)
```

---

#### 9. Get Unread Messages

Fetch unread messages from a specific chat or target. **Automatically marks messages as read after fetching.**

**Endpoint:** `GET /api/messages/unread`

**Query Parameters:**
- `accountPhone` (required): URL-encoded phone number
- `target` (optional): Phone number, username, or @channel
- `chatId` (optional): Chat ID

**Note:** Provide either `target` OR `chatId`, not both.

**Example Request:**
```
GET /api/messages/unread?accountPhone=%2B1234567890&target=%2B9876543210
GET /api/messages/unread?accountPhone=%2B1234567890&chatId=987654321
GET /api/messages/unread?accountPhone=%2B1234567890&target=@channelname
```

**Response (200):**
```json
{
  "success": true,
  "count": 3,
  "unread": [
    {
      "id": 12345,
      "sender": "johndoe",
      "message": "Hey, are you there?",
      "date": "2025-11-10T10:30:00.000Z",
      "isOut": false
    },
    {
      "id": 12346,
      "sender": "johndoe",
      "message": "Please respond!",
      "date": "2025-11-10T10:31:00.000Z",
      "isOut": false
    }
  ]
}
```

**Errors:**
- `400`: Missing or conflicting parameters
- `500`: Server error

**Important:** Messages are marked as read after this call!

**Call from another service (Python example):**
```python
response = requests.get(
    "http://localhost:4000/api/messages/unread",
    params={
        "accountPhone": urllib.parse.quote("+1234567890"),
        "chatId": "987654321"
    }
)

unread = response.json()
if unread["success"]:
    print(f"Found {unread['count']} unread messages")
    for msg in unread["unread"]:
        # Process and store
        db.save_message({
            "telegram_id": msg["id"],
            "sender": msg["sender"],
            "text": msg["message"],
            "timestamp": msg["date"]
        })
```

---

### Polls

#### 10. Get Polls

Fetch polls from a chat.

**Endpoint:** `GET /api/polls`

**Query Parameters:**
- `phone` (required): URL-encoded phone number
- `chatId` (required): Chat ID or username
- `limit` (optional): Number of polls (1-1000, default: 1)

**Example Request:**
```
GET /api/polls?phone=%2B1234567890&chatId=987654321&limit=10
```

**Response (200):**
```json
{
  "success": true,
  "chatId": "987654321",
  "chatTitle": "My Group",
  "phone": "+1234567890",
  "pollsCount": 2,
  "polls": [
    {
      "messageId": 12345,
      "pollId": "5234567890123456789",
      "question": "What's your favorite programming language?",
      "date": "2025-11-10T10:00:00.000Z",
      "closed": false,
      "multipleChoice": false,
      "quiz": false,
      "options": [
        {
          "text": "Python",
          "voterCount": 15,
          "chosen": false
        },
        {
          "text": "TypeScript",
          "voterCount": 12,
          "chosen": true
        },
        {
          "text": "Go",
          "voterCount": 8,
          "chosen": false
        }
      ],
      "totalVoters": 35,
      "closePeriod": null,
      "closeDate": null
    }
  ]
}
```

**Poll Properties:**
- `closed`: Whether poll is closed for voting
- `multipleChoice`: Can vote for multiple options
- `quiz`: Has correct answer
- `chosen`: Whether current user voted for this option

**Errors:**
- `400`: Missing parameters or invalid limit
- `401`: No authenticated session
- `404`: Chat not found
- `500`: Server error

**Call from another service (Python example):**
```python
response = requests.get(
    "http://localhost:4000/api/polls",
    params={
        "phone": urllib.parse.quote("+1234567890"),
        "chatId": "987654321",
        "limit": 10
    }
)

polls = response.json()
if polls["success"]:
    for poll in polls["polls"]:
        # Analyze poll results
        most_voted = max(poll["options"], key=lambda x: x["voterCount"])
        print(f"Poll: {poll['question']}")
        print(f"Winner: {most_voted['text']} with {most_voted['voterCount']} votes")
```

---

#### 11. Vote on Poll

Submit a vote on a poll.

**Endpoint:** `POST /api/polls/vote`

**Request Body:**
```json
{
  "phone": "+1234567890",
  "chatId": "987654321",
  "messageId": 12345,
  "optionIds": [0, 2]
}
```

**Fields:**
- `phone` (required): Authenticated phone number
- `chatId` (required): Chat ID containing the poll
- `messageId` (required): Message ID of the poll
- `optionIds` (required): Array of option indices (0-based)

**Note:** For single-choice polls, only first option is used. For multiple-choice, all options in array are voted.

**Response (200):**
```json
{
  "success": true,
  "pollId": "5234567890123456789",
  "messageId": 12345,
  "votedOptions": [0, 2]
}
```

**Errors:**
- `400`: Missing parameters, poll closed, or invalid option IDs
- `401`: No authenticated session
- `404`: Chat or message not found, or message is not a poll
- `500`: Server error

**Call from another service (Python example):**
```python
# Vote for single option (option 0)
response = requests.post(
    "http://localhost:4000/api/polls/vote",
    json={
        "phone": "+1234567890",
        "chatId": "987654321",
        "messageId": 12345,
        "optionIds": [0]
    }
)

# Vote for multiple options (if poll allows)
response = requests.post(
    "http://localhost:4000/api/polls/vote",
    json={
        "phone": "+1234567890",
        "chatId": "987654321",
        "messageId": 12345,
        "optionIds": [0, 2, 3]
    }
)
```

---

### Health & Status

#### 12. Health Check

Check if the service is running.

**Endpoint:** `GET /health`

**Response (200):**
```json
{
  "success": true,
  "version": "0.1.0",
  "environment": "development",
  "port": 4000
}
```

---

## Using from Other Services

### Python Example (Complete Workflow)

```python
import requests
import urllib.parse
from typing import Dict, List, Optional

class TelegramClient:
    def __init__(self, base_url: str = "http://localhost:4000"):
        self.base_url = base_url
    
    def _encode_phone(self, phone: str) -> str:
        """URL-encode phone number"""
        return urllib.parse.quote(phone)
    
    # Authentication
    def send_code(self, phone: str, api_id: int, api_hash: str) -> Dict:
        """Step 1: Send verification code"""
        response = requests.post(
            f"{self.base_url}/api/auth/send-code",
            json={"phone": phone, "apiId": api_id, "apiHash": api_hash}
        )
        return response.json()
    
    def verify_code(self, phone: str, code: str) -> Dict:
        """Step 2: Verify code and authenticate"""
        response = requests.post(
            f"{self.base_url}/api/auth/verify-code",
            json={"phone": phone, "code": code}
        )
        return response.json()
    
    # Chats
    def get_all_chats(self, phone: str) -> Dict:
        """Get all chats (users, groups, channels, bots)"""
        response = requests.get(
            f"{self.base_url}/api/chats/all",
            params={"accountPhone": self._encode_phone(phone)}
        )
        return response.json()
    
    def get_groups(self, phone: str) -> Dict:
        """Get only groups and channels"""
        response = requests.get(
            f"{self.base_url}/api/chats/groups",
            params={"accountPhone": self._encode_phone(phone)}
        )
        return response.json()
    
    # Messages
    def get_chat_messages(self, phone: str, chat_id: str, limit: int = 100) -> Dict:
        """Fetch message history from a chat"""
        response = requests.get(
            f"{self.base_url}/api/chat-messages",
            params={
                "phone": self._encode_phone(phone),
                "chatId": chat_id,
                "limit": limit
            }
        )
        return response.json()
    
    def send_message(self, from_phone: str, to_target: str, 
                    content: str, reply_to: Optional[int] = None) -> Dict:
        """Send a message"""
        payload = {
            "fromPhone": from_phone,
            "toTarget": to_target,
            "content": content
        }
        if reply_to:
            payload["replyTo"] = reply_to
        
        response = requests.post(
            f"{self.base_url}/api/messages/send",
            json=payload
        )
        return response.json()
    
    def get_unread_messages(self, phone: str, chat_id: str) -> Dict:
        """Get unread messages (auto-marks as read)"""
        response = requests.get(
            f"{self.base_url}/api/messages/unread",
            params={
                "accountPhone": self._encode_phone(phone),
                "chatId": chat_id
            }
        )
        return response.json()
    
    # Participants
    def get_chat_participants(self, phone: str, chat_id: str, limit: int = 100) -> Dict:
        """Get all participants in a chat"""
        response = requests.get(
            f"{self.base_url}/api/chat-participants",
            params={
                "phone": self._encode_phone(phone),
                "chatId": chat_id,
                "limit": limit
            }
        )
        return response.json()
    
    # Polls
    def get_polls(self, phone: str, chat_id: str, limit: int = 10) -> Dict:
        """Get polls from a chat"""
        response = requests.get(
            f"{self.base_url}/api/polls",
            params={
                "phone": self._encode_phone(phone),
                "chatId": chat_id,
                "limit": limit
            }
        )
        return response.json()
    
    def vote_poll(self, phone: str, chat_id: str, 
                  message_id: int, option_ids: List[int]) -> Dict:
        """Vote on a poll"""
        response = requests.post(
            f"{self.base_url}/api/polls/vote",
            json={
                "phone": phone,
                "chatId": chat_id,
                "messageId": message_id,
                "optionIds": option_ids
            }
        )
        return response.json()


# Usage Example
telegram = TelegramClient("http://localhost:4000")

# 1. Authenticate (one-time)
telegram.send_code("+1234567890", 12345, "api_hash")
# ... user receives code on Telegram ...
telegram.verify_code("+1234567890", "12345")

# 2. Get all chats
chats = telegram.get_all_chats("+1234567890")
for chat in chats["details"]:
    print(f"{chat['name']} ({chat['type']}): {chat['id']}")

# 3. Get participants from a group
participants = telegram.get_chat_participants("+1234567890", "987654321")
for p in participants["participants"]:
    print(f"- {p['firstName']} (@{p['username']})")

# 4. Fetch messages
messages = telegram.get_chat_messages("+1234567890", "987654321", limit=50)
for msg in messages["messages"]:
    print(f"[{msg['date']}] {msg['senderFirstName']}: {msg['text']}")

# 5. Send message
telegram.send_message("+1234567890", "@username", "Hello from Python!")

# 6. Get and vote on polls
polls = telegram.get_polls("+1234567890", "987654321")
if polls["pollsCount"] > 0:
    poll = polls["polls"][0]
    telegram.vote_poll("+1234567890", "987654321", poll["messageId"], [0])
```

### Node.js/TypeScript Example

```typescript
import axios from 'axios';

class TelegramClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:4000') {
    this.baseUrl = baseUrl;
  }

  async getAllChats(phone: string) {
    const response = await axios.get(`${this.baseUrl}/api/chats/all`, {
      params: { accountPhone: encodeURIComponent(phone) }
    });
    return response.data;
  }

  async getChatParticipants(phone: string, chatId: string, limit: number = 100) {
    const response = await axios.get(`${this.baseUrl}/api/chat-participants`, {
      params: {
        phone: encodeURIComponent(phone),
        chatId,
        limit
      }
    });
    return response.data;
  }

  async sendMessage(fromPhone: string, toTarget: string, content: string) {
    const response = await axios.post(`${this.baseUrl}/api/messages/send`, {
      fromPhone,
      toTarget,
      content
    });
    return response.data;
  }
}

// Usage
const telegram = new TelegramClient();
const chats = await telegram.getAllChats('+1234567890');
```

---

## API Endpoints

## Data Storage

### Phone Data Files

Location: `telegram2/data/phone_+1234567890.json`

Structure:
```json
{
  "phone": "+1234567890",
  "apiId": 12345,
  "apiHash": "abc123...",
  "session": "session_string...",
  "phoneCodeHash": "temp_hash...",
  "verified": true,
  "lastAuthAt": "2025-10-29T10:00:00.000Z"
}
```

## Testing with Postman

1. Import the collection: `Telegram2-API.postman_collection.json`
2. Update environment variables:
   - `BASE_URL`: `http://localhost:4000`
   - `PHONE_NUMBER`: Your phone number
   - `API_ID`: Your Telegram API ID
   - `API_HASH`: Your Telegram API hash
   - `TARGET_PHONE`: Target phone for testing
3. Follow the authentication flow:
   - Send code
   - Check Telegram app for code
   - Verify code
4. Test messaging and unread endpoints

## Logging

All logs are output in JSON format for easy parsing:

```json
{
  "timestamp": "2025-10-29T10:30:00.000Z",
  "level": "INFO",
  "message": "Session loaded and connected",
  "phone": "+1234567890"
}
```

Log levels: `DEBUG`, `INFO`, `WARN`, `ERROR`

## Error Handling

All error responses follow a consistent format:

```json
{
  "success": false,
  "error": "Error message description"
}
```

### HTTP Status Codes

- **200**: Success
- **400**: Bad Request - Invalid input, missing parameters, or validation error
- **401**: Unauthorized - No authenticated session found
- **403**: Forbidden - No permission (not a member, admin required, etc.)
- **404**: Not Found - Chat, user, or message not found
- **500**: Internal Server Error - Server or Telegram API error

### Common Error Messages

| Error Message | Meaning | Solution |
|---------------|---------|----------|
| `No authenticated session found for {phone}` | Phone not authenticated | Call `/api/auth/send-code` and `/api/auth/verify-code` |
| `Chat not found: {chatId}` | Chat ID doesn't exist or not accessible | Use `/api/chats/all` to get valid chat IDs |
| `You are not a member of this chat` | Account not in the chat | Join the chat first via Telegram app |
| `Admin privileges required to view participants` | Need admin rights | Request admin access or use admin account |
| `Target not found: {target}` | Username or phone doesn't exist | Verify target exists and you've interacted before |
| `Phone parameter is required` | Missing phone parameter | Add phone to query/body |
| `Limit must be a number between 1 and 1000` | Invalid limit | Use limit between 1-1000 |
| `Either target or chatId must be provided` | Missing both parameters | Provide one parameter |
| `Provide either target or chatId, not both` | Conflicting parameters | Use only one parameter |
| `PHONE_CODE_EXPIRED` | Verification code expired | Request new code (codes expire in 2-3 minutes) |
| `Invalid verification code` | Wrong code entered | Double-check code from Telegram app |
| `Poll is closed` | Can't vote on closed poll | Poll voting is closed |
| `Invalid option ID` | Option index out of range | Use valid option index (0-based) |

---

## Session Persistence

- Sessions are saved to JSON files after authentication
- On server restart, all sessions are automatically reloaded
- No need to re-authenticate unless session is deleted

## Graceful Shutdown

The service handles `SIGINT` and `SIGTERM` signals:
1. Disconnects all Telegram clients
2. Closes server connections
3. Exits cleanly

## Code Quality

- ✅ No classes/OOP - pure functional approach
- ✅ All files under 120 lines
- ✅ Clean separation: Utils/Services/Routes
- ✅ Full TypeScript typing
- ✅ Input validation on all endpoints
- ✅ Smart logging for debugging

## Troubleshooting

### "Phone data not found"
Run `/api/auth/send-code` first to save credentials.

### "Verification code has expired"
**This is the most common issue!** Telegram verification codes expire after a few minutes.

**Solution:**
1. Call `/api/auth/send-code` to get a new code
2. Check Telegram immediately for the new code
3. Call `/api/auth/verify-code` **within 2-3 minutes**
4. Don't wait too long between steps!

**Important:** The verification code from Telegram expires quickly. You must enter it within a few minutes of receiving it. If you get a "PHONE_CODE_EXPIRED" error, just request a new code and try again faster.

### "Invalid verification code"
Double-check the code from your Telegram app. Make sure you're using the latest code.

### "2FA is enabled on this account"
Password authentication (2FA) is not yet supported. You'll need to temporarily disable 2FA or use an account without it.

### "Sender not authenticated"
Complete the authentication flow before sending messages.

### "Failed to connect session"
Session may be expired. Re-authenticate with `/api/auth/send-code` and `/api/auth/verify-code`.

## Development

### File Size Limits
All files are kept under 120 lines for maintainability.

### Adding New Features
Follow the pattern:
1. Add utility functions in `utils/`
2. Add business logic in `services/`
3. Add routes in `routes/`
4. Update Postman collection

## License

Private - Internal Use Only
