// Environment Variables with Defaults
// This file centralizes all configuration variables for the application

// Helper functions
function getEnvAsString(key: string, defaultValue: string): string {
  return process.env[key] || defaultValue;
}

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

function getEnvAsOptionalNumber(key: string): number | undefined {
  const value = process.env[key];
  if (!value) return undefined;
  
  const parsed = parseInt(value, 10);
  return isNaN(parsed) ? undefined : parsed;
}

function getEnvAsOptionalString(key: string): string | undefined {
  return process.env[key] || undefined;
}

// Server Configuration
export const PORT = getEnvAsNumber('PORT', 4000);
export const NODE_ENV = getEnvAsString('NODE_ENV', 'development');

// Logging Configuration
export const LOG_LEVEL = getEnvAsString('LOG_LEVEL', 'info');

// Data Storage
export const DATA_DIR = getEnvAsString('DATA_DIR', './data');

// Connection Settings
export const CONNECTION_RETRIES = getEnvAsNumber('CONNECTION_RETRIES', 3);
export const SHUTDOWN_TIMEOUT = getEnvAsNumber('SHUTDOWN_TIMEOUT', 10000);

// Session Management
export const AUTO_LOAD_SESSIONS = getEnvAsBoolean('AUTO_LOAD_SESSIONS', true);
export const SESSION_CLEANUP_INTERVAL = getEnvAsNumber('SESSION_CLEANUP_INTERVAL', 3600000);

// Optional Telegram API Credentials
export const TELEGRAM_API_ID = getEnvAsOptionalNumber('TELEGRAM_API_ID');
export const TELEGRAM_API_HASH = getEnvAsOptionalString('TELEGRAM_API_HASH');
