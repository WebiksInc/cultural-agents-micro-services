# Telegram2 Service - Quick Start Guide

## Prerequisites

1. **Telegram API Credentials**
   - Go to https://my.telegram.org
   - Login with your phone number
   - Navigate to "API development tools"
   - Create a new application
   - Save your `api_id` and `api_hash`

2. **Node.js & npm**
   - Node.js v18 or higher
   - npm v8 or higher

## Installation

```bash
cd telegram2
npm install
```

## Running the Service

### Development Mode (with auto-reload)
```bash
npm run dev
```

### Production Mode
```bash
npm start
```

The service will start on `http://localhost:4000`

## Testing Flow

### Step 1: Send Verification Code

**Request:**
```bash
curl -X POST http://localhost:4000/api/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+1234567890",
    "apiId": 12345,
    "apiHash": "your_api_hash_here"
  }'
```

**Response:**
```json
{
  "success": true,
  "phoneCodeHash": "abc123...",
  "message": "Verification code sent to Telegram"
}
```

**What happens:**
- A verification code is sent to your Telegram app
- Your phone number, apiId, and apiHash are saved to `data/phone_+1234567890.json`
- A temporary client is created and **stored in memory**

⚠️ **CRITICAL:** Do NOT restart the server between send-code and verify-code! The client must stay in memory.

### Step 2: Check Telegram App

**IMPORTANT**: Open your Telegram app **immediately** and find the verification code message.

⚠️ **The code expires in 2-3 minutes!** Don't wait too long before verifying.

⚠️ **Do NOT restart the server!** The client session must stay alive in memory.

### Step 3: Verify Code

**Do this quickly** - the code will expire!
**Do NOT restart the server** - the client must stay connected!

**Request:**
```bash
curl -X POST http://localhost:4000/api/auth/verify-code \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+1234567890",
    "code": "12345"
  }'
```

**Response:**
```json
{
  "success": true,
  "user": "John",
  "message": "Authentication successful"
}
```

**What happens:**
- Your session is verified and saved
- Session persists across server restarts
- You're now authenticated and ready to send/receive messages

### Step 4: Send a Message

**To a Phone Number:**
```bash
curl -X POST http://localhost:4000/api/messages/send \
  -H "Content-Type: application/json" \
  -d '{
    "fromPhone": "+1234567890",
    "toTarget": "+9876543210",
    "message": "Hello from Telegram2 service!"
  }'
```

**To a Group:**
```bash
curl -X POST http://localhost:4000/api/messages/send \
  -H "Content-Type: application/json" \
  -d '{
    "fromPhone": "+1234567890",
    "toTarget": "@mygroupname",
    "message": "Hello group!"
  }'
```

**Response:**
```json
{
  "success": true,
  "sentTo": "+9876543210",
  "message": "Message sent successfully"
}
```

### Step 5: Get Unread Messages

**From a User:**
```bash
curl "http://localhost:4000/api/messages/unread?accountPhone=%2B1234567890&target=%2B9876543210"
```

**From a Channel:**
```bash
curl "http://localhost:4000/api/messages/unread?accountPhone=%2B1234567890&target=%40channelname"
```

**From a Group:**
```bash
curl "http://localhost:4000/api/messages/unread?accountPhone=%2B1234567890&target=%40groupname"
```

**Response:**
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
    },
    {
      "id": 12346,
      "sender": "another_user",
      "message": "How are you?",
      "date": "2025-10-29T10:31:00.000Z",
      "isOut": false
    }
  ]
}
```

**Important:** Messages are automatically marked as read after fetching!

## Using Postman

1. Import `Telegram2-API.postman_collection.json` into Postman
2. Update the collection variables:
   - `BASE_URL`: `http://localhost:4000`
   - `PHONE_NUMBER`: Your phone (e.g., `+1234567890`)
   - `API_ID`: Your Telegram API ID
   - `API_HASH`: Your Telegram API hash
   - `TARGET_PHONE`: A target phone for testing
