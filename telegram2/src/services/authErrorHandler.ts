import * as logger from '../utils/logger';

export function handleSendCodeError(phone: string, err: any): Error {
  logger.error('Failed to send code', { phone, error: err.message });
  
  const errorMessage = err.message || '';
  
  switch (true) {
    case errorMessage.includes('PHONE_NUMBER_INVALID'):
      return new Error('Invalid phone number format. Please use international format (e.g., +1234567890)');
    
    case errorMessage.includes('PHONE_NUMBER_BANNED'):
      return new Error('This phone number has been banned from Telegram');
    
    case errorMessage.includes('API_ID_INVALID'):
      return new Error('Invalid API ID. Please check your Telegram API credentials');
    
    default:
      return new Error(`Failed to send code: ${err.message}`);
  }
}

export function handleVerifyCodeError(phone: string, err: any): Error {
  logger.error('Verification failed', { phone, error: err.message, stack: err.stack });
  
  const errorMessage = err.message || '';
  
  switch (true) {
    case errorMessage.includes('PHONE_CODE_EXPIRED'):
      return new Error(
        'Verification code has expired. Please request a new code by calling send-code again.'
      );
    
    case errorMessage.includes('PHONE_CODE_INVALID'):
      return new Error(
        'Invalid verification code. Please check the code and try again.'
      );
    
    case errorMessage.includes('SESSION_PASSWORD_NEEDED'):
      return new Error(
        '2FA is enabled on this account. Password authentication is not yet supported.'
      );
    
    default:
      return new Error(`Verification failed: ${err.message}`);
  }
}