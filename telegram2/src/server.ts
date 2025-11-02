import 'dotenv/config';
import express from 'express';
import routes from './routes';
import * as sessionManager from './services/sessionManager';
import * as logger from './utils/logger';
import { config } from './utils/config';

const app = express();

app.use(express.json());

app.get('/health', (req, res) => {
  res.json({ 
    success: true, 
    version: '0.1.0',
    environment: config.nodeEnv,
    port: config.port
  });
});

app.get('/config', (req, res) => {
  res.json({
    success: true,
    config: {
      nodeEnv: config.nodeEnv,
      port: config.port,
      logLevel: config.logLevel,
      dataDir: config.dataDir,
      autoLoadSessions: config.autoLoadSessions,
      connectionRetries: config.connectionRetries,
      hasDefaultApiCredentials: !!(config.telegramApiId && config.telegramApiHash)
    }
  });
});

app.use('/api', routes);

async function startServer(): Promise<void> {
  try {
    if (config.autoLoadSessions) {
      await sessionManager.loadAllSessions();
    } else {
      logger.info('Auto-load sessions disabled');
    }
    
    const server = app.listen(config.port, () => {
      logger.info('Server started', { port: config.port });
    });
    
    async function shutdown(): Promise<void> {
      logger.info('Shutting down gracefully');
      
      await sessionManager.disconnectAll();
      
      server.close(() => {
        logger.info('Server closed');
        process.exit(0);
      });
      
      setTimeout(() => {
        logger.error('Forced shutdown after timeout');
        process.exit(1);
      }, config.shutdownTimeout);
    }
    
    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);
  } catch (err: any) {
    logger.error('Failed to start server', { error: err.message });
    process.exit(1);
  }
}

startServer();


