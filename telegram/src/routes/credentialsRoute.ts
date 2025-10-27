import { Router, Request, Response } from 'express';
import { savePhoneCredentials } from '../services/configService';
import { sendSuccess, sendError } from '../utils/response';

const router = Router();

router.post('/', async (req: Request, res: Response) => {
  try {
    const { phone, apiId, apiHash } = req.body;
    
    if (!phone || !apiId || !apiHash) {
      return sendError(res, 400, 'Missing required fields');
    }
    
    const config = savePhoneCredentials(phone, apiId, apiHash);
    sendSuccess(res, config, 'Credentials saved successfully');
  } catch (error) {
    sendError(res, 500, 'Failed to save credentials');
  }
});

export default router;
