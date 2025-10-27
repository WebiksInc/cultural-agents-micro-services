# Postman Collection Usage Guide

## Import Instructions

1. Open Postman
2. Click **Import** button (top left)
3. Select the file: `telegram/Telegram-API.postman_collection.json`
4. Collection will appear in your Collections sidebar

## Configuration

### Collection Variables (Modify these before testing)

Click on the collection → **Variables** tab:

- `baseUrl`: `http://localhost:8005` (default)
- `phone`: Your phone number with country code (e.g., `+1234567890`)
- `apiId`: Your Telegram API ID from https://my.telegram.org
- `apiHash`: Your Telegram API Hash from https://my.telegram.org
- `receiverPhone`: Target phone number to send messages to

## Testing Workflow

### 1. Authentication Flow (Run in order)

#### Step 1: Save Credentials
- **Endpoint**: POST `/auth/credentials`
- **Action**: Stores your phone + API credentials
- **Before running**: Update `apiId` and `apiHash` variables
- **Expected**: `200 OK` with credentials saved

#### Step 2: Start Authentication
- **Endpoint**: POST `/auth/start`
- **Action**: Triggers Telegram to send verification code
- **Check**: Your Telegram app for the code
- **Expected**: `200 OK` with `phoneCodeHash` (auto-saved to variables)

#### Step 3: Verify Code
- **Endpoint**: POST `/auth/verify`
- **Action**: Verifies the code from Telegram
- **Before running**: Replace `12345` in the body with your actual code
- **Expected**: `200 OK` - You're now authenticated!

### 2. Messaging (After authentication)

#### Send Message
- **Endpoint**: POST `/send`
- **Action**: Send a message to another user
- **Before running**: Set `receiverPhone` variable
- **Expected**: `200 OK` with success message

#### Get Messages by Phone
- **Endpoint**: GET `/get`
- **Action**: Fetch unread messages from a conversation
- **Query params**: `phone`, `chatPhone`
- **Expected**: `200 OK` with message array

#### Get Messages by Chat ID
- **Endpoint**: GET `/get`
- **Action**: Fetch messages using Telegram chat ID
- **Query params**: `phone`, `chatId`
- **Expected**: `200 OK` with message array

### 3. Error Scenarios

Test error handling:
- **Send Without Auth**: Should return authentication error
- **Get Messages Without Auth**: Should return authentication error
- **Missing Required Fields**: Should return 400 validation error

## Response Examples

### Success Response
```json
{
  "success": true,
  "message": "Message sent successfully",
  "data": null
}
```

### Error Response
```json
{
  "success": false,
  "error": "Sender not authenticated"
}
```

### Messages Response
```json
{
  "success": true,
  "message": "Messages retrieved",
  "data": [
    {
      "id": 12345,
      "senderId": "987654321",
      "text": "Hello!",
      "timestamp": "2025-10-27T12:34:56.000Z"
    }
  ]
}
```

## Troubleshooting

### Can't connect to service
```bash
# Check if service is running
docker-compose ps

# Start the service
docker-compose up telegram
```

### Authentication fails
- Verify API credentials from https://my.telegram.org
- Ensure phone number includes country code (+...)
- Check that you entered the correct verification code

### Messages not appearing
- Ensure sender is authenticated
- Verify receiver phone number format
- Check that conversation exists in Telegram
