import sessionManager from './sessionManager';
import logger from '../utils/logger';
import entityResolver from './entityResolver';
import { Api } from 'telegram';

const TYPING_REFRESH_INTERVAL = 5000; 

export const showTyping = async (
  phone: string,
  chatId: string,
  duration: number = 5000
): Promise<void> => {
  logger.info('Showing typing indicator', { phone, chatId, duration });

  const client = sessionManager.getClient(phone);
  if (!client) {throw new Error(`No authenticated session found for ${phone}`);}

  const entity = await entityResolver.getEntity(client, phone, chatId);
  const iterations = Math.ceil(duration / TYPING_REFRESH_INTERVAL);
  
  for (let i = 0; i < iterations; i++) {
    await client.invoke(
      new Api.messages.SetTyping({
        peer: entity,
        action: new Api.SendMessageTypingAction(),
      })
    );
    
    if (i < iterations - 1) {
      await new Promise(resolve => setTimeout(resolve, TYPING_REFRESH_INTERVAL));
    }
  }

  const remainingTime = duration % TYPING_REFRESH_INTERVAL;
  if (remainingTime > 0) {
    await new Promise(resolve => setTimeout(resolve, remainingTime));
  }

  logger.info('Typing indicator completed', { phone, chatId, duration });
};

export default { showTyping };
