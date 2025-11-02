import sessionManager from './sessionManager.js';
import validators from '../utils/validators.js';
import logger from '../utils/logger.js';

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

  try {
    const entity = await client.getEntity(toTarget);
    await client.sendMessage(entity, { message });
    
    logger.info('Message sent successfully', { fromPhone, toTarget });
    
    return { sentTo: toTarget };
  } catch (err: any) {
    if (err.message.includes('Could not find the input entity')) {
      throw new Error(`Target not found: ${toTarget}. Make sure the user/chat exists and you have interacted with them before.`);
    }
    throw err;
  }
};
