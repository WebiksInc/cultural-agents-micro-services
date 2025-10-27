import { getClient } from './clientManager';
import { Api } from 'telegram';

export async function sendMessage(
  senderPhone: string,
  receiverPhone: string,
  message: string
): Promise<boolean> {
  const client = await getClient(senderPhone);
  
  if (!client) {
    throw new Error('Sender not authenticated');
  }
  
  try {
    await client.sendMessage(receiverPhone, { message });
    return true;
  } catch (error) {
    throw new Error('Failed to send message');
  }
}
