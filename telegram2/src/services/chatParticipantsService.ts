import sessionManager from './sessionManager';
import logger from '../utils/logger';
import entityResolver from './entityResolver';
import { ChatParticipant, ChatParticipantsResponse } from '../types/chats';


async function getAuthenticatedClient(phone: string): Promise<any> {
  const client = sessionManager.getClient(phone);
  if (client) return client;
  return await sessionManager.loadSession(phone);
}

export const getChatParticipants = async (
  phone: string,
  chatId: string,
  limit: number = 100
): Promise<ChatParticipantsResponse> => {
  logger.info('Fetching chat participants', { phone, chatId, limit });
  
  const client = await getAuthenticatedClient(phone);
  
  if (!client) {
    throw new Error(`No authenticated session found for ${phone}`);
  }

  try {
    const entity = await entityResolver.getEntity(client, phone, chatId);
    const chatTitle = entity.title || entity.firstName || chatId;
    const chatType = entity.className === 'User' ? 'user' : 
                     entity.broadcast ? 'channel' : 'group';
    

    let chatDescription = null;
    if (entity.className !== 'User') {
      try {
        const fullChat = await client.invoke(
          new (await import('telegram')).Api.channels.GetFullChannel({
            channel: entity,
          })
        );
        chatDescription = fullChat.fullChat.about || null;
      } catch (e) {
        logger.warn('Could not fetch full chat info', { phone, chatId, error: (e as Error).message });
      }
    }

    if (entity.className === 'User') {
      const participant: ChatParticipant = {
        userId: entity.id?.toString() || null,
        firstName: entity.firstName || null,
        lastName: entity.lastName || null,
        username: entity.username || null,
        isBot: entity.bot || false,
        isSelf: false,
      };
      
      logger.info('Participants fetched successfully (DM)', { phone, chatId, count: 1 });
      
      return {
        chatId: entity.id?.toString() || chatId,
        chatTitle,
        chatType,
        chatDescription,
        participantsCount: 1,
        participants: [participant],
      };
    }
    
    const participants = await client.getParticipants(entity, {
      limit,
    });
    
    
    const transformedParticipants = participants.map((p: any) => {
      return {
        userId: p.id?.toString() || null,
        firstName: p.firstName as string | null || null,
        lastName: p.lastName as string | null || null,
        username: p.username as string | null || null,
        isBot: p.bot as boolean || false,
        isSelf: p.self as boolean || false,
      };
    });
    
    logger.info('Participants fetched successfully', { 
      phone, 
      chatId, 
      count: transformedParticipants.length 
    });
    
    return {
      chatId: entity.id?.toString() || chatId,
      chatTitle,
      chatDescription,
      chatType,
      participantsCount: transformedParticipants.length,
      participants: transformedParticipants,
    };
  } catch (err: unknown) {
    const error = err as Error;
    logger.error('Failed to fetch chat participants', { 
      phone, 
      chatId, 
      error: error.message 
    });
    
    if (error.message.includes('Could not find the input entity')) {
      throw new Error(`Chat not found: ${chatId}`);
    }
    
    if (error.message.includes('CHAT_ADMIN_REQUIRED')) {
      throw new Error('Admin privileges required to view participants');
    }
    
    if (error.message.includes('not a member')) {
      throw new Error('You are not a member of this chat');
    }
    
    throw err;
  }
};

export default {
  getChatParticipants,
};
