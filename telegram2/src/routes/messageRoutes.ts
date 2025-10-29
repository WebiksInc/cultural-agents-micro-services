import { Router, Request, Response } from 'express';
import {sendMessage}  from '../services/messageService';
import * as validators from '../utils/validators';
import * as logger from '../utils/logger';

const router = Router();

router.post('/send', async (req: Request, res: Response) => {
  try {
    const fromPhone = validators.validatePhone(req.body.fromPhone);
    const toTarget = validators.validateTarget(req.body.toTarget);
    const message = validators.validateMessage(req.body.message);
    
    const result = await sendMessage(fromPhone, toTarget, message);
    
    res.json({
      success: true,
      sentTo: result.sentTo,
      message: 'Message sent successfully',
    });
  } catch (err: any) {
    logger.error('Send message failed', { error: err.message });
    res.status(400).json({ success: false, error: err.message });
  }
});

export default router;

