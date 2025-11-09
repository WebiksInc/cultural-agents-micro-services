import sessionManager from './sessionManager';
import logger from '../utils/logger.js';
import entityResolver from './entityResolver';
import { FullChatMessage, MediaInfo } from '../types/messages';

function extractMediaInfo(media: unknown): MediaInfo {
  const mediaObj = media as Record<string, unknown>;
  const className = (mediaObj.className || mediaObj.constructor?.toString() || 'unknown') as string;
  
  let type: MediaInfo['type'] = 'unknown';
  if (className.includes('Photo')) type = 'photo';
  else if (className.includes('Video')) type = 'video';
  else if (className.includes('Audio')) type = 'audio';
  else if (className.includes('Voice')) type = 'voice';
  else if (className.includes('Document')) type = 'document';
  else if (className.includes('Sticker')) type = 'sticker';
  else if (className.includes('Animation') || className.includes('Gif')) type = 'animation';
  else if (className.includes('Contact')) type = 'contact';
  else if (className.includes('Location') || className.includes('Geo')) type = 'location';
  else if (className.includes('Poll')) type = 'poll';

  const document = mediaObj.document as Record<string, unknown> | undefined;
  const photo = mediaObj.photo as Record<string, unknown> | undefined;
  const attributes = document?.attributes as Array<Record<string, unknown>> | undefined;

  return {
    type,
    fileName: attributes?.find((a) => a.fileName)?.fileName as string | undefined,
    fileSize: (document?.size || photo?.size) as number | undefined,
    duration: attributes?.find((a) => a.duration)?.duration as number | undefined,
    mimeType: document?.mimeType as string | undefined,
  };
}

function transformMessage(msg: unknown): FullChatMessage {
  const message = msg as Record<string, unknown>;
  const sender = message.sender as Record<string, unknown> | undefined;
  const replyTo = message.replyTo as Record<string, unknown> | undefined;
  
  return {
    id: message.id as number,
    date: message.date ? new Date((message.date as number) * 1000).toISOString() : new Date().toISOString(),
    text: (message.message as string) || null,
    senderId: message.senderId?.toString() || null,
    senderUsername: sender?.username as string | null || null,
    senderFirstName: sender?.firstName as string | null || null,
    senderLastName: sender?.lastName as string | null || null,
    isOutgoing: (message.out as boolean) || false,
    isForwarded: message.fwdFrom !== undefined && message.fwdFrom !== null,
    replyToMessageId: (replyTo?.replyToMsgId as number) || null,
    media: message.media ? extractMediaInfo(message.media) : null,
    views: (message.views as number) || null,
    forwards: (message.forwards as number) || null,
  };
}

export const getMessages = async (
  phone: string,
  chatId: string,
  limit: number
): Promise<{ chatId: string; chatTitle: string; messages: FullChatMessage[] }> => {
  const client = sessionManager.getClient(phone);
  
  if (!client) {
    throw new Error(`No authenticated session found for ${phone}`);
  }

  logger.info('Fetching messages from chat', { phone, chatId, limit });

  try {
    const entity = await entityResolver.getEntity(client, phone, chatId);
    
    const messages = await client.getMessages(entity, {
      limit,
      reverse: false,
    });

    const chatTitle = entity.title || entity.firstName || chatId;
    const transformedMessages = messages.map((msg: unknown) => transformMessage(msg));

    logger.info('Messages fetched successfully', { 
      phone, 
      chatId, 
      count: transformedMessages.length 
    });

    return {
      chatId: entity.id?.toString() || chatId,
      chatTitle,
      messages: transformedMessages,
    };
  } catch (err: unknown) {
    const error = err as Error;
    logger.error('Failed to fetch messages', { phone, chatId, error: error.message });
    
    if (error.message.includes('Could not find the input entity')) {
      throw new Error(`Chat not found: ${chatId}`);
    }
    
    if (error.message.includes('CHAT_WRITE_FORBIDDEN') || 
        error.message.includes('not a member')) {
      throw new Error('You are not a member of this chat or don\'t have permission to read messages');
    }
    
    throw err;
  }
};

export default {
  getMessages,
};
