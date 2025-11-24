import { Router, Request, Response } from 'express';
import chatMessagesService from '../services/chatMessagesService.js';
import validators from '../utils/validators.js';
import logger from '../utils/logger.js';

const router = Router();

router.get('/', async (req: Request, res: Response) => {
  try {
    const phone = req.query.phone as string;
    const chatId = req.query.chatId as string;
    const limitParam = req.query.limit as string;

    if (!phone) {
      return res.status(400).json({
        success: false,
        error: 'Phone parameter is required',
      });
    }

    if (!chatId) {
      return res.status(400).json({
        success: false,
        error: 'chatId parameter is required',
      });
    }

    validators.validatePhone(phone);

    const limit = limitParam ? parseInt(limitParam, 10) : 100;

    if (isNaN(limit) || limit < 1 || limit > 1000) {
      return res.status(400).json({
        success: false,
        error: 'Limit must be a number between 1 and 1000',
      });
    }

    const result = await chatMessagesService.getMessages(phone, chatId, limit);

    res.json({
      success: true,
      chatId: result.chatId,
      chatTitle: result.chatTitle,
      phone,
      messagesCount: result.messages.length,
      messages: result.messages,
    });
  } catch (err: unknown) {
    const error = err as Error;
    logger.error('Get chat messages failed', { error: error.message });

    if (error.message.includes('No authenticated session')) {
      return res.status(401).json({ success: false, error: error.message });
    }

    if (error.message.includes('not a member') || error.message.includes('permission')) {
      return res.status(403).json({ success: false, error: error.message });
    }

    if (error.message.includes('Chat not found') || error.message.includes('Could not find')) {
      return res.status(404).json({ success: false, error: error.message });
    }

    if (error.message.includes('Invalid phone')) {
      return res.status(400).json({ success: false, error: error.message });
    }

    res.status(500).json({
      success: false,
      error: `Failed to fetch messages: ${error.message}`,
    });
  }
});

export default router;
