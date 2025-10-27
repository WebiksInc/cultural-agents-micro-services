import * as path from 'path';
import * as fs from 'fs';

const SESSIONS_DIR = path.join(__dirname, '../../sessions');

export function ensureSessionsDir(): void {
  if (!fs.existsSync(SESSIONS_DIR)) {
    fs.mkdirSync(SESSIONS_DIR, { recursive: true });
  }
}

export function getSessionPath(phone: string): string {
  const sanitized = phone.replace(/[^0-9+]/g, '');
  return path.join(SESSIONS_DIR, `session_${sanitized}`);
}

export function sessionExists(phone: string): boolean {
  const sessionPath = getSessionPath(phone);
  return fs.existsSync(sessionPath);
}

