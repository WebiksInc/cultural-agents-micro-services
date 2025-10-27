import { Router, Request, Response } from 'express';
import { startAuth } from '../services/authInitiator';
import { sendSuccess, sendError } from '../utils/response';

const router = Router();

router.post('/', async (req: Request, res: Response) => {
  try {
    const { phone } = req.body;
    
    if (!phone) {
      return sendError(res, 400, 'Phone number required');
    }
    
    const result = await startAuth(phone);
    
    if (!result) {
      return sendError(res, 404, 'Phone config not found');
    }
    
    sendSuccess(res, result, 'Verification code sent');
  } catch (error) {
    sendError(res, 500, 'Failed to initiate authentication');
  }
});

export default router;

