function getEnvAsNumber(key: string, defaultValue: number): number {
  const value = process.env[key];
  if (!value) return defaultValue;
  
  const parsed = parseInt(value, 10);
  if (isNaN(parsed)) {
    console.warn(`Invalid ${key}, using default:`, { value, default: defaultValue });
    return defaultValue;
  }
  
  return parsed;
}

function getEnvAsBoolean(key: string, defaultValue: boolean): boolean {
  const value = process.env[key];
  if (!value) return defaultValue;
  return value.toLowerCase() === 'true';
}

export default {
  PORT: getEnvAsNumber('PORT', 4000),
  NODE_ENV: process.env.NODE_ENV || 'development',
  LOG_LEVEL: process.env.LOG_LEVEL || 'info',
  DATA_DIR: process.env.DATA_DIR || './data',
  CONNECTION_RETRIES: getEnvAsNumber('CONNECTION_RETRIES', 3),
  SHUTDOWN_TIMEOUT: getEnvAsNumber('SHUTDOWN_TIMEOUT', 10000),
  AUTO_LOAD_SESSIONS: getEnvAsBoolean('AUTO_LOAD_SESSIONS', true),
  SESSION_CLEANUP_INTERVAL: getEnvAsNumber('SESSION_CLEANUP_INTERVAL', 3600000),
  TELEGRAM_API_ID: process.env.TELEGRAM_API_ID ? parseInt(process.env.TELEGRAM_API_ID, 10) : undefined,
  TELEGRAM_API_HASH: process.env.TELEGRAM_API_HASH || undefined,
};
