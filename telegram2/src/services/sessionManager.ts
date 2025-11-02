import logger from '../utils/logger';
import sessionLoader from './sessionLoader';

const activeClients = new Map<string, any>();

export const loadAllSessions = async (): Promise<void> => {
  return sessionLoader.loadAllSessions(activeClients);
}

export const loadSession = async (phone: string): Promise<any | null> => {
  return sessionLoader.loadSession(phone, activeClients);
}

export const getClient = (phone: string): any | null => {
  return activeClients.get(phone) || null;
}

export const setClient = (phone: string, client: any): void => {
  activeClients.set(phone, client);
  logger.debug('Client stored in memory', { phone });
}

export const removeClient = (phone: string): void => {
  activeClients.delete(phone);
  logger.debug('Client removed from memory', { phone });
}

export const disconnectClient = async (phone: string): Promise<void> => {
  const client = activeClients.get(phone);
  
  if (!client) 
    return;
  
  
  try {
    await client.disconnect();
    activeClients.delete(phone);
    logger.info('Client disconnected', { phone });
  } catch (err: any) {
    logger.error('Failed to disconnect client', { phone, error: err.message });
  }
}

export const disconnectAll = async (): Promise<void> => {
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

export const isAuthenticated = (phone: string): boolean => {
  const client = activeClients.get(phone);
  return client !== undefined;
}

export const getActivePhones = (): string[] => {
  return Array.from(activeClients.keys());
}

export const getActiveClientCount = (): number => {
  return activeClients.size;
}


export default({
  loadAllSessions,
  loadSession,
  getClient,
  setClient,
  removeClient,
  disconnectClient,
  disconnectAll,
  isAuthenticated,
  getActivePhones,
  getActiveClientCount,
});