3. Run requests in order:
   - Health Check
   - Send Verification Code
   - Verify Code
   - Send Message
   - Get Unread Messages

## Common Errors and Solutions

### Error: "Client session not found"
**This means the server was restarted between send-code and verify-code!**

**Solution:**
1. Make sure the server is running continuously
2. Call `/api/auth/send-code` 
3. **WITHOUT restarting the server**, call `/api/auth/verify-code`
4. The client must stay in memory during this process

### Error: "Verification code has expired"
**This is the most common error!** Telegram codes expire in 2-3 minutes.

**Solution:**
1. Call `/api/auth/send-code` again to get a fresh code
2. Check Telegram **immediately**
3. Call `/api/auth/verify-code` **right away**
4. Complete the process within 2-3 minutes
5. **Do NOT restart the server during this process!**

**Tip:** Have everything ready before requesting the code. Don't let the code sit unused.

### Error: "Invalid verification code"
**Solution:** 
- Make sure you're using the most recent code from Telegram
- Check for typos
- The code might have expired - request a new one

### Error: "Phone data not found"
**Solution:** You need to call `/api/auth/send-code` first to save your credentials.

### Error: "Sender not authenticated"
**Solution:** Complete the authentication flow:
1. Call `/api/auth/send-code`
2. Get the code from Telegram
3. Call `/api/auth/verify-code`

### Error: "Session not authorized"
**Solution:** Your session may have expired. Re-authenticate using the steps above.

### Error: "Phone number must start with +"
**Solution:** Always include the country code with + prefix (e.g., `+1234567890`)

### Error: "Failed to connect session"
**Solution:** 
- Check if the session file exists in `data/`
- Try deleting the session file and re-authenticating
- Ensure your API credentials are correct

## Data Files

All data is stored in the `telegram2/data/` directory:

```
data/
├── phone_+1234567890.json
├── phone_+9876543210.json
└── ...
```

Each file contains:
- Phone number
- API credentials (apiId, apiHash)
- Session string (after verification)
- Verification status
- Last authentication timestamp

## Logs

All logs are in JSON format for easy parsing:

```json
{
  "timestamp": "2025-10-29T10:30:00.000Z",
  "level": "INFO",
  "message": "Session loaded and connected",
  "phone": "+1234567890"
}
```

## Health Check

Always check if the service is running:

```bash
curl http://localhost:4000/health
```

Response:
```json
{
  "success": true,
  "message": "Service is healthy"
}
```

## Stopping the Service

Press `Ctrl+C` in the terminal. The service will:
1. Disconnect all Telegram clients gracefully
2. Save any pending data
3. Exit cleanly

## Tips

1. **Session Persistence**: Once authenticated, you don't need to verify again (even after restarts)
2. **Multiple Accounts**: You can authenticate multiple phone numbers simultaneously
3. **Target Formats**: 
   - Phone: `+1234567890`
   - Username: `@username`
   - Group: `@groupname`
   - Channel: `@channelname`
4. **Auto Mark as Read**: Unread messages are automatically marked as read when fetched
5. **Group Messages**: Use the group's @username, not the display name

## Architecture Benefits

- ✅ **No OOP/Classes**: Pure functional approach
- ✅ **Clean Separation**: Utils → Services → Routes
- ✅ **Small Files**: All files under 120 lines
- ✅ **Type Safe**: Full TypeScript support
- ✅ **Smart Logging**: JSON logs for easy debugging
- ✅ **Graceful Shutdown**: Clean disconnection on exit

## Next Steps

1. Test the authentication flow with your own phone
2. Try sending messages to different targets
3. Fetch unread messages from various sources
4. Explore the Postman collection for more examples
5. Check logs for debugging information

## Support

For issues:
1. Check the logs in JSON format
2. Verify your API credentials
3. Ensure proper phone number format (+country code)
4. Check that sessions are properly saved in `data/`
