# 🚀 Quick Start Guide

## Prerequisites

1. **Telegram API Credentials**
   - Go to https://my.telegram.org
   - Login with your phone number
   - Go to "API development tools"
   - Create an application to get `api_id` and `api_hash`

2. **Docker & Docker Compose**
   - Ensure Docker is installed and running

## Installation & Running

### Option 1: Docker Compose (Recommended)

```bash
# From project root
cd /home/yair/cultural-agents-micro-services

# Build and start the service
docker-compose up --build telegram

# Or run in background
docker-compose up -d telegram

# View logs
docker-compose logs -f telegram

# Stop the service
docker-compose down
```

### Option 2: Local Development

```bash
cd telegram

# Install dependencies
npm install

# Build TypeScript
npm run build

# Start the server
npm start

# Or for development with auto-reload
npm run dev
```

## Testing with Postman

1. **Import Collection**
   ```bash
   File: telegram/Telegram-API.postman_collection.json
   ```

2. **Configure Variables**
   - Click collection → Variables
   - Set your `phone`, `apiId`, `apiHash`

3. **Run Authentication Flow**
   - Save Credentials
   - Start Authentication (check Telegram app for code)
   - Verify Code

4. **Start Messaging**
   - Send messages
   - Fetch unread messages

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/credentials` | Save phone + API credentials |
| POST | `/auth/start` | Initiate authentication |
| POST | `/auth/verify` | Verify code from Telegram |
| POST | `/send` | Send a message |
| GET | `/get` | Get unread messages |

## File Structure

```
telegram/
├── src/                 # TypeScript source files
│   ├── routes/         # API endpoints (5 files)
│   ├── services/       # Business logic (8 files)
│   ├── utils/          # Helper functions (4 files)
│   └── types/          # TypeScript interfaces
├── config/             # Phone credentials (generated)
├── sessions/           # Telegram sessions (generated)
└── Telegram-API.postman_collection.json
```

## Verification

```bash
# Check if service is running
curl http://localhost:8005/auth/credentials

# Should return 405 Method Not Allowed (expects POST)
```

## Next Steps

1. Get your Telegram API credentials
2. Import Postman collection
3. Follow authentication flow
4. Start sending/receiving messages!

## Support

- Full API documentation: `telegram/README.md`
- Postman guide: `telegram/POSTMAN_GUIDE.md`
- Implementation details: `telegram/IMPLEMENTATION.md`
