import { TelegramClient } from 'telegram';
import { readConfig } from '../utils/fileSystem';
import { PhoneConfig } from '../types';
import { createClient } from './clientFactory';


const pendingClients = new Map<string, TelegramClient>();

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

export function getPendingClient(phone: string): TelegramClient | undefined {
  return pendingClients.get(phone);
}

