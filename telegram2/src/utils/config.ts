export interface Config {
  port: number;
  nodeEnv: string;
  logLevel: string;
  dataDir: string;
  shutdownTimeout: number;
  connectionRetries: number;
  telegramApiId?: number;
  telegramApiHash?: string;
  autoLoadSessions: boolean;
  sessionCleanupInterval: number;
}

function parseNumber(value: string | undefined, defaultValue: number, name: string): number {
  if (!value) return defaultValue;
  
  const parsed = parseInt(value, 10);
  if (isNaN(parsed)) {
    console.warn(`Invalid ${name}, using default:`, { value, default: defaultValue });
    return defaultValue;
  }
  
  return parsed;
}

function parseBoolean(value: string | undefined, defaultValue: boolean): boolean {
  if (!value) return defaultValue;
  return value.toLowerCase() === 'true';
}

function loadConfig(): Config {
  const config: Config = {
    port: parseNumber(process.env.PORT, 4000, 'PORT'),
    nodeEnv: process.env.NODE_ENV || 'development',
    logLevel: process.env.LOG_LEVEL || 'info',
    dataDir: process.env.DATA_DIR || './data',
    shutdownTimeout: parseNumber(process.env.SHUTDOWN_TIMEOUT, 10000, 'SHUTDOWN_TIMEOUT'),
    connectionRetries: parseNumber(process.env.CONNECTION_RETRIES, 3, 'CONNECTION_RETRIES'),
    autoLoadSessions: parseBoolean(process.env.AUTO_LOAD_SESSIONS, true),
    sessionCleanupInterval: parseNumber(process.env.SESSION_CLEANUP_INTERVAL, 3600000, 'SESSION_CLEANUP_INTERVAL'),
  };

  // Optional Telegram API credentials
  if (process.env.TELEGRAM_API_ID) {
    config.telegramApiId = parseNumber(process.env.TELEGRAM_API_ID, 0, 'TELEGRAM_API_ID');
  }
  
  if (process.env.TELEGRAM_API_HASH) {
    config.telegramApiHash = process.env.TELEGRAM_API_HASH;
  }

  return config;
}

export const config = loadConfig();