import { readConfig } from '../utils/fileSystem';
import { PhoneConfig } from '../types';
import { createClient } from './clientFactory';
import { updateConfig } from '../utils/configWriter';
import { getSessionPath } from '../utils/sessionManager';
import * as fs from 'fs';
import { Api } from 'telegram';

export async function verifyCode(
  phone: string,
  code: string,
  phoneCodeHash: string
): Promise<boolean> {
  const config = readConfig<PhoneConfig>(phone);
  
  if (!config) {
    return false;
  }
  
  try {
    const client = await createClient(config);
    await client.connect();
    
    await client.invoke(
      new Api.auth.SignIn({
        phoneNumber: phone,
        phoneCodeHash: phoneCodeHash,
        phoneCode: code,
      })
    );
    
    const sessionString = client.session.save() as unknown as string;
    const sessionPath = getSessionPath(phone);
    fs.writeFileSync(sessionPath, sessionString);
    
    // Mark the phone as verified
    updateConfig<PhoneConfig>(phone, { verified: true });
    await client.disconnect();
    return true;
  } catch (error: any) {
    if (error.code === 420) {
      const waitMinutes = Math.ceil(error.seconds / 60);
      console.error(`FloodWait: Must wait ${waitMinutes} minutes`);
      throw new Error(
        `Too many attempts. Please wait ${waitMinutes} minutes`
      );
    }
    console.error('Verification error:', error.message);
    return false;
  }
}


