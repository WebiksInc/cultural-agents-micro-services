import { Router, Request, Response } from 'express';
import pollService from '../services/pollService';
import pollVoteService from '../services/pollVoteService';
import validators from '../utils/validators';
import logger from '../utils/logger';

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

    const limit = limitParam ? parseInt(limitParam, 10) : 1;

    if (isNaN(limit) || limit < 1 || limit > 1000) {
      return res.status(400).json({
        success: false,
        error: 'Limit must be a number between 1 and 1000',
      });
    }

    const result = await pollService.getPolls(phone, chatId, limit);

    res.json({
      success: true,
      chatId: result.chatId,
      chatTitle: result.chatTitle,
      phone,
      pollsCount: result.polls.length,
      polls: result.polls,
    });
  } catch (err: unknown) {
    const error = err as Error;
    logger.error('Get polls failed', { error: error.message });

    if (error.message.includes('No authenticated session')) {
      return res.status(401).json({ success: false, error: error.message });
    }

    if (error.message.includes('Chat not found')) {
      return res.status(404).json({ success: false, error: error.message });
    }

    if (error.message.includes('Invalid phone')) {
      return res.status(400).json({ success: false, error: error.message });
    }

    res.status(500).json({
      success: false,
      error: `Failed to fetch polls: ${error.message}`,
    });
  }
});

router.post('/vote', async (req: Request, res: Response) => {
  try {
    const { phone, chatId, messageId, optionIds } = req.body;

    if (!phone) {
      return res.status(400).json({ success: false, error: 'phone is required' });
    }

    if (!chatId) {
      return res.status(400).json({ success: false, error: 'chatId is required' });
    }

    if (messageId === undefined || messageId === null) {
      return res.status(400).json({ success: false, error: 'messageId is required' });
    }

    if (!Array.isArray(optionIds) || optionIds.length === 0) {
      return res.status(400).json({ 
        success: false, 
        error: 'optionIds must be a non-empty array' 
      });
    }

    validators.validatePhone(phone);

    const result = await pollVoteService.votePoll(phone, chatId, messageId, optionIds);

    res.json({
      success: true,
      pollId: result.pollId,
      messageId: result.messageId,
      votedOptions: result.votedOptions,
    });
  } catch (err: unknown) {
    const error = err as Error;
    logger.error('Vote poll failed', { error: error.message });

    if (error.message.includes('No authenticated session')) {
      return res.status(401).json({ success: false, error: error.message });
    }

    if (error.message.includes('not found') || error.message.includes('Not found')) {
      return res.status(404).json({ success: false, error: error.message });
    }

    if (error.message.includes('closed') || 
        error.message.includes('Invalid option') ||
        error.message.includes('not a poll')) {
      return res.status(400).json({ success: false, error: error.message });
    }

    res.status(500).json({
      success: false,
      error: `Failed to vote: ${error.message}`,
    });
  }
});

export default router;
