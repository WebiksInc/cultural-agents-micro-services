import sessionManager from './sessionManager';
import validators from '../utils/validators';
import logger from '../utils/logger';
import entityResolver from './entityResolver';
import chatMessagesService from './chatMessagesService';
import { Api } from 'telegram';

export const addReaction = async (
  phone: string,
  chatId: string,
  messageId?: number,
  messageTimestamp?: string,
  emoji?: string
): Promise<{ chatId: string; messageId: number; emoji: string }> => {
  validators.validatePhone(phone);
  validators.validateTarget(chatId);

  if (!emoji) {
    throw new Error('Emoji is required');
  }

  let actualMessageId: number | undefined = messageId;
  if (messageTimestamp) {
    const resolvedId = await chatMessagesService.findMessageIdByTimestamp(
      phone,
      chatId,
      messageTimestamp
    );
    
    if (!resolvedId) {
      throw new Error(`Could not find message with timestamp: ${messageTimestamp}`);
    }
    
    actualMessageId = resolvedId;
    
    logger.info('Resolved timestamp to message ID', { 
      phone, 
      chatId,
      timestamp: messageTimestamp, 
      messageId: actualMessageId 
    });
  }

  if (!actualMessageId) {
    throw new Error('Either messageId or messageTimestamp must be provided');
  }

  const client = sessionManager.getClient(phone);
  if (!client) {
    throw new Error(`No authenticated session found for ${phone}`);
  }

  logger.info('Adding reaction', { 
    phone, 
    chatId, 
    messageId: actualMessageId,
    emoji 
  });

  try {
    const entity = await entityResolver.getEntity(client, phone, chatId);
    
    await client.invoke(
      new Api.messages.SendReaction({
        peer: entity,
        msgId: actualMessageId,
        reaction: [
          new Api.ReactionEmoji({
            emoticon: emoji,
          }),
        ],
      })
    );

    logger.info('Reaction added successfully', { 
      phone, 
      chatId, 
      messageId: actualMessageId,
      emoji 
    });

    return {
      chatId,
      messageId: actualMessageId,
      emoji,
    };
  } catch (err: unknown) {
    const error = err as Error;
    logger.error('Failed to add reaction', { 
      phone, 
      chatId, 
      messageId: actualMessageId,
      error: error.message 
    });

    if (error.message.includes('MESSAGE_NOT_MODIFIED')) {
      throw new Error('Reaction already exists or no change made');
    }

    if (error.message.includes('REACTION_INVALID')) {
      throw new Error('Invalid emoji reaction');
    }

    throw err;
  }
};

export default { addReaction };
