import { Router, Request, Response } from 'express';
import { getUnreadMessages } from '../services/messageFetcher';
import { markAsRead } from '../services/messageReader';
import { sendSuccess, sendError } from '../utils/response';

const router = Router();

router.get('/', async (req: Request, res: Response) => {
  try {
    const { phone, chatId, chatPhone } = req.query;
    
    if (!phone) {
      return sendError(res, 400, 'Phone number required');
    }
    
    const chatIdentifier = (chatId || chatPhone) as string;
    
    if (!chatIdentifier) {
      return sendError(res, 400, 'Chat ID or phone required');
    }
    
    const messages = await getUnreadMessages(
      phone as string,
      chatIdentifier
    );
    
    const messageIds = messages.map(m => m.id);
    await markAsRead(phone as string, chatIdentifier, messageIds);
    
    sendSuccess(res, messages, 'Messages retrieved');
  } catch (error: any) {
    const msg = error.message || 'Failed to get messages';
    sendError(res, 500, msg);
  }
});

export default router;

