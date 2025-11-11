import { Router, Request, Response } from 'express';
import {sendMessage}  from '../services/messageService';
import validators from '../utils/validators';
import logger from '../utils/logger';
import unreadService from '../services/unreadService';

const router = Router();

router.post('/send', async (req: Request, res: Response) => {
  try {
    const { fromPhone, toTarget, content, replyTo } = req.body;

    if (!fromPhone) {
      return res.status(400).json({
        success: false,
        error: 'fromPhone is required',
      });
    }

    if (!toTarget) {
      return res.status(400).json({
        success: false,
        error: 'toTarget is required',
      });
    }

    if (!content) {
      return res.status(400).json({
        success: false,
        error: 'content is required',
      });
    }

    const validatedPhone = validators.validatePhone(fromPhone);
    const validatedTarget = validators.validateTarget(toTarget);
    const validatedContent = validators.validateContent(content);
    const validatedReplyTo = validators.validateReplyTo(replyTo);
    
    const result = await sendMessage(
      validatedPhone, 
      validatedTarget, 
      validatedContent,
      validatedReplyTo
    );
    
    res.json({
      success: true,
      sentTo: result.sentTo,
      messageId: result.messageId,
    });
  } catch (err: unknown) {
    const error = err as Error;
    logger.error('Send message failed', { error: error.message });

    if (error.message.includes('No authenticated session')) {
      return res.status(401).json({ success: false, error: error.message });
    }

    if (error.message.includes('Target not found')) {
      return res.status(404).json({ success: false, error: error.message });
    }

    if (error.message.includes('required') || 
        error.message.includes('must be') ||
        error.message.includes('cannot be empty')) {
      return res.status(400).json({ success: false, error: error.message });
    }

    res.status(500).json({ success: false, error: error.message });
  }
});

router.get('/unread', async (req: Request, res: Response) => {
  try {
    const accountPhone = validators.validatePhone(req.query.accountPhone as string);
    const target = req.query.target as string;
    const chatId = req.query.chatId as string;
    
    if (!target && !chatId) {
      return res.status(400).json({
        success: false,
        error: 'Either target (phone/username) or chatId must be provided',
      });
    }
    
    if (target && chatId) {
      return res.status(400).json({
        success: false,
        error: 'Provide either target or chatId, not both',
      });
    }
    
    if (target) {
      validators.validateTarget(target);
    }
    
    const result = await unreadService.getUnreadMessages(accountPhone, target, chatId);
    
    res.json({
      success: true,
      count: result.count,
      unread: result.unread,
    });
  } catch (err: any) {
    logger.error('Get unread failed', { error: err.message });
    res.status(500).json({ success: false, error: err.message });
  }
});

export default router;
