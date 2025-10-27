# Complete Beginner's Guide to the Telegram Microservice

## Table of Contents
1. [What is This Project?](#what-is-this-project)
2. [Understanding the Architecture](#understanding-the-architecture)
3. [File Structure Explained](#file-structure-explained)
4. [Code Walkthrough - File by File](#code-walkthrough)
5. [How It All Works Together](#how-it-all-works-together)

---

## What is This Project?

This is a **microservice** - a small, independent application that does ONE specific job: managing Telegram messaging through an API.

**What does it do?**
- Lets users authenticate with their Telegram account
- Sends messages to other Telegram users
- Retrieves unread messages from conversations

**Why is it useful?**
Instead of manually opening Telegram, you can automate messaging through HTTP requests (like Postman or curl).

---

## Understanding the Architecture

### What is a Microservice?

Think of it like a restaurant:
- **Monolithic app** = One chef does everything (cooking, serving, cleaning)
- **Microservice** = Specialized workers (one cooks, one serves, one cleans)

This Telegram service is ONE specialized worker that only handles Telegram operations.

### The Three-Layer Architecture

Our service has 3 layers, like a sandwich:

```
┌─────────────────────────────────────┐
│  ROUTES (Top Layer)                 │  ← Receives HTTP requests
│  "What endpoints can users access?" │
├─────────────────────────────────────┤
│  SERVICES (Middle Layer)            │  ← Business logic
│  "What actions can we perform?"     │
├─────────────────────────────────────┤
│  UTILS (Bottom Layer)               │  ← Helper functions
│  "Reusable tools everyone needs"    │
└─────────────────────────────────────┘
```

**Why separate layers?**
- **Organization**: Easy to find code
- **Reusability**: Same functions used everywhere
- **Maintainability**: Fix one place, fixes everywhere
- **Testing**: Test each layer independently

---

## File Structure Explained

```
telegram/
├── src/                          # All TypeScript source code
│   ├── types/                    # Type definitions (data shapes)
│   │   └── index.ts             # Interfaces for our data
│   │
│   ├── utils/                    # Helper functions (reusable tools)
│   │   ├── fileSystem.ts        # Read config files
│   │   ├── configWriter.ts      # Write config files
│   │   ├── sessionManager.ts    # Manage Telegram sessions
│   │   └── response.ts          # Format HTTP responses
│   │
│   ├── services/                 # Business logic (the "brain")
│   │   ├── clientFactory.ts     # Create Telegram clients
│   │   ├── clientManager.ts     # Manage active clients
│   │   ├── configService.ts     # Save credentials
│   │   ├── authInitiator.ts     # Start authentication
│   │   ├── codeVerifier.ts      # Verify auth codes
│   │   ├── messageSender.ts     # Send messages
│   │   ├── messageFetcher.ts    # Get messages
│   │   └── messageReader.ts     # Mark messages as read
│   │
│   ├── routes/                   # API endpoints (entry points)
│   │   ├── credentialsRoute.ts  # POST /auth/credentials
│   │   ├── authStartRoute.ts    # POST /auth/start
│   │   ├── verifyRoute.ts       # POST /auth/verify
│   │   ├── sendRoute.ts         # POST /send
│   │   └── getRoute.ts          # GET /get
│   │
│   └── server.ts                 # Main app (connects everything)
│
├── dist/                         # Compiled JavaScript (TypeScript → JS)
├── config/                       # Stored credentials (generated)
├── sessions/                     # Telegram sessions (generated)
├── package.json                  # Dependencies list
├── tsconfig.json                 # TypeScript settings
├── Dockerfile                    # How to build Docker image
└── docker-compose.yml            # How to run container
```

---

## Code Walkthrough - File by File

### 1. Types (`src/types/index.ts`)

**What are types?**
Think of types as "blueprints" or "contracts" that define what data looks like.

```typescript
export interface PhoneConfig {
  phone: string;
  apiId: number;
  apiHash: string;
  verified: boolean;
}
```

**Translation:**
"A PhoneConfig object MUST have exactly these 4 properties with these data types."

**Why?**
- **Prevents errors**: TypeScript checks if you use data correctly
- **Documentation**: You know what each object contains
- **Auto-complete**: Your editor suggests available properties

**Example:**
```typescript
// ✅ Valid
const config: PhoneConfig = {
  phone: "+123",
  apiId: 12345,
  apiHash: "abc",
  verified: false
};

// ❌ Invalid - TypeScript will show an error
const bad: PhoneConfig = {
  phone: 123,  // Wrong! Should be string
  // Missing required fields!
};
```

---

### 2. Utils - The Toolbox

Think of utils as a toolbox with screwdrivers, hammers, etc. that everyone uses.

#### `fileSystem.ts` - Reading Files

```typescript
export function getConfigPath(phone: string): string {
  const sanitized = phone.replace(/[^0-9+]/g, '');
  return path.join(CONFIG_DIR, `phone_${sanitized}.json`);
}
```

**What does this do?**
1. Takes a phone number like "+1 (234) 567-890"
2. Removes everything except numbers and + → "+1234567890"
3. Creates a file path: `config/phone_+1234567890.json`

**Why?**
We need a consistent, safe filename for each phone number.

```typescript
export function readConfig<T>(phone: string): T | null {
  try {
    const configPath = getConfigPath(phone);
    if (!fs.existsSync(configPath)) {
      return null;
    }
    const data = fs.readFileSync(configPath, 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    return null;
  }
}
```

**What does this do?**
1. Get the file path for this phone
2. Check if file exists
3. Read the file content
4. Parse JSON text into a JavaScript object
5. Return it (or null if something fails)

**The `<T>` magic:**
This is a **generic**. It means "I can read ANY type of data you tell me about."
```typescript
const config = readConfig<PhoneConfig>("+123");  // Returns PhoneConfig or null
```

---

#### `configWriter.ts` - Writing Files

```typescript
export function writeConfig<T>(phone: string, data: T): void {
  ensureConfigDir();
  const configPath = getConfigPath(phone);
  fs.writeFileSync(configPath, JSON.stringify(data, null, 2));
}
```

**What does this do?**
1. Make sure the `config/` folder exists
2. Get the file path
3. Convert JavaScript object to JSON text
4. Write it to the file

**The `null, 2` part:**
Makes JSON pretty (indented) instead of one long line.

```json
// With null, 2:
{
  "phone": "+123",
  "apiId": 12345
}

// Without it:
{"phone":"+123","apiId":12345}
```

---

#### `sessionManager.ts` - Session Paths

**What's a session?**
When you log into Telegram, it creates a "session" - proof that you're logged in. Like a ticket to enter a concert.

```typescript
export function getSessionPath(phone: string): string {
  const sanitized = phone.replace(/[^0-9+]/g, '');
  return path.join(SESSIONS_DIR, `session_${sanitized}`);
}
```

Same idea as config paths, but for session files.

---

#### `response.ts` - HTTP Responses

**What's an HTTP response?**
When someone sends a request to your API, you send back a response with data.

```typescript
export function sendError(
  res: Response,
  statusCode: number,
  message: string
): void {
  res.status(statusCode).json({
    success: false,
    error: message,
  });
}
```

**What does this do?**
Sends a consistent error format:
```json
{
  "success": false,
  "error": "User not authenticated"
}
```

**Why consistent format?**
The client (Postman, app, etc.) always knows what to expect.

---

### 3. Services - The Brain

Services contain the **business logic** - the actual work of the application.

#### `clientFactory.ts` - Creating Telegram Clients

```typescript
export async function createClient(
  config: PhoneConfig
): Promise<TelegramClient> {
  ensureSessionsDir();
  
  const sessionPath = getSessionPath(config.phone);
  const session = new StringSession('');
  
  const client = new TelegramClient(
    session,
    config.apiId,
    config.apiHash,
    {
      connectionRetries: 5,
    }
  );
  
  return client;
}
```

**What's a Telegram client?**
It's an object that can talk to Telegram's servers. Like a phone that can make calls.

**What does this do?**
1. Make sure sessions folder exists
2. Create an empty session
3. Create a new Telegram client with the user's API credentials
4. Return it

**`async` and `Promise`:**
- `async` = "This function takes time (waits for things)"
- `Promise` = "I promise to give you a result later"

Think of ordering pizza:
```typescript
// ❌ Synchronous (blocks everything)
const pizza = makePizza();  // Wait 30 minutes doing nothing

// ✅ Asynchronous (do other things while waiting)
const pizzaPromise = orderPizza();  // Order and continue
// Do other stuff...
const pizza = await pizzaPromise;  // Pick it up when ready
```

---

#### `clientManager.ts` - Managing Active Clients

```typescript
const activeClients = new Map<string, TelegramClient>();

export async function getClient(
  phone: string
): Promise<TelegramClient | null> {
  if (activeClients.has(phone)) {
    return activeClients.get(phone)!;
  }
  
  const config = readConfig<PhoneConfig>(phone);
  if (!config || !config.verified) {
    return null;
  }
  
  const client = await createClient(config);
  activeClients.set(phone, client);
  return client;
}
```

**What's a Map?**
A dictionary/phonebook that stores key-value pairs:
```typescript
activeClients.set("+123", clientObject);  // Store
activeClients.get("+123");                // Retrieve
activeClients.has("+123");                // Check if exists
```

**What does this function do?**
1. Check if we already have a client for this phone (cached)
2. If yes, return it immediately
3. If no, check if phone is verified
4. Create a new client
5. Store it in cache
6. Return it

**Why cache clients?**
Creating a client is slow. Reusing is fast.

---

#### `configService.ts` - Saving Credentials

```typescript
export function savePhoneCredentials(
  phone: string,
  apiId: number,
  apiHash: string
): PhoneConfig {
  ensureConfigDir();
  
  const config: PhoneConfig = {
    phone,
    apiId,
    apiHash,
    verified: false,
  };
  
  writeConfig(phone, config);
  return config;
}
```

**What does this do?**
1. Make sure config folder exists
2. Create a PhoneConfig object
3. Set `verified: false` (not authenticated yet)
4. Save it to a file
5. Return the config

**Note the shorthand:**
```typescript
// Instead of:
const config = {
  phone: phone,
  apiId: apiId,
  apiHash: apiHash,
  verified: false
};

// We can write:
const config = {
  phone,      // Same as phone: phone
  apiId,      // Same as apiId: apiId
  apiHash,    // Same as apiHash: apiHash
  verified: false
};
```

---

#### `authInitiator.ts` - Starting Authentication

```typescript
export async function startAuth(
  phone: string
): Promise<{ phoneCodeHash: string } | null> {
  const config = readConfig<PhoneConfig>(phone);
  
  if (!config) {
    return null;
  }
  
  const client = await createClient(config);
  await client.connect();
  
  pendingClients.set(phone, client);
  
  const result = await client.sendCode(
    {
      apiId: config.apiId,
      apiHash: config.apiHash,
    },
    phone
  );
  
  return { phoneCodeHash: result.phoneCodeHash };
}
```

**What does this do?**
1. Read the saved credentials
2. If no credentials, return null (error)
3. Create a Telegram client
4. Connect to Telegram servers
5. Store client for later use
6. Ask Telegram to send a verification code to the phone
7. Return a hash (you need this to verify the code later)

**Flow:**
```
User → POST /auth/start → This function → Telegram servers
                                          ↓
                                    Code sent to user's phone
```

---

#### `codeVerifier.ts` - Verifying the Code

```typescript
export async function verifyCode(
  phone: string,
  code: string,
  phoneCodeHash: string
): Promise<boolean> {
  const config = readConfig<PhoneConfig>(phone);
  
  if (!config) {
    return false;
  }
  
  try {
    const client = await createClient(config);
    await client.connect();
    
    await client.start({
      phoneNumber: phone,
      phoneCode: async () => code,
      onError: (err) => console.error(err),
    });
    
    updateConfig<PhoneConfig>(phone, { verified: true });
    await client.disconnect();
    return true;
  } catch (error: any) {
    if (error.code === 420) {
      const waitMinutes = Math.ceil(error.seconds / 60);
      throw new Error(
        `Too many attempts. Please wait ${waitMinutes} minutes`
      );
    }
    return false;
  }
}
```

**What does this do?**
1. Read credentials
2. Create and connect client
3. Start authentication with the code
4. If successful, mark as verified in config
5. Disconnect
6. Return true

**Error handling:**
- If error code is 420 (FloodWait), calculate wait time and throw a helpful message
- Otherwise, return false

**`try-catch`:**
```typescript
try {
  // Try to do something risky
} catch (error) {
  // If it fails, handle the error
}
```

---

#### `messageSender.ts` - Sending Messages

```typescript
export async function sendMessage(
  senderPhone: string,
  receiverPhone: string,
  message: string
): Promise<boolean> {
  const client = await getClient(senderPhone);
  
  if (!client) {
    throw new Error('Sender not authenticated');
  }
  
  try {
    await client.sendMessage(receiverPhone, { message });
    return true;
  } catch (error) {
    throw new Error('Failed to send message');
  }
}
```

**What does this do?**
1. Get the sender's Telegram client
2. If sender not authenticated, throw error
3. Try to send the message
4. If successful, return true
5. If fails, throw error

**`throw new Error()`:**
This stops the function and sends an error up to whoever called it.

---

#### `messageFetcher.ts` - Getting Messages

```typescript
export async function getUnreadMessages(
  phone: string,
  chatIdentifier: string
): Promise<Message[]> {
  const client = await getClient(phone);
  
  if (!client) {
    throw new Error('User not authenticated');
  }
  
  try {
    const messages = await client.getMessages(chatIdentifier, {
      limit: 100,
    });
    
    const unread = messages.filter((msg: any) => !msg.out);
    
    return unread.map((msg: any) => ({
      id: msg.id,
      senderId: msg.fromId?.userId?.toString() || 'unknown',
      text: msg.message || '',
      timestamp: new Date(msg.date * 1000),
    }));
  } catch (error) {
    throw new Error('Failed to fetch messages');
  }
}
```

**What does this do?**
1. Get user's client
2. Fetch up to 100 messages from the chat
3. Filter out messages sent by us (`!msg.out` = not outgoing)
4. Transform each message into our Message format
5. Return the array

**`filter()`:**
Keeps only items that match a condition:
```typescript
const numbers = [1, 2, 3, 4, 5];
const evens = numbers.filter(n => n % 2 === 0);  // [2, 4]
```

**`map()`:**
Transforms each item:
```typescript
const numbers = [1, 2, 3];
const doubled = numbers.map(n => n * 2);  // [2, 4, 6]
```

---

#### `messageReader.ts` - Marking as Read

```typescript
export async function markAsRead(
  phone: string,
  chatIdentifier: string,
  messageIds: number[]
): Promise<void> {
  const client = await getClient(phone);
  
  if (!client) {
    throw new Error('User not authenticated');
  }
  
  try {
    await client.markAsRead(chatIdentifier);
  } catch (error) {
    throw new Error('Failed to mark messages as read');
  }
}
```

**What does this do?**
1. Get user's client
2. Tell Telegram to mark all messages in this chat as read
3. If fails, throw error

**`Promise<void>`:**
This function doesn't return anything (void), but it's async so it returns a Promise.

---

### 4. Routes - The Front Door

Routes are the **entry points** - the URLs users can access.

#### `credentialsRoute.ts`

```typescript
const router = Router();

router.post('/', async (req: Request, res: Response) => {
  try {
    const { phone, apiId, apiHash } = req.body;
    
    if (!phone || !apiId || !apiHash) {
      return sendError(res, 400, 'Missing required fields');
    }
    
    const config = savePhoneCredentials(phone, apiId, apiHash);
    sendSuccess(res, config, 'Credentials saved successfully');
  } catch (error) {
    sendError(res, 500, 'Failed to save credentials');
  }
});

export default router;
```

**What's a Router?**
A router handles different URL paths. Like a receptionist directing visitors.

**Breaking it down:**

1. **`Router()`**: Creates a new router
2. **`router.post('/')`**: Handle POST requests to this route
3. **`async (req, res) => {}`**: The handler function
   - `req` = Request (incoming data)
   - `res` = Response (what we send back)
4. **`const { phone, apiId, apiHash } = req.body`**: Destructuring
   - Extract these fields from the request body
5. **Validation**: Check if all fields exist
6. **Call service**: `savePhoneCredentials()` does the actual work
7. **Send response**: Use our helper to send JSON

**Flow:**
```
POST /auth/credentials
  ↓
Extract data from request body
  ↓
Validate data
  ↓
Call service to save
  ↓
Send success response
```

---

### 5. Server - The Main Hub

```typescript
import express, { Express } from 'express';
import credentialsRoute from './routes/credentialsRoute';
import authStartRoute from './routes/authStartRoute';
import verifyRoute from './routes/verifyRoute';
import sendRoute from './routes/sendRoute';
import getRoute from './routes/getRoute';

const app: Express = express();
const PORT = process.env.PORT || 8005;

app.use(express.json());

app.use('/auth/credentials', credentialsRoute);
app.use('/auth/start', authStartRoute);
app.use('/auth/verify', verifyRoute);
app.use('/send', sendRoute);
app.use('/get', getRoute);

app.listen(PORT, () => {
  console.log(`Telegram service running on port ${PORT}`);
});
```

**What's Express?**
A framework for building web servers in Node.js. It handles HTTP requests/responses.

**Breaking it down:**

1. **Import everything**: Get all our routes
2. **Create app**: `express()` creates the server
3. **Get PORT**: Use environment variable or default to 8005
4. **`app.use(express.json())`**: Middleware to parse JSON bodies
5. **Mount routes**: Connect each route to a path
6. **Start listening**: Begin accepting requests on port 8005

**What's middleware?**
Functions that process requests before they reach your routes.

```typescript
Request → Middleware 1 → Middleware 2 → Route Handler → Response
```

**Example:**
```typescript
app.use(express.json());  // Parses JSON automatically

// Without this middleware:
req.body = '{"phone":"+123"}'  // String

// With this middleware:
req.body = { phone: "+123" }   // Object
```

---

## How It All Works Together

### Complete Authentication Flow

```
1. USER: POST /auth/credentials
   {
     "phone": "+123",
     "apiId": 12345,
     "apiHash": "abc"
   }
   ↓
2. SERVER: credentialsRoute receives request
   ↓
3. ROUTE: Validates data, calls configService.savePhoneCredentials()
   ↓
4. SERVICE: Creates PhoneConfig object
   ↓
5. UTILS: configWriter.writeConfig() saves to config/phone_+123.json
   ↓
6. RESPONSE: { success: true, data: {...} }

═══════════════════════════════════════════════════════════

7. USER: POST /auth/start
   {
     "phone": "+123"
   }
   ↓
8. ROUTE: authStartRoute calls authInitiator.startAuth()
   ↓
9. SERVICE: 
   - Reads config file (utils)
   - Creates Telegram client
   - Sends code request to Telegram
   ↓
10. TELEGRAM: Sends SMS with code to user's phone
   ↓
11. RESPONSE: { success: true, data: { phoneCodeHash: "xyz" } }

═══════════════════════════════════════════════════════════

12. USER: Receives SMS code "12345"

13. USER: POST /auth/verify
    {
      "phone": "+123",
      "code": "12345",
      "phoneCodeHash": "xyz"
    }
    ↓
14. ROUTE: verifyRoute calls codeVerifier.verifyCode()
    ↓
15. SERVICE:
    - Creates client
    - Verifies code with Telegram
    - Updates config: verified: true
    ↓
16. RESPONSE: { success: true, message: "Authentication successful" }

═══════════════════════════════════════════════════════════

Now user can send/receive messages!
```

### Sending a Message Flow

```
1. USER: POST /send
   {
     "senderPhone": "+123",
     "receiverPhone": "+456",
     "message": "Hello!"
   }
   ↓
2. ROUTE: sendRoute validates and calls messageSender.sendMessage()
   ↓
3. SERVICE:
   - Calls clientManager.getClient("+123")
   - Client manager checks cache
   - If not cached, reads config and creates client
   ↓
4. SERVICE: Uses client to send message via Telegram API
   ↓
5. TELEGRAM: Delivers message to +456
   ↓
6. RESPONSE: { success: true, message: "Message sent successfully" }
```

---

## Key Concepts Summary

### 1. Separation of Concerns
Each file has ONE job:
- **Routes**: Handle HTTP
- **Services**: Business logic
- **Utils**: Reusable helpers

### 2. Async/Await
Handle operations that take time without blocking:
```typescript
// ❌ Bad - blocks everything
const data = downloadFile();  // Wait...

// ✅ Good - do other things while waiting
const data = await downloadFile();
```

### 3. TypeScript Benefits
- Catch errors before running
- Auto-complete in editor
- Clear documentation

### 4. Error Handling
Always handle errors gracefully:
```typescript
try {
  // Try something
} catch (error) {
  // Handle failure
}
```

### 5. Modularity
Small, focused files are:
- Easier to understand
- Easier to test
- Easier to maintain

---

## Common Patterns You'll See

### 1. Destructuring
```typescript
// Instead of:
const phone = req.body.phone;
const code = req.body.code;

// We write:
const { phone, code } = req.body;
```

### 2. Arrow Functions
```typescript
// Traditional function:
function add(a, b) {
  return a + b;
}

// Arrow function:
const add = (a, b) => a + b;
```

### 3. Template Literals
```typescript
// Instead of:
const msg = "Hello " + name + "!";

// We write:
const msg = `Hello ${name}!`;
```

### 4. Optional Chaining
```typescript
// Instead of:
const id = msg.fromId && msg.fromId.userId;

// We write:
const id = msg.fromId?.userId;  // Returns undefined if fromId is null
```

### 5. Null Coalescing
```typescript
// Use default if null/undefined
const port = process.env.PORT || 8005;
const port = process.env.PORT ?? 8005;  // Newer syntax
```

---

## Next Steps

1. **Read each file** in this order:
   - types/index.ts
   - utils/response.ts
   - utils/fileSystem.ts
   - services/configService.ts
   - routes/credentialsRoute.ts
   - server.ts

2. **Try modifying**:
   - Add a console.log() in a route to see when it's called
   - Add a new field to PhoneConfig
   - Create a new utility function

3. **Experiment**:
   - Use Postman to call endpoints
   - Check the generated config files
   - Read the logs with `docker-compose logs -f telegram`

4. **Resources**:
   - TypeScript: https://www.typescriptlang.org/docs/handbook/intro.html
   - Express: https://expressjs.com/en/starter/basic-routing.html
   - Async/Await: https://javascript.info/async-await

---

## Troubleshooting Guide

**"Cannot find module X"**
→ Run `npm install`

**"Port 8005 already in use"**
→ Another service is using that port, change PORT in docker-compose.yml

**"FloodWaitError"**
→ Telegram rate limit, wait the specified time

**"User not authenticated"**
→ Complete auth flow first (credentials → start → verify)

**Changes not reflected**
→ Rebuild: `npm run build && docker-compose up -d --build telegram`

---

*This guide assumes you're learning. Don't hesitate to ask questions!*
