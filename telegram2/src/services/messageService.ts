import sessionManager from './sessionManager';
import validators from '../utils/validators';
import logger from '../utils/logger';
import entityResolver from './entityResolver';
import { SendMessageContent } from '../types/messages';
import chatMessagesService from './chatMessagesService';

export const sendMessage = async (
  fromPhone: string,
  toTarget: string,
  content: SendMessageContent,
  replyTo?: number,          
  replyToTimestamp?: string   
): Promise<{ sentTo: string; messageId?: number }> => {
  validators.validatePhone(fromPhone);
  validators.validateTarget(toTarget);
  validators.validateContent(content);

  let actualReplyToId: number | undefined = replyTo;
  
  if (replyToTimestamp) {
    const messageId = await chatMessagesService.findMessageIdByTimestamp(
      fromPhone,
      toTarget,
      replyToTimestamp
    );
    
    if (!messageId) {
      throw new Error(`Could not find message with timestamp: ${replyToTimestamp}`);
    }
    
    actualReplyToId = messageId;
    logger.info('Resolved timestamp to message ID', { 
      fromPhone, 
      timestamp: replyToTimestamp, 
      messageId 
    });
  }

  if (actualReplyToId !== undefined) {
    validators.validateReplyTo(actualReplyToId);
  }

  const client = sessionManager.getClient(fromPhone);
  if (!client) {
    throw new Error(`No authenticated session found for ${fromPhone}`);
  }

  logger.info('Sending message', { 
    fromPhone, 
    toTarget, 
    contentType: content.type,
    isReply: !!actualReplyToId,
    replyToTimestamp 
  });

  try {
    const entity = await entityResolver.getEntity(client, fromPhone, toTarget);
    
    let result;
    if (content.type === 'text' || content.type === 'emoji') {
      result = await client.sendMessage(entity, {
        message: content.value,
        replyTo: actualReplyToId,  
      });
    } 

    const messageId = result?.id;
    const sentToInfo = entity.username || entity.phone || entity.title || toTarget;

    logger.info('Message sent successfully', { 
      fromPhone, 
      sentTo: sentToInfo, 
      messageId,
      repliedTo: actualReplyToId 
    });

    return {
      sentTo: sentToInfo,
      messageId,
    };
  } catch (err: unknown) {
    const error = err as Error;
    logger.error('Failed to send message', { 
      fromPhone, 
      toTarget, 
      error: error.message 
    });

    if (error.message.includes('CHAT_WRITE_FORBIDDEN')) {
      throw new Error('You do not have permission to send messages to this chat');
    }

    if (error.message.includes('USER_IS_BLOCKED')) {
      throw new Error('You have been blocked by this user');
    }

    if (error.message.includes('USER_BANNED_IN_CHANNEL')) {
      throw new Error('You are banned from sending messages in this group/channel');
    }

    throw err;
  }
};
