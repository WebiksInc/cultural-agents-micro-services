import { PhoneConfig } from '../types';
import { writeConfig } from '../utils/configWriter';
import { ensureConfigDir } from '../utils/fileSystem';

export function savePhoneCredentials(
  phone: string,
  apiId: number,
  apiHash: string
): PhoneConfig {
  ensureConfigDir();
  
  const config: PhoneConfig = {
    phone,
    apiId,
    apiHash,
    verified: false,
  };
  
  writeConfig(phone, config);
  return config;
}
