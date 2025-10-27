import { Router, Request, Response } from 'express';
import { sendMessage } from '../services/messageSender';
import { sendSuccess, sendError } from '../utils/response';

const router = Router();

router.post('/', async (req: Request, res: Response) => {
  try {
    const { senderPhone, receiverPhone, message } = req.body;
    
    if (!senderPhone || !receiverPhone || !message) {
      return sendError(res, 400, 'Missing required fields');
    }
    
    await sendMessage(senderPhone, receiverPhone, message);
    sendSuccess(res, null, 'Message sent successfully');
  } catch (error: any) {
    const msg = error.message || 'Failed to send message';
    sendError(res, 500, msg);
  }
});

export default router;
