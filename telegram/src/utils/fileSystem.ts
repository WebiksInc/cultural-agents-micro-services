import * as fs from 'fs';
import * as path from 'path';

const CONFIG_DIR = path.join(__dirname, '../../config');

// Ensure the configuration directory exists, create if missing
export function ensureConfigDir(): void {
  if (!fs.existsSync(CONFIG_DIR)) {
    fs.mkdirSync(CONFIG_DIR, { recursive: true });
  }
}

export function getConfigPath(phone: string): string {
  const sanitized = phone.replace(/[^0-9+]/g, '');
  return path.join(CONFIG_DIR, `phone_${sanitized}.json`);
}

export function readConfig<T>(phone: string): T | null {
  try {
    const configPath = getConfigPath(phone);
    if (!fs.existsSync(configPath)) {
      return null;
    }
    const data = fs.readFileSync(configPath, 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    return null;
  }
}

