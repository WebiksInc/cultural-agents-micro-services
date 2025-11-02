import 'dotenv/config';
import express from 'express';
import sessions from './services/sessionManager.js';
import logger from './utils/logger.js';
import vars from './vars.js';
import routes from './routes/index.js';

const app = express();

app.use(express.json());

app.get('/health', (req, res) => {
  res.json({ 
    success: true, 
    version: '0.1.0',
    environment: vars.NODE_ENV,
    port: vars.PORT
  });
});

app.use('/api', routes);

async function shutdown(server: any): Promise<void> {
  logger.info('Shutting down gracefully');
  
  await sessions.disconnectAll();
  
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
  
  setTimeout(() => {
    logger.error('Forced shutdown after timeout');
    process.exit(1);
  }, vars.SHUTDOWN_TIMEOUT);
}

async function startServer(): Promise<void> {
  try {
    if (vars.AUTO_LOAD_SESSIONS) {
      await sessions.loadAllSessions();
    } else {
      logger.info('Auto-load sessions disabled');
    }
    
    const server = app.listen(vars.PORT, () => {
      logger.info('Server started', { port: vars.PORT });
    });
    
    process.on('SIGINT', () => shutdown(server));
    process.on('SIGTERM', () => shutdown(server));
  } catch (err: any) {
    logger.error('Failed to start server', { error: err.message });
    process.exit(1);
  }
}

startServer();

