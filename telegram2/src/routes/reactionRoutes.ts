import { Router, Request, Response } from 'express';
import reactionService from '../services/reactionService';
import validators from '../utils/validators';
import logger from '../utils/logger';

const router = Router();

router.post('/', async (req: Request, res: Response) => {
  try {
    const { phone, chatId, messageId, messageTimestamp, emoji } = req.body;

    if (!phone || !chatId) {
      return res.status(400).json({
        success: false,
        error: 'phone and chatId are required',
      });
    }

    if (!emoji) {
      return res.status(400).json({
        success: false,
        error: 'emoji is required',
      });
    }

    if (!messageId && !messageTimestamp) {
      return res.status(400).json({
        success: false,
        error: 'Either messageId or messageTimestamp must be provided',
      });
    }

    validators.validatePhone(phone);
    validators.validateTarget(chatId);

    const result = await reactionService.addReaction(
      phone,
      chatId,
      messageId,
      messageTimestamp,
      emoji
    );

    res.json({
      success: true,
      ...result,
    });
  } catch (err: unknown) {
    const error = err as Error;
    logger.error('Add reaction failed', { error: error.message });

    const statusCode = error.message.includes('No authenticated session') ? 401 :
                       error.message.includes('not found') ? 404 :
                       error.message.includes('required') ? 400 : 500;

    res.status(statusCode).json({
      success: false,
      error: error.message,
    });
  }
});

export default router;
