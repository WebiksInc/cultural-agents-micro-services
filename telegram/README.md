# Telegram Microservice

TypeScript-based microservice for Telegram authentication and messaging using GramJS.

## Setup

### Install Dependencies

```bash
cd telegram
npm install
```

### Build

```bash
npm run build
```

### Run with Docker

```bash
docker-compose up --build
```

## API Endpoints

### 1. Save Credentials

**POST** `/auth/credentials`

Save phone number with API credentials.

```json
{
  "phone": "+1234567890",
  "apiId": 12345,
  "apiHash": "your_api_hash"
}
```

### 2. Start Authentication

**POST** `/auth/start`

Initiate authentication and receive verification code.

```json
{
  "phone": "+1234567890"
}
```

### 3. Verify Code

**POST** `/auth/verify`

Submit verification code from Telegram.

```json
{
  "phone": "+1234567890",
  "code": "12345",
  "phoneCodeHash": "hash_from_start_response"
}
```

### 4. Send Message

**POST** `/send`

Send a message to another user.

```json
{
  "senderPhone": "+1234567890",
  "receiverPhone": "+0987654321",
  "message": "Hello!"
}
```

### 5. Get Unread Messages

**GET** `/get?phone=+1234567890&chatPhone=+0987654321`

Retrieve and mark unread messages as read.

Query parameters:
- `phone`: Your phone number
- `chatId`: Chat ID or
- `chatPhone`: Contact phone number

## Configuration

Credentials stored in: `./config/phone_+123.json`
Sessions stored in: `./sessions/session_+123`

## Port

Service runs on port **8005**
