import { Api } from 'telegram/tl';
import * as logger from '../utils/logger';
import * as phoneStorage from '../utils/phoneStorage';
import * as sessionManager from './sessionManager';
import { handleVerifyCodeError } from './authErrorHandler';

export async function verifyCode(
  phone: string,
  code: string
): Promise<{ success: boolean; user?: string }> {
  logger.info('Verifying code', { phone });
  
  const phoneData = loadAndValidatePhoneData(phone);
  const client = getValidatedClient(phone);
  
  logger.info('Client found in memory, proceeding with verification', { phone });
  
  try {
    const result = await performSignIn(client, phone, phoneData.phoneCodeHash, code);
    
    const sessionString = client.session.save() as unknown as string;
    
    saveVerifiedSession(phone, sessionString);
    sessionManager.setClient(phone, client);
    
    const userName = extractUserName(result);
    logger.info('Code verified successfully', { phone, user: userName });
    
    return { success: true, user: userName };
  } catch (err: any) {
    throw handleVerifyCodeError(phone, err);
  }
}

function loadAndValidatePhoneData(phone: string): any {
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
  
  return phoneData;
}

function getValidatedClient(phone: string): any {
  const client = sessionManager.getClient(phone);
  
  if (!client) {
    logger.error('Client not found in memory', { phone });
    throw new Error(
      'Client session not found. The server may have been restarted or the client was disconnected. Please call send-code again.'
    );
  }
  
  return client;
}

async function performSignIn(
  client: any,
  phone: string,
  phoneCodeHash: string,
  code: string
): Promise<any> {
  return await client.invoke(
    new Api.auth.SignIn({
      phoneNumber: phone,
      phoneCodeHash,
      phoneCode: code,
    })
  );
}

function saveVerifiedSession(phone: string, sessionString: string): void {
  phoneStorage.updatePhoneData(phone, {
    session: sessionString,
    verified: true,
    lastAuthAt: new Date().toISOString(),
    phoneCodeHash: undefined,
  });
}

function extractUserName(result: any): string {
  return (result as any).user?.firstName || 'Unknown';
}