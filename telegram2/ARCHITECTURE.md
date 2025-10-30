# Telegram2 Service Architecture

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT REQUEST                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EXPRESS SERVER                              │
│                     (src/server.ts)                              │
│  • JSON body parsing                                             │
│  • Route mounting (/api)                                         │
│  • Health endpoint                                               │
│  • Graceful shutdown                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ROUTES LAYER                             │
│                    (src/routes/*.ts)                             │
├─────────────────────────────────────────────────────────────────┤
│  authRoutes.ts          messageRoutes.ts      unreadRoutes.ts   │
│  • /auth/send-code      • /messages/send      • /messages/unread│
│  • /auth/verify-code                                             │
│                                                                  │
│  Responsibilities:                                               │
│  • Parse request                                                 │
│  • Validate inputs (using validators.ts)                        │
│  • Call service functions                                        │
│  • Format response                                               │
│  • Handle errors                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SERVICES LAYER                             │
│                   (src/services/*.ts)                            │
├─────────────────────────────────────────────────────────────────┤
│  authService.ts                                                  │
│  • sendCode(phone, apiId, apiHash)                              │
│  • verifyCode(phone, code)                                      │
│                                                                  │
│  messageService.ts                                               │
│  • sendMessage(fromPhone, toTarget, message)                    │
│                                                                  │
│  unreadService.ts                                                │
│  • getUnreadMessages(accountPhone, target)                      │
│                                                                  │
│  sessionManager.ts                                               │
│  • loadAllSessions()                                             │
│  • loadSession(phone)                                            │
│  • getClient(phone)                                              │
│  • setClient(phone, client)                                     │
│  • disconnectAll()                                               │
│                                                                  │
│  Responsibilities:                                               │
│  • Business logic                                                │
│  • Telegram API interaction                                      │
│  • Session management                                            │
│  • Error handling                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│     UTILS LAYER          │  │   TELEGRAM (GramJS)      │
│   (src/utils/*.ts)       │  │                          │
├──────────────────────────┤  │  • TelegramClient        │
│  logger.ts               │  │  • StringSession         │
│  • debug()               │  │  • Api.auth.SendCode     │
│  • info()                │  │  • Api.auth.SignIn       │
│  • warn()                │  │  • getMessages()         │
│  • error()               │  │  • sendMessage()         │
│                          │  │  • markAsRead()          │
│  phoneStorage.ts         │  └──────────────────────────┘
│  • savePhoneData()       │
│  • loadPhoneData()       │
│  • updatePhoneData()     │
│  • listAllPhones()       │
│                          │
│  validators.ts           │
│  • validatePhone()       │
│  • validateApiCreds()    │
│  • validateCode()        │
│  • validateMessage()     │
│  • validateTarget()      │
└──────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PERSISTENT STORAGE                          │
│                     (telegram2/data/)                            │
├─────────────────────────────────────────────────────────────────┤
│  phone_+1234567890.json                                          │
│  {                                                               │
│    "phone": "+1234567890",                                       │
│    "apiId": 12345,                                               │
│    "apiHash": "abc...",                                          │
│    "session": "session_string...",                               │
│    "verified": true,                                             │
│    "lastAuthAt": "2025-10-29T..."                                │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Examples

### 1. Authentication Flow

```
User Request → Routes → Services → Utils → Telegram API → Storage
────────────────────────────────────────────────────────────────────

Step 1: Send Code
POST /api/auth/send-code
  ↓
authRoutes.ts (validate input)
  ↓
authService.sendCode()
  ↓
sessionManager.getClient() → new TelegramClient()
  ↓
Telegram API: Api.auth.SendCode()
  ↓
phoneStorage.savePhoneData() → data/phone_+123.json
  ↓
Response: { phoneCodeHash }

Step 2: Verify Code
POST /api/auth/verify-code
  ↓
authRoutes.ts (validate input)
  ↓
authService.verifyCode()
  ↓
phoneStorage.loadPhoneData() → read JSON
  ↓
Telegram API: Api.auth.SignIn()
  ↓
Get session string from client
  ↓
phoneStorage.updatePhoneData() → update JSON
  ↓
sessionManager.setClient() → store in memory
  ↓
Response: { success: true, user }
```

### 2. Send Message Flow

```
User Request → Routes → Services → Telegram API
──────────────────────────────────────────────────

POST /api/messages/send
  ↓
messageRoutes.ts (validate input)
  ↓
messageService.sendMessage()
  ↓
sessionManager.getClient() → get from memory
  │ (if not in memory)
  └→ sessionManager.loadSession() → read JSON → connect
  ↓
client.checkAuthorization()
  ↓
client.sendMessage(target, { message })
  ↓
Response: { success: true, sentTo }
```

### 3. Get Unread Messages Flow

```
User Request → Routes → Services → Telegram API
──────────────────────────────────────────────────

GET /api/messages/unread
  ↓
unreadRoutes.ts (validate input)
  ↓
unreadService.getUnreadMessages()
  ↓
sessionManager.getClient() or loadSession()
  ↓
client.getEntity(target)
  ↓
client.getDialogs() → find dialog → get unreadCount
  ↓
client.getMessages(entity, limit: unreadCount)
  ↓
Filter: messages.filter(m => !m.out)
  ↓
client.markAsRead(entity) ← AUTO MARK AS READ
  ↓
Response: { unread: [...], count }
```

## Memory Management

```
┌─────────────────────────────────────────┐
│         IN-MEMORY STORAGE               │
│    (sessionManager activeClients)       │
├─────────────────────────────────────────┤
│  Map<phone, TelegramClient>             │
│  ┌─────────────────────────────────┐    │
│  │ "+1234567890" → Client A        │    │
│  │ "+9876543210" → Client B        │    │
│  │ "+1111111111" → Client C        │    │
│  └─────────────────────────────────┘    │
│                                          │
│  Lifecycle:                              │
│  • Created on sendCode()                 │
│  • Stored on verifyCode()                │
│  • Loaded on startup                     │
│  • Reused for all operations             │
│  • Disconnected on shutdown              │
└─────────────────────────────────────────┘
```

## File Dependencies

```
server.ts
  └── routes/index.ts
       ├── authRoutes.ts
       │    ├── authService.ts
       │    │    ├── sessionManager.ts
       │    │    │    ├── phoneStorage.ts
       │    │    │    │    └── logger.ts
       │    │    │    └── logger.ts
       │    │    └── phoneStorage.ts
       │    ├── validators.ts
       │    └── logger.ts
       │
       ├── messageRoutes.ts
       │    ├── messageService.ts
       │    │    ├── sessionManager.ts
       │    │    └── logger.ts
       │    ├── validators.ts
       │    └── logger.ts
       │
       └── unreadRoutes.ts
            ├── unreadService.ts
            │    ├── sessionManager.ts
            │    └── logger.ts
            ├── validators.ts
            └── logger.ts
```

## Functional Programming Patterns

### No Classes - Pure Functions

```typescript

class SessionManager {
  private clients = new Map();
  getClient() { ... }
  setClient() { ... }
}
const manager = new SessionManager();

// ✅ Functional Approach (USED)
const activeClients = new Map();
export function getClient(phone) { ... }
export function setClient(phone, client) { ... }
```

### Module-Level State

```typescript
// State encapsulated in module
const activeClients = new Map<string, any>();

// Exported functions operate on state
export function getClient(phone: string) {
  return activeClients.get(phone) || null;
}

export function setClient(phone: string, client: any) {
  activeClients.set(phone, client);
}
```

### Composition over Inheritance

```typescript
// Services compose utilities
import * as logger from '../utils/logger';
import * as phoneStorage from '../utils/phoneStorage';

export async function sendCode(...) {
  logger.info('Sending code', { phone });
  phoneStorage.savePhoneData(data);
  return result;
}
```

## Error Handling Strategy

```
┌─────────────────────────────────────────┐
│         ERROR PROPAGATION               │
└─────────────────────────────────────────┘

Validators (throw ValidationError)
  ↓
Routes (catch → 400 response)

Services (throw Error)
  ↓
Routes (catch → 400/500 response)

Utils (throw Error)
  ↓
Services (catch/propagate)
  ↓
Routes (catch → 400/500 response)

All responses in format:
{
  "success": false,
  "error": "Clear message"
}
```

## Logging Strategy

```
Level     | Use Case                    | Example
──────────┼────────────────────────────┼────────────────────────
DEBUG     | Development details         | "Session already loaded"
INFO      | Important events            | "Code sent successfully"
WARN      | Recoverable issues          | "Failed to load session"
ERROR     | Critical failures           | "Failed to connect"

All logs include:
• timestamp
• level
• message
• context (phone, target, error, etc.)
```

## Key Design Decisions

1. **No Classes**: Pure functional approach for simplicity
2. **Per-Phone Files**: Isolated data, easy to manage
3. **Auto Mark as Read**: Convenient for most use cases
4. **JSON Logging**: Structured, parseable logs
5. **Module Exports**: Simple, straightforward API
6. **Type Safety**: Full TypeScript for reliability
7. **Small Files**: < 120 lines for maintainability
8. **Clear Separation**: Utils/Services/Routes pattern

## Performance Considerations

- ✅ Sessions kept in memory (fast access)
- ✅ Lazy loading (connect only when needed)
- ✅ Graceful shutdown (clean disconnection)
- ✅ Atomic file writes (temp file + rename)
- ✅ Non-blocking session loading (async)
- ✅ Reusable connections (per phone)

## Security Considerations

- ✅ Credentials stored locally (not in code)
- ✅ Session strings encrypted by Telegram
- ✅ No password storage (Telegram handles)
- ✅ Input validation on all endpoints
- ✅ Type safety prevents injection
- ✅ Graceful error messages (no leaks)

---

**Architecture Status**: ✅ Clean & Functional  
**Pattern**: Utils → Services → Routes  
**Paradigm**: Functional Programming (No OOP)  
**Type Safety**: Full TypeScript
