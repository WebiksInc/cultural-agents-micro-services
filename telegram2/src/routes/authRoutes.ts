import { Router, Request, Response } from 'express';
import * as authService from '../services/authService';
import * as sessionManager from '../services/sessionManager';
import * as validators from '../utils/validators';
import * as logger from '../utils/logger';

const router = Router();

router.post('/send-code', async (req: Request, res: Response) => {
  try {
    const phone = validators.validatePhone(req.body.phone);
    const { apiId, apiHash } = validators.validateApiCredentials(
      req.body.apiId,
      req.body.apiHash
    );
    
    const result = await authService.sendCode(phone, apiId, apiHash);
    
    res.json({
      success: true,
      phoneCodeHash: result.phoneCodeHash,
      message: 'Verification code sent to Telegram',
    });
  } catch (err: any) {
    logger.error('Send code failed', { error: err.message });
    res.status(400).json({ success: false, error: err.message });
  }
});

router.post('/verify-code', async (req: Request, res: Response) => {
  try {
    const phone = validators.validatePhone(req.body.phone);
    const code = validators.validateCode(req.body.code);
    
    const result = await authService.verifyCode(phone, code);
    
    res.json({
      success: true,
      user: result.user,
      message: 'Authentication successful',
    });
  } catch (err: any) {
    logger.error('Verify code failed', { error: err.message });
    res.status(400).json({ success: false, error: err.message });
  }
});

router.get('/debug/active-sessions', async (req: Request, res: Response) => {
  const activePhones = sessionManager.getActivePhones();
  const count = sessionManager.getActiveClientCount();
  
  logger.info('Debug: Active sessions requested', { count, phones: activePhones });
  
  res.json({
    success: true,
    count,
    activePhones,
    message: 'These phones have active clients in memory',
  });
});

export default router;


