import logger from '../utils/logger';
import sessionManager from './sessionManager';
import { UnreadMessage } from '../types/messages';
import { 
  resolveEntity, 
  getUnreadCount, 
  filterAndMapUnreadMessages 
} from './messageProcessor';

async function getAuthenticatedClient(accountPhone: string): Promise<any> {
    const client = sessionManager.getClient(accountPhone);
    if (client) return client 
    return await sessionManager.loadSession(accountPhone);
}

async function fetchAndProcessMessages(
  client: any,
  entity: any,
  unreadCount: number
): Promise<UnreadMessage[]> {
  if (unreadCount === 0) {
    logger.info('No unread messages', { unreadCount });
    return [];
  }
  
  logger.debug('Fetching messages', { unreadCount });
  const messages = await client.getMessages(entity, { limit: unreadCount });
  logger.debug('Messages fetched', { 
    total: messages.length,
    messageIds: messages.map((m: any) => m.id)
  });
  
  return filterAndMapUnreadMessages(messages);
}

async function markMessagesAsRead(client: any, entity: any): Promise<void> {
  await client.markAsRead(entity);
  logger.debug('Messages marked as read');
}

export const getUnreadMessages = async (
  accountPhone: string,
  target?: string,
  chatId?: string
): Promise<{ unread: UnreadMessage[]; count: number }> => {
  logger.info('Fetching unread messages', { accountPhone, target, chatId });
  
  const client = await getAuthenticatedClient(accountPhone);
  const entity = await resolveEntity(client, target, chatId);
  const unreadCount = await getUnreadCount(client, entity);
  const unreadMessages = await fetchAndProcessMessages(client, entity, unreadCount);
  
  await markMessagesAsRead(client, entity);
  
  logger.info('Unread messages fetched and marked as read', {
    accountPhone,
    target,
    chatId,
    count: unreadMessages.length,
  });
  
  return { unread: unreadMessages, count: unreadMessages.length };
}

export default {
  getUnreadMessages,
};



