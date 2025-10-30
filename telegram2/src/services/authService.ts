import { Api } from 'telegram/tl';
import { TelegramClient } from 'telegram';
import { StringSession } from 'telegram/sessions';
import * as logger from '../utils/logger';
import * as phoneStorage from '../utils/phoneStorage';
import * as sessionManager from './sessionManager';
import { config } from '../utils/config';

export async function sendCode(
  phone: string,
  apiId: number,
  apiHash: string
): Promise<{ phoneCodeHash: string }> {
  logger.info('Sending verification code', { phone });
  
  let client = sessionManager.getClient(phone);
  
  if (!client) {
    logger.info('Creating new client for send-code', { phone });
    client = new TelegramClient(
      new StringSession(''),
      apiId,
      apiHash,
      { connectionRetries: config.connectionRetries }
    );
    await client.connect();
    sessionManager.setClient(phone, client);
    logger.info('Client created and stored', { phone });
  } else {
    logger.info('Reusing existing client for send-code', { phone });
  }
  
  try {
    const result = await client.invoke(
      new Api.auth.SendCode({
        phoneNumber: phone,
        apiId,
        apiHash,
        settings: new Api.CodeSettings({}),
      })
    );
    
    phoneStorage.savePhoneData({
      phone,
      apiId,
      apiHash,
      phoneCodeHash: result.phoneCodeHash,
      verified: false,
    });
    
    logger.info('Code sent successfully', { phone, phoneCodeHash: result.phoneCodeHash });
    
    return { phoneCodeHash: result.phoneCodeHash };
  } catch (err: any) {
    logger.error('Failed to send code', { phone, error: err.message });
    
    if (err.message.includes('PHONE_NUMBER_INVALID')) {
      throw new Error('Invalid phone number format. Please use international format (e.g., +1234567890)');
    }
    
    if (err.message.includes('PHONE_NUMBER_BANNED')) {
      throw new Error('This phone number has been banned from Telegram');
    }
    
    if (err.message.includes('API_ID_INVALID')) {
      throw new Error('Invalid API ID. Please check your Telegram API credentials');
    }
    
    throw new Error(`Failed to send code: ${err.message}`);
  }
}

export async function verifyCode(
  phone: string,
  code: string
): Promise<{ success: boolean; user?: string }> {
  logger.info('Verifying code', { phone });
  
  const phoneData = phoneStorage.loadPhoneData(phone);
  
  if (!phoneData) {
    logger.error('Phone data not found', { phone });
    throw new Error('Phone data not found. Please call send-code first.');
  }
  
  if (!phoneData.phoneCodeHash) {
    logger.error('No phoneCodeHash found', { phone });
    throw new Error('No phoneCodeHash found. Please call send-code first.');
  }
  
  logger.info('Phone data loaded', { 
    phone, 
    hasPhoneCodeHash: !!phoneData.phoneCodeHash,
    phoneCodeHash: phoneData.phoneCodeHash 
  });
  
  const client = sessionManager.getClient(phone);
  
  if (!client) {
    logger.error('Client not found in memory', { phone });
    throw new Error(
      'Client session not found. The server may have been restarted or the client was disconnected. Please call send-code again.'
    );
  }
  
  logger.info('Client found in memory, proceeding with verification', { phone });
  
  try {
    const result = await client.invoke(
      new Api.auth.SignIn({
        phoneNumber: phone,
        phoneCodeHash: phoneData.phoneCodeHash,
        phoneCode: code,
      })
    );
    
    const sessionString = client.session.save() as unknown as string;
    
    phoneStorage.updatePhoneData(phone, {
      session: sessionString,
      verified: true,
      lastAuthAt: new Date().toISOString(),
      phoneCodeHash: undefined,
    });
    
    sessionManager.setClient(phone, client);
    
    const userName = (result as any).user?.firstName || 'Unknown';
    logger.info('Code verified successfully', { phone, user: userName });
    
    return { success: true, user: userName };
  } catch (err: any) {
    logger.error('Verification failed', { phone, error: err.message, stack: err.stack });
    
    if (err.message.includes('PHONE_CODE_EXPIRED')) {
      throw new Error(
        'Verification code has expired. Please request a new code by calling send-code again.'
      );
    }
    
    if (err.message.includes('PHONE_CODE_INVALID')) {
      throw new Error(
        'Invalid verification code. Please check the code and try again.'
      );
    }
    
    if (err.message.includes('SESSION_PASSWORD_NEEDED')) {
      throw new Error(
        '2FA is enabled on this account. Password authentication is not yet supported.'
      );
    }
    
    throw new Error(`Verification failed: ${err.message}`);
  }
}


