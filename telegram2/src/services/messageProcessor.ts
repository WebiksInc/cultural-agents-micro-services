import * as logger from '../utils/logger';
import { UnreadMessage } from '../types/messages';

export async function resolveEntity(client: any, target?: string, chatId?: string): Promise<any> {
  if (!target && !chatId) {
    throw new Error('Either target or chatId must be provided');
  }
  
  if (chatId) {
    const idNum = BigInt(chatId);
    const entity = await client.getEntity(idNum);
    logger.debug('Entity fetched by chatId', { chatId, entityId: entity.id.toString() });
    return entity;
  }
  
  if (target) {
    const entity = await client.getEntity(target);
    logger.debug('Entity fetched by target', { target, entityId: entity.id.toString() });
    return entity;
  }
}

export async function getUnreadCount(client: any, entity: any): Promise<number> {
  const dialogs = await client.getDialogs({ limit: 100 });
  logger.debug('Dialogs fetched', { count: dialogs.length });
  
  const dialog = findMatchingDialog(dialogs, entity);
  
  const unreadCount = dialog?.unreadCount || 0;
  logger.debug('Unread count determined', { unreadCount, found: !!dialog });
  
  return unreadCount;
}

function findMatchingDialog(dialogs: any[], entity: any): any | undefined {
  const targetId = entity.id.toString();
  
  return dialogs.find((d: any) => {
    const dialogId = d.entity.id.toString();
    const match = dialogId === targetId;
    
    logger.debug('Comparing dialog', { 
      dialogId, 
      targetId, 
      match,
      unreadCount: d.unreadCount 
    });
    
    return match;
  });
}

export function filterAndMapUnreadMessages(messages: any[]): UnreadMessage[] {
  return messages
    .filter((m: any) => {
      const isIncoming = !m.out;
      logger.debug('Message details', { 
        id: m.id, 
        isOut: m.out,
        hasMessage: !!m.message,
        sender: m.sender?.username || m.sender?.phone || 'Unknown',
        isIncoming
      });
      return isIncoming;
    })
    .map((m: any) => ({
      id: m.id,
      sender: m.sender?.username || m.sender?.phone || 'Unknown',
      message: m.message || '',
      date: new Date(m.date * 1000).toISOString(),
      isOut: m.out,
    }));
}
