import { TelegramClient } from 'telegram';
import { StringSession } from 'telegram/sessions';
import * as logger from '../utils/logger';
import * as phoneStorage from '../utils/phoneStorage';

const activeClients = new Map<string, any>();

export async function loadAllSessions(): Promise<void> {
  logger.info('Loading existing sessions');
  
  const phones = phoneStorage.listAllPhones();
  
  for (const phone of phones) {
    try {
      await loadSession(phone);
    } catch (err: any) {
      logger.warn('Failed to load session', { phone, error: err.message });
    }
  }
  
  logger.info('Sessions loaded', { count: activeClients.size });
}

export async function loadSession(phone: string): Promise<any | null> {
  const existing = activeClients.get(phone);
  if (existing) {
    logger.debug('Session already loaded', { phone });
    return existing;
  }
  
  const phoneData = phoneStorage.loadPhoneData(phone);
  
  if (!phoneData || !phoneData.session || !phoneData.verified) {
    logger.debug('No valid session found', { phone });
    return null;
  }
  
  try {
    const client = new TelegramClient(
      new StringSession(phoneData.session),
      phoneData.apiId,
      phoneData.apiHash,
      { connectionRetries: 3 }
    );
    
    await client.connect();
    activeClients.set(phone, client);
    
    logger.info('Session loaded and connected', { phone });
    return client;
  } catch (err: any) {
    logger.error('Failed to connect session', { phone, error: err.message });
    return null;
  }
}

export function getClient(phone: string): any | null {
  return activeClients.get(phone) || null;
}

export function setClient(phone: string, client: any): void {
  activeClients.set(phone, client);
  logger.debug('Client stored in memory', { phone });
}

export function removeClient(phone: string): void {
  activeClients.delete(phone);
  logger.debug('Client removed from memory', { phone });
}

export async function disconnectClient(phone: string): Promise<void> {
  const client = activeClients.get(phone);
  
  if (client) {
    try {
      await client.disconnect();
      activeClients.delete(phone);
      logger.info('Client disconnected', { phone });
    } catch (err: any) {
      logger.error('Failed to disconnect client', { phone, error: err.message });
    }
  }
}

export async function disconnectAll(): Promise<void> {
  logger.info('Disconnecting all clients', { count: activeClients.size });
  
  const promises = Array.from(activeClients.keys()).map(phone => 
    disconnectClient(phone).catch(err => 
      logger.error('Error during disconnect', { phone, error: err.message })
    )
  );
  
  await Promise.all(promises);
  activeClients.clear();
  
  logger.info('All clients disconnected');
}

export function isAuthenticated(phone: string): boolean {
  const client = activeClients.get(phone);
  return client !== undefined;
}

export function getActivePhones(): string[] {
  return Array.from(activeClients.keys());
}

export function getActiveClientCount(): number {
  return activeClients.size;
}



