import * as logger from '../utils/logger';
import * as sessionManager from './sessionManager';
import { UnreadMessage } from '../types/messages';
import { 
  resolveEntity, 
  getUnreadCount, 
  filterAndMapUnreadMessages 
} from './messageProcessor';

export async function getUnreadMessages(
  accountPhone: string,
  target?: string,
  chatId?: string
): Promise<{ unread: UnreadMessage[]; count: number }> {
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

async function getAuthenticatedClient(accountPhone: string): Promise<any> {
  let client = sessionManager.getClient(accountPhone);
  
  if (!client) {
    client = await sessionManager.loadSession(accountPhone);
  }
  
  if (!client) {
    throw new Error('Account not authenticated. Please authenticate first.');
  }
  
  return client;
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


