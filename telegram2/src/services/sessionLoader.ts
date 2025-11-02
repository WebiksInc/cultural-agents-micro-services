import { TelegramClient } from 'telegram';
import { StringSession } from 'telegram/sessions';
import logger from '../utils/logger';
import phoneStorage from '../utils/phoneStorage';
import vars from '../vars';


async function connectClient(session: string, apiId: number, apiHash: string): Promise<any> {
  const client = new TelegramClient(
    new StringSession(session),
    apiId,
    apiHash,
    { connectionRetries: vars.CONNECTION_RETRIES }
  );
  
  await client.connect();
  return client;
}

export const loadSession = async (phone: string, activeClients: Map<string, any>): Promise<any | null> => {
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
    const client = await connectClient(phoneData.session, phoneData.apiId, phoneData.apiHash);
    activeClients.set(phone, client);
    
    logger.info('Session loaded and connected', { phone });
    return client;
  } catch (err: any) {
    logger.error('Failed to connect session', { phone, error: err.message });
    return null;
  }
}

export const loadAllSessions = async (activeClients: Map<string, any>): Promise<void> => {
  logger.info('Loading existing sessions');
  
  const phones = phoneStorage.listAllPhones();
  
  for (const phone of phones) {
    try {
      await loadSession(phone, activeClients);
    } catch (err: any) {
      logger.warn('Failed to load session', { phone, error: err.message });
    }
  }
  
  logger.info('Sessions loaded', { count: activeClients.size });
}

export default {
  loadSession,
  loadAllSessions,
  connectClient
};
