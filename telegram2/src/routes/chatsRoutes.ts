import { Router, Request, Response } from 'express';
import * as chatsService from '../services/chatsService';
import * as validators from '../utils/validators';
import * as logger from '../utils/logger';

const router = Router();

router.get('/all', async (req: Request, res: Response) => {
  try {
    const accountPhone = validators.validatePhone(req.query.accountPhone as string);
    
    const result = await chatsService.getAllChats(accountPhone);
    
    res.json({
      success: true,
      chats: result.chats,
      details: result.details,
      count: result.details.length,
    });
  } catch (err: any) {
    logger.error('Get all chats failed', { error: err.message });
    res.status(400).json({ success: false, error: err.message });
  }
});

router.get('/groups', async (req: Request, res: Response) => {
  try {
    const accountPhone = validators.validatePhone(req.query.accountPhone as string);
    
    const result = await chatsService.getGroupsOnly(accountPhone);
    
    res.json({
      success: true,
      chats: result.chats,
      details: result.details,
      count: result.details.length,
    });
  } catch (err: any) {
    logger.error('Get groups failed', { error: err.message });
    res.status(400).json({ success: false, error: err.message });
  }
});

export default router;

