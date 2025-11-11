import logger from '../utils/logger';
import sessionManager from './sessionManager';
import chatProcessor from './chatProcessor';
import { ChatsResponse, TelegramDialog } from '../types/chats';



async function getAuthenticatedClient(accountPhone: string): Promise<any> {
    const client = sessionManager.getClient(accountPhone);
    if (client) return client;
    return await sessionManager.loadSession(accountPhone);
}

async function fetchDialogs(client: any): Promise<TelegramDialog[]> {
  try {
    return await client.getDialogs({ limit: 100 });
  } catch (err: any) {
    throw new Error(`Failed to fetch chats: ${err.message}`);
  }
}

export const getAllChats = async (accountPhone: string): Promise<ChatsResponse> => {
  logger.info('Fetching all chats', { accountPhone });
  const client = await getAuthenticatedClient(accountPhone);
  const dialogs = await fetchDialogs(client);
  const { chats, details } = chatProcessor.processDialogs(dialogs);
  chatProcessor.logChatsSummary(accountPhone, details);
  return { chats, details };
}

export const getGroupsOnly = async (accountPhone: string): Promise<ChatsResponse> => {
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

export default {
  getAllChats,
  getGroupsOnly,
};

