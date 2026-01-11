import { Router, Request, Response } from 'express';
import  unreadService from '../services/unreadService';
import  validators from '../utils/validators';
import  logger from '../utils/logger';

const router = Router();

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


