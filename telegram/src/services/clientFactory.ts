import { TelegramClient } from 'telegram';
import { StringSession } from 'telegram/sessions';
import { PhoneConfig } from '../types';
import { getSessionPath, ensureSessionsDir } from '../utils/sessionManager';

const clients = new Map<string, TelegramClient>();

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
