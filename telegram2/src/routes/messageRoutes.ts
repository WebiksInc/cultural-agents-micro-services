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
    });
  } catch (err: any) {
    logger.error('Send message failed', { error: err.message });
    res.status(500).json({ success: false, error: err.message });
  }
});

export default router;
