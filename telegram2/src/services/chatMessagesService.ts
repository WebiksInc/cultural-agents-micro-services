import sessionManager from './sessionManager';
import logger from '../utils/logger.js';
import entityResolver from './entityResolver';
import { FullChatMessage } from '../types/messages';
import { transformMessage } from '../utils/chatMessage';

export const findMessageIdByTimestamp = async (
  phone: string,
  chatId: string,
  targetTimestamp: string  // ISO string like "2025-11-11T14:30:00.000Z"
): Promise<number | null> => {
  const client = sessionManager.getClient(phone);
  

  logger.info('Finding message by timestamp', { phone, chatId, targetTimestamp });

  try {
    const entity = await entityResolver.getEntity(client, phone, chatId);
    const targetDate = Math.floor(new Date(targetTimestamp).getTime() / 1000);
    const messages = await client.getMessages(entity, {
      limit: 3,  
      offsetDate: targetDate + 1,
    });

    if (messages.length === 0) {
      logger.warn('No messages found near timestamp', { phone, chatId, targetTimestamp });
      return null;
    }

    const transformedMessages = messages.map((msg: unknown) => transformMessage(msg));
    const exactMatch = transformedMessages.find((msg: FullChatMessage) => msg.date === targetTimestamp);
    if (exactMatch) {
      logger.info('Message found by timestamp', { phone, chatId, messageId: exactMatch.id });
      return exactMatch.id;
    }

    logger.warn('Exact timestamp match not found', { phone, chatId, targetTimestamp });
    return null;

  } catch (err: unknown) {
    const error = err as Error;
    logger.error('Failed to find message by timestamp', { phone, chatId, error: error.message });
    throw err;
  }
};

export const getMessages = async (
  phone: string,
  chatId: string,
  limit: number
): Promise<{ chatId: string; chatTitle: string; messages: FullChatMessage[] }> => {
  const client = sessionManager.getClient(phone);
  
  if (!client) {
    throw new Error(`No authenticated session found for ${phone}`);
  }

  logger.info('Fetching messages from chat', { phone, chatId, limit });

  try {
    const entity = await entityResolver.getEntity(client, phone, chatId);
    
    const messages = await client.getMessages(entity, {
      limit,
      reverse: false,
    });

    const chatTitle = entity.title || entity.firstName || chatId;
    const transformedMessages = messages.map((msg: unknown) => transformMessage(msg));

    logger.info('Messages fetched successfully', { 
      phone, 
      chatId, 
      count: transformedMessages.length 
    });

    return {
      chatId: entity.id?.toString() || chatId,
      chatTitle,
      messages: transformedMessages,
    };
  } catch (err: unknown) {
    const error = err as Error;
    logger.error('Failed to fetch messages', { phone, chatId, error: error.message });
    
    if (error.message.includes('Could not find the input entity')) {
      throw new Error(`Chat not found: ${chatId}`);
    }
    
    if (error.message.includes('CHAT_WRITE_FORBIDDEN') || 
        error.message.includes('not a member')) {
      throw new Error('You are not a member of this chat or don\'t have permission to read messages');
    }
    
    throw err;
  }
};

export default {
  getMessages,
  findMessageIdByTimestamp,
};

