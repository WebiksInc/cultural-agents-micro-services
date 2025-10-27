import { getClient } from './clientManager';

export async function markAsRead(
  phone: string,
  chatIdentifier: string,
  messageIds: number[]
): Promise<void> {
  const client = await getClient(phone);
  
  if (!client) {
    throw new Error('User not authenticated');
  }
  
  try {
    await client.markAsRead(chatIdentifier);
  } catch (error) {
    throw new Error('Failed to mark messages as read');
  }
}

