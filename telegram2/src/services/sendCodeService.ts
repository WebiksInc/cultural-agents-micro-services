import { Api } from 'telegram/tl';
import { TelegramClient } from 'telegram';
import { StringSession } from 'telegram/sessions';
import * as logger from '../utils/logger';
import * as phoneStorage from '../utils/phoneStorage';
import * as sessionManager from './sessionManager';
import { config } from '../utils/config';
import { handleSendCodeError } from './authErrorHandler';

export async function sendCode(
  phone: string,
  apiId: number,
  apiHash: string
): Promise<{ phoneCodeHash: string }> {
  logger.info('Sending verification code', { phone });
  
  let client = sessionManager.getClient(phone);
  
  if (!client) {
    logger.info('Creating new client for send-code', { phone });
    client = await createNewClient(apiId, apiHash);
    sessionManager.setClient(phone, client);
    logger.info('Client created and stored', { phone });
  } else {
    logger.info('Reusing existing client for send-code', { phone });
  }
  
  try {
    const result = await invokeCodeRequest(client, phone, apiId, apiHash);
    
    savePhoneCredentials(phone, apiId, apiHash, result.phoneCodeHash);
    
    logger.info('Code sent successfully', { phone, phoneCodeHash: result.phoneCodeHash });
    
    return { phoneCodeHash: result.phoneCodeHash };
  } catch (err: any) {
    throw handleSendCodeError(phone, err);
  }
}

async function createNewClient(apiId: number, apiHash: string): Promise<any> {
  const client = new TelegramClient(
    new StringSession(''),
    apiId,
    apiHash,
    { connectionRetries: config.connectionRetries }
  );
  await client.connect();
  return client;
}

async function invokeCodeRequest(
  client: any,
  phone: string,
  apiId: number,
  apiHash: string
): Promise<{ phoneCodeHash: string }> {
  return await client.invoke(
    new Api.auth.SendCode({
      phoneNumber: phone,
      apiId,
      apiHash,
      settings: new Api.CodeSettings({}),
    })
  );
}

function savePhoneCredentials(
  phone: string,
  apiId: number,
  apiHash: string,
  phoneCodeHash: string
): void {
  phoneStorage.savePhoneData({
    phone,
    apiId,
    apiHash,
    phoneCodeHash,
    verified: false,
  });
}