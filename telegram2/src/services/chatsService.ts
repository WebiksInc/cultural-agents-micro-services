import * as logger from '../utils/logger';
import * as sessionManager from './sessionManager';
import { 
  ChatInfo, 
  ChatsResponse, 
  EntityType, 
  TelegramDialog, 
  TelegramEntity 
} from '../types/chats';

export async function getAllChats(accountPhone: string): Promise<ChatsResponse> {
  logger.info('Fetching all chats', { accountPhone });
  const client = await getAuthenticatedClient(accountPhone);
  const dialogs = await fetchDialogs(client);
  const { chats, details } = processDialogs(dialogs);
  logChatsSummary(accountPhone, details);
  return { chats, details };
}

async function getAuthenticatedClient(accountPhone: string): Promise<any> {
  let client = sessionManager.getClient(accountPhone);
  if (!client) {
    client = await sessionManager.loadSession(accountPhone);
  }
  return client;
}

async function fetchDialogs(client: any): Promise<TelegramDialog[]> {
  try {
    return await client.getDialogs({ limit: 100 });
  } catch (err: any) {
    throw new Error(`Failed to fetch chats: ${err.message}`);
  }
}

function processDialogs(dialogs: TelegramDialog[]): { chats: Record<string, string>; details: ChatInfo[] } {
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

function extractChatInfo(dialog: TelegramDialog): ChatInfo | null {
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

function logChatsSummary(accountPhone: string, details: ChatInfo[]): void {
  logger.info('Chats fetched successfully', { 
    accountPhone, 
    totalChats: details.length,
    users: details.filter(d => d.type === 'user').length,
    groups: details.filter(d => d.type === 'group').length,
    channels: details.filter(d => d.type === 'channel').length,
    bots: details.filter(d => d.type === 'bot').length,
  });
}

export async function getGroupsOnly(accountPhone: string): Promise<ChatsResponse> {
  logger.info('Fetching groups only', { accountPhone });
  const allChats = await getAllChats(accountPhone);
  const groups = allChats.details.filter(d => d.type === 'group' || d.type === 'channel');
  const chats: Record<string, string> = {};
  for (const group of groups) {
    chats[group.name] = group.id;
  }
  logger.info('Groups fetched successfully', { accountPhone, count: groups.length });
  return { chats, details: groups };
}


