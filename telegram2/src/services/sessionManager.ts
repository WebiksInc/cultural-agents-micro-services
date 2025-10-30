import * as logger from '../utils/logger';
import * as sessionLoader from './sessionLoader';

const activeClients = new Map<string, any>();

export async function loadAllSessions(): Promise<void> {
  return sessionLoader.loadAllSessions(activeClients);
}

export async function loadSession(phone: string): Promise<any | null> {
  return sessionLoader.loadSession(phone, activeClients);
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
  
  if (!client) {
    return;
  }
  
  try {
    await client.disconnect();
    activeClients.delete(phone);
    logger.info('Client disconnected', { phone });
  } catch (err: any) {
    logger.error('Failed to disconnect client', { phone, error: err.message });
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


