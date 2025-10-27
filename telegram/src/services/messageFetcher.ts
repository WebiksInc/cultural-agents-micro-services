import { getClient } from './clientManager';
import { Message } from '../types';
import { Api } from 'telegram';

export async function getUnreadMessages(
  phone: string,
  chatIdentifier: string
): Promise<Message[]> {
  const client = await getClient(phone);
  
  if (!client) {
    throw new Error('User not authenticated');
  }
  
  try {
    const messages = await client.getMessages(chatIdentifier, {
      limit: 100,
    });
    
    const unread = messages.filter((msg: any) => !msg.out);
    
    return unread.map((msg: any) => ({
      id: msg.id,
      senderId: msg.fromId?.userId?.toString() || 'unknown',
      text: msg.message || '',
      timestamp: new Date(msg.date * 1000),
    }));
  } catch (error) {
    throw new Error('Failed to fetch messages');
  }
}
