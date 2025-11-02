import * as logger from '../utils/logger';
import * as sessionManager from './sessionManager';
import * as chatProcessor from './chatProcessor';
import { ChatsResponse, TelegramDialog } from '../types/chats';

export async function getAllChats(accountPhone: string): Promise<ChatsResponse> {
  logger.info('Fetching all chats', { accountPhone });
  const client = await getAuthenticatedClient(accountPhone);
  const dialogs = await fetchDialogs(client);
  const { chats, details } = chatProcessor.processDialogs(dialogs);
  chatProcessor.logChatsSummary(accountPhone, details);
  return { chats, details };
}

async function getAuthenticatedClient(accountPhone: string): Promise<any> {
    const client = sessionManager.getClient(accountPhone);
    if (client) return client 
    return await sessionManager.loadSession(accountPhone);
}

async function fetchDialogs(client: any): Promise<TelegramDialog[]> {
  try {
    return await client.getDialogs({ limit: 100 });
  } catch (err: any) {
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


