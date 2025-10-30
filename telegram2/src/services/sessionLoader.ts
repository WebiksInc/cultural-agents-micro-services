import { TelegramClient } from 'telegram';
import { StringSession } from 'telegram/sessions';
import * as logger from '../utils/logger';
import * as phoneStorage from '../utils/phoneStorage';
import { config } from '../utils/config';

export async function loadSession(phone: string, activeClients: Map<string, any>): Promise<any | null> {
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

export async function loadAllSessions(activeClients: Map<string, any>): Promise<void> {
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

async function connectClient(session: string, apiId: number, apiHash: string): Promise<any> {
  const client = new TelegramClient(
    new StringSession(session),
    apiId,
    apiHash,
    { connectionRetries: config.connectionRetries }
  );
  
  await client.connect();
  return client;
}
