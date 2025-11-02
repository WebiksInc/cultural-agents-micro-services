# Environment Variables Configuration

This document describes all environment variables supported by the Telegram2 service.

## Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your preferred values

3. The service automatically loads `.env` on startup

## Environment Variables

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

## Usage Examples

### Development Environment
```bash
# .env
PORT=4000
NODE_ENV=development
LOG_LEVEL=debug
DATA_DIR=./data
AUTO_LOAD_SESSIONS=true
```

### Production Environment
```bash
# .env
PORT=8080
NODE_ENV=production
LOG_LEVEL=info
DATA_DIR=/app/data
AUTO_LOAD_SESSIONS=true
CONNECTION_RETRIES=5
SHUTDOWN_TIMEOUT=15000
```

### Docker Environment
```bash
# .env
PORT=4000
NODE_ENV=production
LOG_LEVEL=warn
DATA_DIR=/app/sessions
AUTO_LOAD_SESSIONS=true
TELEGRAM_API_ID=12345
TELEGRAM_API_HASH=your_api_hash_here
```

## New API Endpoints

### Configuration Endpoint
```
GET /config
```

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

### Enhanced Health Endpoint
```
GET /health
```

Returns enhanced health information:
```json
{
  "success": true,
  "message": "Service is healthy",
  "version": "0.1.0",
  "environment": "development",
  "port": 4000
}
```

## Log Level Behavior

- **`debug`**: All log messages (debug, info, warn, error)
- **`info`**: Info, warn, and error messages
- **`warn`**: Only warn and error messages  
- **`error`**: Only error messages

## Data Directory

The `DATA_DIR` variable controls where phone session files are stored:
- Relative paths are resolved from the project root
- Absolute paths are used as-is
- Directory is created automatically if it doesn't exist
- Files are named `phone_+1234567890.json`

## Default API Credentials

If you set `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`, these will be used as defaults, but can still be overridden in individual API requests to `/api/auth/send-code`.

## Migration from Previous Version

The service remains fully backward compatible. No changes needed to existing:
- API calls
- Data files
- Authentication flow
- Session persistence

All previous functionality works exactly the same, just with added configurability.

## Testing Configuration

Test your configuration by running:
```bash
curl http://localhost:4000/config
```

This will show your current settings without exposing sensitive values.