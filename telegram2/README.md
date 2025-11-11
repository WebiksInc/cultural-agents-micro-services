# Telegram2 Microservice
# Telegram2 Service (Simple Telegram MTProto Integration)



A clean, functional TypeScript microservice for Telegram integration using GramJS library.
Minimal service providing:

- Authentication (send code, verify code) using telegram (MTProto client)

## Features- Send message between accounts and targets (phone numbers only)

- Fetch unread messages (based on last fetched state)

- **Authentication**: Phone verification with session persistence

- **Message Sending**: Send messages to users, groups, and channels## Endpoints

- **Unread Messages**: Fetch and auto-mark-as-read messages from any target1. POST /auth/send-code { apiId, apiHash, phone }

- **Session Management**: Persistent sessions survive server restarts2. POST /auth/verify-code { phone, code }

- **Clean Architecture**: Utils, Services, Routes separation3. POST /messages/send { fromPhone, toPhone, content }

- **Smart Logging**: JSON-formatted logs for easy debugging4. GET /messages/unread?accountPhone=...&target=... (target can be phone or channel username like @mychannel)



## Architecture## Running

Install deps and start:

``````

telegram2/npm install

├── src/npm run dev

│   ├── utils/          # Utility functions```

│   │   ├── logger.ts         # JSON logging

│   │   ├── phoneStorage.ts   # Per-phone JSON files
│   │   │                        # Set LOG_LEVEL=debug for verbose logs.
│   │   └── validators.ts     # Input validation

│   ├── services/       # Business logic
│   │   │                  # Data Store
│   │   ├── sessionManager.ts # Session lifecycle
│   │   │                        # Single JSON file at data/store.json maintaining accounts, messages, and conversation state.
│   │   ├── authService.ts    # Authentication

│   │   ├── messageService.ts # Send messages
│   │   │                        # Notes
│   │   └── unreadService.ts  # Fetch unread
│   │   │                        # Each file kept under 120 lines.
│   ├── routes/         # API endpoints
│   │   │                  # Sessions auto-loaded at startup.
│   │   ├── authRoutes.ts
│   │   │                        # Unread determined by last fetched message id per conversation.
│   │   ├── messageRoutes.ts
│   │   │                        # Channel support: pass channel username as target (e.g. @telegram). Messages filtered same way.
│   │   ├── unreadRoutes.ts
│   │   └── index.ts
│   └── server.ts       # Express server
└── data/               # Generated at runtime
    └── phone_+123.json # Per-phone credentials
```

## Setup

### Install Dependencies

```bash
cd telegram2
npm install
```

### Environment Variables Configuration

#### Setup

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your preferred settings:
   ```bash
   # Basic configuration
   PORT=4000
   NODE_ENV=development
   LOG_LEVEL=info
   DATA_DIR=./data
   AUTO_LOAD_SESSIONS=true
   ```

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

**Production Environment:**
```bash
PORT=8080
NODE_ENV=production
LOG_LEVEL=info
DATA_DIR=/app/data
AUTO_LOAD_SESSIONS=true
CONNECTION_RETRIES=5
SHUTDOWN_TIMEOUT=15000
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

#### Log Level Behavior

- **`debug`**: All log messages (debug, info, warn, error)
- **`info`**: Info, warn, and error messages
- **`warn`**: Only warn and error messages  
- **`error`**: Only error messages

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

### 1. Health Check

**GET** `/health`

Response:
```json
{
  "success": true,
  "message": "Service is healthy",
  "version": "0.1.0",
  "environment": "development",
  "port": 4000
}
```

**GET** `/config`

Returns current configuration (excluding sensitive data):
```json
{
  "success": true,
  "config": {
    "nodeEnv": "development",
    "port": 4000,
    "logLevel": "info",
    "dataDir": "./data",
    "autoLoadSessions": true,
    "connectionRetries": 3,
    "hasDefaultApiCredentials": false
  }
}
```

Test your configuration:
```bash
curl http://localhost:4000/config
```

### 2. Send Verification Code

**POST** `/api/auth/send-code`

Request body:
```json
{
  "phone": "+1234567890",
  "apiId": 12345,
  "apiHash": "your_api_hash"
}
```

Response:
```json
{
  "success": true,
  "phoneCodeHash": "abc123...",
  "message": "Verification code sent to Telegram"
}
```

### 3. Verify Code

**POST** `/api/auth/verify-code`

Request body:
```json
{
  "phone": "+1234567890",
  "code": "12345"
}
```

Response:
```json
{
  "success": true,
  "user": "John",
  "message": "Authentication successful"
}
```

### 4. Send Message

**POST** `/api/messages/send`

Request body:
```json
{
  "fromPhone": "+1234567890",
  "toTarget": "+9876543210",
  "message": "Hello!"
}
```

Target can be:
- Phone number: `+1234567890`
- Username: `@username`
- Group: `@groupname`
- Channel: `@channelname`

Response:
```json
{
  "success": true,
  "sentTo": "+9876543210",
  "message": "Message sent successfully"
}
```

### 5. Get Unread Messages

**GET** `/api/messages/unread`

Query parameters:
- `accountPhone`: Your authenticated phone number (required)
- `target`: Phone/username/channel to fetch from (optional)
- `chatId`: Chat ID to fetch from (optional)

**Note**: Either `target` OR `chatId` must be provided, not both.

**Example 1: Using target (phone/username)**
```
GET /api/messages/unread?accountPhone=%2B1234567890&target=%2B9876543210
GET /api/messages/unread?accountPhone=%2B1234567890&target=@channelname
```

**Example 2: Using chat ID**
```
GET /api/messages/unread?accountPhone=%2B1234567890&chatId=123456789
```

Response:
```json
{
  "success": true,
  "count": 2,
  "unread": [
    {
      "id": 12345,
      "sender": "username",
      "message": "Hello!",
      "date": "2025-10-29T10:30:00.000Z",
      "isOut": false
    }
  ]
}
```

**Important Notes**:
- Messages are automatically marked as read after fetching
- Phone numbers in URL must be URL-encoded (`+` becomes `%2B`)
- Use the `/api/chats/all` endpoint to get chat IDs

### 6. Get All Chats

**GET** `/api/chats/all?accountPhone=+1234567890`

Returns all chats (users, groups, channels, bots) with their IDs.

Query parameters:
- `accountPhone`: Your authenticated phone number

Response:
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
    }
  ],
  "count": 3
}
```

### 7. Get Groups and Channels Only

**GET** `/api/chats/groups?accountPhone=+1234567890`

Returns only groups and channels (excludes users and bots).

Query parameters:
- `accountPhone`: Your authenticated phone number

Response:
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
      "type": "group",
      "username": "mygroup"
    }
  ],
  "count": 2
}
```

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

All errors return a consistent format:

```json
{
  "success": false,
  "error": "Error message description"
}
```

Common errors:
- `400`: Invalid input or authentication required
- `500`: Internal server error

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
