import sessionManager from './sessionManager';
import validators from '../utils/validators';
import logger from '../utils/logger';
import entityResolver from './entityResolver';
import { SendMessageContent } from '../types/messages';

export const sendMessage = async (
  fromPhone: string,
  toTarget: string,
  content: SendMessageContent,
  replyTo?: number
): Promise<{ sentTo: string; messageId?: number }> => {
  content: SendMessageContent,
  replyTo?: number
): Promise<{ sentTo: string; messageId?: number }> => {
  validators.validatePhone(fromPhone);
  validators.validateTarget(toTarget);
  validators.validateContent(content);

  if (replyTo !== undefined) {
    validators.validateReplyTo(replyTo);
  }
  validators.validateContent(content);

  if (replyTo !== undefined) {
    validators.validateReplyTo(replyTo);
  }

  const client = sessionManager.getClient(fromPhone);
  if (!client) {
    throw new Error(`No authenticated session found for ${fromPhone}`);
  }

  logger.info('Sending message', { 
    fromPhone, 
    toTarget, 
    contentType: content.type,
    isReply: !!replyTo 
  });
  logger.info('Sending message', { 
    fromPhone, 
    toTarget, 
    contentType: content.type,
    isReply: !!replyTo 
  });

  try {
    const entity = await entityResolver.getEntity(client, fromPhone, toTarget);
    
    const messageOptions: Record<string, unknown> = {
      message: content.value,
    };

    if (replyTo) {
      messageOptions.replyTo = replyTo;
    }

    const result = await client.sendMessage(entity, messageOptions);
    
    logger.info('Message sent successfully', { 
      fromPhone, 
      toTarget,
      messageId: result?.id,
      contentType: content.type 
    });
    logger.info('Message sent successfully', { 
      fromPhone, 
      toTarget,
      messageId: result?.id,
      contentType: content.type 
    });
    
    return { 
      sentTo: toTarget,
      messageId: result?.id 
    };
  } catch (err: unknown) {
    const error = err as Error;
    logger.error('Send message failed', { 
      fromPhone, 
      toTarget, 
      error: error.message 
    });
    
    if (error.message.includes('Could not find the input entity')) {
    return { 
      sentTo: toTarget,
      messageId: result?.id 
    };
  } catch (err: unknown) {
    const error = err as Error;
    logger.error('Send message failed', { 
      fromPhone, 
      toTarget, 
      error: error.message 
    });
    
    if (error.message.includes('Could not find the input entity')) {
      throw new Error(`Target not found: ${toTarget}. Make sure the user/chat exists and you have interacted with them before.`);
    }
    throw err;
  }
};
