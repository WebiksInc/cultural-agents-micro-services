import * as logger from '../utils/logger';
import * as sessionManager from './sessionManager';

interface ChatInfo {
  id: string;
  name: string;
  type: 'user' | 'group' | 'channel' | 'bot';
  username?: string;
}

interface ChatsResponse {
  chats: Record<string, string>;
  details: ChatInfo[];
}

export async function getAllChats(accountPhone: string): Promise<ChatsResponse> {
  logger.info('Fetching all chats', { accountPhone });
  
  let client = sessionManager.getClient(accountPhone);
  
  if (!client) {
    client = await sessionManager.loadSession(accountPhone);
  }
  
  if (!client) {
    throw new Error('Account not authenticated. Please authenticate first.');
  }
  
  try {
    const dialogs = await client.getDialogs({ limit: 100 });
    
    const chats: Record<string, string> = {};
    const details: ChatInfo[] = [];
    
    for (const dialog of dialogs) {
      const entity = dialog.entity;
      
      let name = dialog.title || 'Unknown';
      let id = entity.id?.toString() || '';
      let type: 'user' | 'group' | 'channel' | 'bot' = 'user';
      let username: string | undefined;
      
      if (entity.className === 'User') {
        const firstName = (entity as any).firstName || '';
        const lastName = (entity as any).lastName || '';
        name = `${firstName} ${lastName}`.trim() || 'Unknown User';
        type = (entity as any).bot ? 'bot' : 'user';
        username = (entity as any).username;
      } else if (entity.className === 'Channel') {
        name = (entity as any).title || 'Unknown Channel';
        type = (entity as any).broadcast ? 'channel' : 'group';
        username = (entity as any).username;
      } else if (entity.className === 'Chat') {
        name = (entity as any).title || 'Unknown Chat';
        type = 'group';
      }
      
      if (id) {
        chats[name] = id;
        details.push({
          id,
          name,
          type,
          username,
        });
      }
    }
    
    logger.info('Chats fetched successfully', { 
      accountPhone, 
      totalChats: details.length,
      users: details.filter(d => d.type === 'user').length,
      groups: details.filter(d => d.type === 'group').length,
      channels: details.filter(d => d.type === 'channel').length,
      bots: details.filter(d => d.type === 'bot').length,
    });
    
    return { chats, details };
  } catch (err: any) {
    logger.error('Failed to fetch chats', { accountPhone, error: err.message });
    throw new Error(`Failed to fetch chats: ${err.message}`);
  }
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

