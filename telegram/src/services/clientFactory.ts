import { TelegramClient } from 'telegram';
import { StringSession } from 'telegram/sessions';
import { PhoneConfig } from '../types';
import { getSessionPath, ensureSessionsDir } from '../utils/sessionManager';
import * as fs from 'fs';

const clients = new Map<string, TelegramClient>();

export async function createClient(
  config: PhoneConfig
): Promise<TelegramClient> {
  ensureSessionsDir();
  
  const sessionPath = getSessionPath(config.phone);
  let sessionString = '';
  
  if (fs.existsSync(sessionPath)) {
    sessionString = fs.readFileSync(sessionPath, 'utf-8');
  }
  
  const session = new StringSession(sessionString);
  
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
