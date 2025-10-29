import * as logger from '../utils/logger';
import * as sessionManager from './sessionManager';

interface UnreadMessage {
  id: number;
  sender: string;
  message: string;
  date: string;
  isOut: boolean;
}

export async function getUnreadMessages(
  accountPhone: string,
  target?: string,
  chatId?: string
): Promise<{ unread: UnreadMessage[]; count: number }> {
  logger.info('Fetching unread messages', { accountPhone, target, chatId });
  
  let client = sessionManager.getClient(accountPhone);
  
  if (!client) {
    client = await sessionManager.loadSession(accountPhone);
  }
  
  if (!client) {
    throw new Error('Account not authenticated. Please authenticate first.');
  }
  
  let entity;
  
  if (chatId) {
    const idNum = BigInt(chatId);
    entity = await client.getEntity(idNum);
    logger.debug('Entity fetched by chatId', { chatId, entityId: entity.id.toString() });
  } else if (target) {
    entity = await client.getEntity(target);
    logger.debug('Entity fetched by target', { target, entityId: entity.id.toString() });
  } else {
    throw new Error('Either target or chatId must be provided');
  }
  
  const dialogs = await client.getDialogs({ limit: 100 });
  logger.debug('Dialogs fetched', { count: dialogs.length });
  
  const dialog = dialogs.find((d: any) => {
    const dialogEntity = d.entity;
    const dialogId = dialogEntity.id.toString();
    const targetId = entity.id.toString();
    logger.debug('Comparing dialog', { 
      dialogId, 
      targetId, 
      match: dialogId === targetId,
      unreadCount: d.unreadCount 
    });
    return dialogId === targetId;
  });
  
  logger.debug('Dialog found', { found: !!dialog, unreadCount: dialog?.unreadCount });
  
  const unreadCount = dialog?.unreadCount || 0;
  
  if (unreadCount === 0) {
    logger.info('No unread messages reported by dialog', { accountPhone, target, chatId });
    // Even if unreadCount is 0, let's still fetch some recent messages to check
    // This handles cases where Telegram's unread counter might be out of sync
  }
  
  // Fetch more messages than the unread count to be safe
  const fetchLimit = Math.max(unreadCount, 20);
  logger.debug('Fetching messages', { unreadCount, fetchLimit });
  const messages = await client.getMessages(entity, { limit: fetchLimit });
  logger.debug('Messages fetched', { 
    total: messages.length,
    messageIds: messages.map((m: any) => m.id)
  });
  
  const unreadMessages: UnreadMessage[] = messages
    .filter((m: any) => {
      logger.debug('Message details', { 
        id: m.id, 
        isOut: m.out,
        hasMessage: !!m.message,
        sender: m.sender?.username || m.sender?.phone || 'Unknown'
      });
      return !m.out;
    })
    .map((m: any) => ({
      id: m.id,
      sender: m.sender?.username || m.sender?.phone || 'Unknown',
      message: m.message || '',
      date: new Date(m.date * 1000).toISOString(),
      isOut: m.out,
    }));
  
  await client.markAsRead(entity);
  
  logger.info('Unread messages fetched and marked as read', {
    accountPhone,
    target,
    chatId,
    count: unreadMessages.length,
  });
  
  return { unread: unreadMessages, count: unreadMessages.length };
}


