import fs from 'fs';
import path from 'path';
import * as logger from './logger';
import { config } from './config';

const dataDir = path.resolve(config.dataDir);

export interface PhoneData {
  phone: string;
  apiId: number;
  apiHash: string;
  session?: string;
  phoneCodeHash?: string;
  verified: boolean;
  lastAuthAt?: string;
}

function ensureDataDir(): void {
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
    logger.info('Created data directory', { path: dataDir });
  }
}

function getPhoneFilePath(phone: string): string {
  const sanitized = phone.replace(/[^0-9+]/g, '');
  return path.join(dataDir, `phone_${sanitized}.json`);
}

export function savePhoneData(data: PhoneData): void {
  ensureDataDir();
  const filePath = getPhoneFilePath(data.phone);
  const temp = filePath + '.tmp';
  
  fs.writeFileSync(temp, JSON.stringify(data, null, 2));
  fs.renameSync(temp, filePath);
  
  logger.info('Saved phone data', { phone: data.phone, verified: data.verified });
}

export function loadPhoneData(phone: string): PhoneData | null {
  const filePath = getPhoneFilePath(phone);
  
  if (!fs.existsSync(filePath)) {
    logger.debug('Phone data not found', { phone });
    return null;
  }
  
  try {
    const raw = fs.readFileSync(filePath, 'utf-8');
    const data = JSON.parse(raw) as PhoneData;
    logger.debug('Loaded phone data', { phone });
    return data;
  } catch (err: any) {
    logger.error('Failed to load phone data', { phone, error: err.message });
    return null;
  }
}

export function updatePhoneData(phone: string, updates: Partial<PhoneData>): void {
  const existing = loadPhoneData(phone);
  
  if (!existing) {
    throw new Error(`Phone data not found for ${phone}`);
  }
  
  const updated = { ...existing, ...updates };
  savePhoneData(updated);
}

export function listAllPhones(): string[] {
  ensureDataDir();
  
  const files = fs.readdirSync(dataDir);
  const phones = files
    .filter(f => f.startsWith('phone_') && f.endsWith('.json'))
    .map(f => {
      const data = JSON.parse(fs.readFileSync(path.join(dataDir, f), 'utf-8'));
      return data.phone;
    });
  
  return phones;
}

export function deletePhoneData(phone: string): void {
  const filePath = getPhoneFilePath(phone);
  
  if (fs.existsSync(filePath)) {
    fs.unlinkSync(filePath);
    logger.info('Deleted phone data', { phone });
  }
}

