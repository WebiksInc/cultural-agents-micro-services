type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogContext {
  [key: string]: any;
}

// Log level hierarchy: debug < info < warn < error
const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

function getCurrentLogLevel(): LogLevel {
  const envLevel = process.env.LOG_LEVEL?.toLowerCase();
  if (envLevel && envLevel in LOG_LEVELS) {
    return envLevel as LogLevel;
  }
  return 'info';
}

function shouldLog(level: LogLevel): boolean {
  const currentLevel = getCurrentLogLevel();
  return LOG_LEVELS[level] >= LOG_LEVELS[currentLevel];
}

function timestamp(): string {
  return new Date().toISOString();
}

function formatMessage(level: LogLevel, message: string, context?: LogContext): string {
  const logEntry = {
    timestamp: timestamp(),
    level: level.toUpperCase(),
    message,
    ...context,
  };
  return JSON.stringify(logEntry);
}

function logOutput(level: LogLevel, message: string, context?: LogContext): void {
  if (!shouldLog(level)) {
    return;
  }
  
  const formatted = formatMessage(level, message, context);
  
  switch (level) {
    case 'error':
      console.error(formatted);
      break;
    case 'warn':
      console.warn(formatted);
      break;
    case 'debug':
      console.debug(formatted);
      break;
    default:
      console.log(formatted);
  }
}

export function debug(message: string, context?: LogContext): void {
  logOutput('debug', message, context);
}

export function info(message: string, context?: LogContext): void {
  logOutput('info', message, context);
}

export function warn(message: string, context?: LogContext): void {
  logOutput('warn', message, context);
}

export function error(message: string, context?: LogContext): void {
  logOutput('error', message, context);
}


export default {
  debug,
  info,
  warn,
  error,
  logOutput,
  getCurrentLogLevel,
  shouldLog,
  timestamp,
  formatMessage
};
