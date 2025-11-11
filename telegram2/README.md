# Telegram2 Service

## Summary

Telegram2 is a stateless REST API microservice that interfaces with Telegram's API using GramJS. It provides endpoints for authentication, chat management, messaging, and poll interactions. The service maintains session persistence through JSON files and serves as an API gateway for Telegram operations.

**Base URL:** `http://localhost:4000`

---

## Setup

### Prerequisites
- Node.js 20+
- Telegram API credentials (API_ID and API_HASH from https://my.telegram.org)

### Installation

```bash
npm install
```

### Build

```bash
npm run build
```

### Run

```bash
# Development
npm run dev

# Production
npm start
```

---

## Docker

### Build Image

```bash
docker build -t telegram2-service .
```

The Dockerfile uses a multi-stage build:
- **Builder stage**: Compiles TypeScript to JavaScript
- **Production stage**: Runs with minimal dependencies (Node.js 20 Alpine)
- **Security**: Runs as non-root user (`node`)
- **Health check**: Built-in health monitoring

---

### Run Container (Standalone)

```bash
docker run -d \
  --name telegram2 \
  -p 4000:4000 \
  -e TELEGRAM_API_ID=your_api_id \
  -e TELEGRAM_API_HASH=your_api_hash \
  -e NODE_ENV=production \
  -v $(pwd)/data:/app/data \
  telegram2-service
```

**Important:** Mount the `data` directory to persist session files between container restarts.

---

### Docker Compose (Recommended)

The root directory contains a `docker-compose.yml` file for easy deployment:

```yaml
services:
  telegram2:
    build: ./telegram2
    ports:
      - "4000:4000"
    volumes:
      - ./telegram2/data:/app/data
    environment:
      - NODE_ENV=production
      - PORT=4000
      - LOG_LEVEL=info
      - DATA_DIR=/app/data
      - AUTO_LOAD_SESSIONS=true
      - CONNECTION_RETRIES=5
      - SHUTDOWN_TIMEOUT=15000
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:4000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Commands:**

```bash
# Start service
docker-compose up -d telegram2

# View logs
docker-compose logs -f telegram2

# Stop service
docker-compose down

# Rebuild and restart
docker-compose up -d --build telegram2
```

---

### Health Check

The Docker container includes automatic health monitoring:
- **Endpoint**: `/health`
- **Interval**: Every 30 seconds
- **Timeout**: 10 seconds
- **Start period**: 40 seconds (allows startup time)
- **Retries**: 3 attempts before marking unhealthy

Check container health:
```bash
docker ps
# Look for "healthy" status in the STATUS column
```

---

### Volume Persistence

Session files are stored in `/app/data` inside the container. **Always mount this directory** to persist authenticated sessions:

```bash
# Local directory mount
-v $(pwd)/data:/app/data

# Named volume (alternative)
-v telegram2-data:/app/data
```

Without volume mounting, all sessions will be lost when the container restarts.

---

## Environment Variables

Configure these in a `.env` file or through environment variables:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PORT` | number | `4000` | Server port |
| `NODE_ENV` | string | `development` | Environment mode |
| `LOG_LEVEL` | string | `info` | Logging level (error, warn, info, debug) |
| `DATA_DIR` | string | `./data` | Directory for session files |
| `CONNECTION_RETRIES` | number | `3` | Connection retry attempts |
| `SHUTDOWN_TIMEOUT` | number | `10000` | Graceful shutdown timeout (ms) |
| `AUTO_LOAD_SESSIONS` | boolean | `true` | Auto-load saved sessions on startup |
| `SESSION_CLEANUP_INTERVAL` | number | `3600000` | Session cleanup interval (ms) |
| `TELEGRAM_API_ID` | number | - | Telegram API ID (required) |
| `TELEGRAM_API_HASH` | string | - | Telegram API Hash (required) |

---

## Routes

### Health Check

**GET** `/health`

**Response:**
```json
{
  "success": true,
  "version": "0.1.0",
  "environment": "development",
  "port": 4000
}
```

---

### Authentication

#### Send Verification Code

**POST** `/api/auth/send-code`

**Request Body:**
```json
{
  "phone": "+1234567890",
  "apiId": 12345678,
  "apiHash": "your_api_hash_here"
}
```

**Response:**
```json
{
  "success": true,
  "phoneCodeHash": "hash_string"
}
```

---

#### Verify Code

**POST** `/api/auth/verify-code`

**Request Body:**
```json
{
  "phone": "+1234567890",
  "code": "12345"
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": "123456789",
    "firstName": "John",
    "lastName": "Doe",
    "username": "johndoe",
    "phone": "+1234567890"
  }
}
```

---

#### Get Active Sessions

**GET** `/api/auth/debug/active-sessions`

**Response:**
```json
{
  "success": true,
  "count": 2,
  "activePhones": ["+1234567890", "+9876543210"]
}
```

---

### Chats

#### Get All Chats

**GET** `/api/chats/all`

**Query Parameters:**
- `accountPhone` (required): Phone number

**Response:**
```json
{
  "success": true,
  "chats": [
    {
      "id": "123456789",
      "title": "Chat Name",
      "type": "user | group | channel",
      "username": "chatusername"
    }
  ],
  "details": {
    "totalChats": 5,
    "users": 2,
    "groups": 2,
    "channels": 1
  }
}
```

---

#### Get Groups Only

**GET** `/api/chats/groups`

**Query Parameters:**
- `accountPhone` (required): Phone number

**Response:**
```json
{
  "success": true,
  "chats": [
    {
      "id": "123456789",
      "title": "Group Name",
      "type": "group | channel",
      "username": "groupusername"
    }
  ],
  "details": {
    "totalChats": 3,
    "groups": 2,
    "channels": 1
  }
}
```

---

### Chat Messages

#### Get Chat Messages

**GET** `/api/chat-messages`

**Query Parameters:**
- `phone` (required): Phone number
- `chatId` (required): Chat ID or username
- `limit` (optional): Number of messages (1-1000, default: 100)

**Response:**
```json
{
  "success": true,
  "chatId": "123456789",
  "chatTitle": "Chat Name",
  "phone": "+1234567890",
  "messagesCount": 50,
  "messages": [
    {
      "id": 12345,
      "chatId": "123456789",
      "senderId": "987654321",
      "senderUsername": "username",
      "senderFirstName": "John",
      "text": "Message content",
      "date": "2025-11-11T10:30:00.000Z",
      "isOutgoing": false,
      "replyToMsgId": null,
      "mediaType": null
    }
  ]
}
```

---

### Chat Participants

#### Get Chat Participants

**GET** `/api/chat-participants`

**Query Parameters:**
- `phone` (required): Phone number
- `chatId` (required): Chat ID or username
- `limit` (optional): Number of participants (1-1000, default: 100)

**Response:**
```json
{
  "success": true,
  "chatId": "123456789",
  "chatTitle": "Group Name",
  "chatType": "group | channel",
  "phone": "+1234567890",
  "participantsCount": 15,
  "participants": [
    {
      "userId": "987654321",
      "firstName": "John",
      "lastName": "Doe",
      "username": "johndoe",
      "isBot": false,
      "isSelf": false
    }
  ]
}
```

---

### Messages

#### Send Message

**POST** `/api/messages/send`

**Request Body:**
```json
{
  "fromPhone": "+1234567890",
  "toTarget": "username or +phone or chatId",
  "content": "Message text",
  "replyTo": 12345
}
```

**Response:**
```json
{
  "success": true,
  "sentTo": "username",
  "messageId": 67890
}
```

---

#### Get Unread Messages

**GET** `/api/messages/unread`

**Query Parameters:**
- `accountPhone` (required): Phone number
- `target` OR `chatId` (one required): Username/phone or chat ID

**Response:**
```json
{
  "success": true,
  "count": 5,
  "unread": [
    {
      "id": 12345,
      "chatId": "123456789",
      "senderId": "987654321",
      "senderUsername": "username",
      "text": "Unread message",
      "date": "2025-11-11T10:30:00.000Z",
      "isOutgoing": false
    }
  ]
}
```

**Note:** This endpoint automatically marks messages as read after fetching.

---

### Polls

#### Get Polls

**GET** `/api/polls`

**Query Parameters:**
- `phone` (required): Phone number
- `chatId` (required): Chat ID or username
- `limit` (optional): Number of polls (1-1000, default: 1)

**Response:**
```json
{
  "success": true,
  "chatId": "123456789",
  "chatTitle": "Chat Name",
  "phone": "+1234567890",
  "pollsCount": 1,
  "polls": [
    {
      "id": "poll_id_123",
      "question": "Poll question?",
      "answers": [
        {
          "text": "Option 1",
          "voters": 5,
          "option": 0
        },
        {
          "text": "Option 2",
          "voters": 3,
          "option": 1
        }
      ],
      "closed": false,
      "totalVoters": 8,
      "messageId": 12345
    }
  ]
}
```

---

#### Vote on Poll

**POST** `/api/polls/vote`

**Request Body:**
```json
{
  "phone": "+1234567890",
  "chatId": "123456789",
  "messageId": 12345,
  "optionIds": [0, 1]
}
```

**Response:**
```json
{
  "success": true,
  "pollId": "poll_id_123",
  "messageId": 12345,
  "votedOptions": [0, 1]
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "success": false,
  "error": "Error message description"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `400` | Bad Request (validation error, missing parameters) |
| `401` | Unauthorized (no authenticated session) |
| `403` | Forbidden (not a member, insufficient permissions) |
| `404` | Not Found (chat/user/poll not found) |
| `500` | Internal Server Error |

---



## Session Persistence

Sessions are stored as JSON files in the `DATA_DIR` directory (default: `./data`). Each authenticated phone number creates a file: `phone_+1234567890.json`

Sessions are automatically loaded on startup when `AUTO_LOAD_SESSIONS=true`.
