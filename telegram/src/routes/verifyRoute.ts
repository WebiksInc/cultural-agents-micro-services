import { Router, Request, Response } from 'express';
import { verifyCode } from '../services/codeVerifier';
import { sendSuccess, sendError } from '../utils/response';

const router = Router();

router.post('/', async (req: Request, res: Response) => {
  try {
    const { phone, code, phoneCodeHash } = req.body;
    
    if (!phone || !code || !phoneCodeHash) {
      return sendError(res, 400, 'Missing required fields');
    }
    
    const success = await verifyCode(phone, code, phoneCodeHash);
    
    if (!success) {
      return sendError(res, 401, 'Invalid verification code');
    }
    
    sendSuccess(res, null, 'Authentication successful');
  } catch (error: any) {
    const message = error.message || 'Verification failed';
    sendError(res, 429, message);
  }
});

export default router;

