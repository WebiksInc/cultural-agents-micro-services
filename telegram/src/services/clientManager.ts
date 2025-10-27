import { TelegramClient } from 'telegram';
import { readConfig } from '../utils/fileSystem';
import { PhoneConfig } from '../types';
import { createClient } from './clientFactory';

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

