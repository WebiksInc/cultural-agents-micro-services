import * as fs from 'fs';
import { getConfigPath, ensureConfigDir } from './fileSystem';

export function writeConfig<T>(phone: string, data: T): void {
  ensureConfigDir();
  const configPath = getConfigPath(phone);
  fs.writeFileSync(configPath, JSON.stringify(data, null, 2));
}

export function updateConfig<T>(
  phone: string,
  updates: Partial<T>
): T | null {
  const configPath = getConfigPath(phone);
  
  if (!fs.existsSync(configPath)) {
    return null;
  }
  
  const current = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
  const updated = { ...current, ...updates };
  
  writeConfig(phone, updated);
  return updated;
}

