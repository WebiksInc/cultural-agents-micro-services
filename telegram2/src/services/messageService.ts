import  sessionManager from './sessionManager';
import  validators from '../utils/validators';
import  logger from '../utils/logger';

export const sendMessage = async (
  fromPhone: string,
  toTarget: string,
  message: string
): Promise<{ sentTo: string }> => {
  validators.validatePhone(fromPhone);
  validators.validateTarget(toTarget);
  validators.validateMessage(message);

  const client = sessionManager.getClient(fromPhone);
  if (!client) {
    throw new Error(`No authenticated session found for ${fromPhone}`);
  }

  logger.info('Sending message', { fromPhone, toTarget });

  await client.sendMessage(toTarget, { message });

  logger.info('Message sent successfully', { fromPhone, toTarget });

  return { sentTo: toTarget };
};

