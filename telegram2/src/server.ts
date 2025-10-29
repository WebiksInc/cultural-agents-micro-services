import express from 'express';
import routes from './routes';
import * as sessionManager from './services/sessionManager';
import * as logger from './utils/logger';

const app = express();
const port = process.env.PORT || 4000;

app.use(express.json());

app.get('/health', (_req, res) => {
  res.json({ success: true, message: 'Service is healthy' });
});

app.use('/api', routes);

async function startServer(): Promise<void> {
  try {
    await sessionManager.loadAllSessions();
    
    const server = app.listen(port, () => {
      logger.info('Server started', { port });
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
      }, 10000);
    }
    
    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);
  } catch (err: any) {
    logger.error('Failed to start server', { error: err.message });
    process.exit(1);
  }
}

startServer();

