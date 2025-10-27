import { readConfig } from '../utils/fileSystem';
import { PhoneConfig } from '../types';
import { createClient } from './clientFactory';
import { updateConfig } from '../utils/configWriter';



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
    
    await client.start({
      phoneNumber: phone,
      phoneCode: async () => code,
      onError: (err) => console.error(err),
    });
    
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

