import { Router, Request, Response } from 'express';
import typingService from '../services/typingService';
import validators from '../utils/validators';
import logger from '../utils/logger';

const router = Router();

const DEFAULT_DURATION = 3000;

router.post('/', async (req: Request, res: Response) => {
  try {
    const { phone, chatId, duration } = req.body;

    if (!phone || !chatId) {
      return res.status(400).json({
        success: false,
        error: 'phone and chatId are required',
      });
    }

    validators.validatePhone(phone);
    validators.validateTarget(chatId);

    const durationMs = duration ? parseInt(duration, 10) : DEFAULT_DURATION;

    typingService.showTyping(phone, chatId, durationMs).catch(err => {
      logger.error('Background typing failed', { 
        phone, 
        chatId, 
        error: err.message 
      });
    });

    res.json({
      success: true,
      phone,
      chatId,
      duration: durationMs,
    });
  } catch (err: unknown) {
    const error = err as Error;
    logger.error('Show typing failed', { error: error.message });

    const statusCode = error.message.includes('No authenticated session') ? 401 :
                       error.message.includes('not found') ? 404 : 500;

    res.status(statusCode).json({
      success: false,
      error: error.message,
    });
  }
});

export default router;
