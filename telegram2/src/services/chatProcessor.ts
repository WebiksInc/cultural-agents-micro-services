import * as logger from '../utils/logger';
import { 
  ChatInfo, 
  EntityType, 
  TelegramDialog, 
  TelegramEntity 
} from '../types/chats';

export function processDialogs(dialogs: TelegramDialog[]): { chats: Record<string, string>; details: ChatInfo[] } {
  const chats: Record<string, string> = {};
  const details: ChatInfo[] = [];
  for (const dialog of dialogs) {
    const chatInfo = extractChatInfo(dialog);
    if (chatInfo && chatInfo.id) {
      chats[chatInfo.name] = chatInfo.id;
      details.push(chatInfo);
    }
  }
  return { chats, details };
}

export function extractChatInfo(dialog: TelegramDialog): ChatInfo | null {
  const entity = dialog.entity;
  const id = entity.id?.toString();
  if (!id) {
    return null;
  }
  const name = determineChatName(dialog, entity);
  const type = determineChatType(entity);
  const username = entity.username;
  
  return { id, name, type, username };
}

function determineChatName(dialog: TelegramDialog, entity: TelegramEntity): string {
  switch (entity.className) {
    case 'User':
      return buildUserName(entity);
    case 'Channel':
      return entity.title || 'Unknown Channel';
    case 'Chat':
      return entity.title || 'Unknown Chat';
    default:
      return dialog.title || 'Unknown';
  }
}

function buildUserName(entity: TelegramEntity): string {
  const firstName = entity.firstName || '';
  const lastName = entity.lastName || '';
  const fullName = `${firstName} ${lastName}`.trim();
  return fullName || 'Unknown User';
}

function determineChatType(entity: TelegramEntity): EntityType {
  switch (entity.className) {
    case 'User':
      return entity.bot ? 'bot' : 'user';
    
    case 'Channel':
      return entity.broadcast ? 'channel' : 'group';
    
    case 'Chat':
      return 'group';
    
    default:
      return 'user';
  }
}

export function logChatsSummary(accountPhone: string, details: ChatInfo[]): void {
  logger.info('Chats fetched successfully', { 
    accountPhone, 
    totalChats: details.length,
    users: details.filter(d => d.type === 'user').length,
    groups: details.filter(d => d.type === 'group').length,
    channels: details.filter(d => d.type === 'channel').length,
    bots: details.filter(d => d.type === 'bot').length,
  });
}
