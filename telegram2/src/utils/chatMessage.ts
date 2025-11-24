import { FullChatMessage, MediaInfo, MessageReaction } from '../types/messages';

export function extractMediaInfo(media: unknown): MediaInfo {
  const mediaObj = media as Record<string, unknown>;
  const className = (mediaObj.className || mediaObj.constructor?.toString() || 'unknown') as string;
  
  let type: MediaInfo['type'] = 'unknown';
  if (className.includes('Photo')) type = 'photo';
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

export function extractReactions(reactions: unknown): MessageReaction[] {
  if (!reactions) return [];
  
  const reactionsObj = reactions as Record<string, unknown>;
  const results = reactionsObj.results as Array<Record<string, unknown>> | undefined;
  
  if (!Array.isArray(results)) return [];
  
  return results.map((result) => {
    const reaction = result.reaction as Record<string, unknown>;
    
    // Handle both emoticon and custom emoji reactions
    let emoji: string;
    if (reaction?.emoticon) {
      emoji = reaction.emoticon as string;
    } else if (reaction?.documentId) {
      emoji = `custom_${reaction.documentId}`;
    } else {
      emoji = 'unknown';
    }
    
    return {
      emoji,
      count: (result.count as number) || 0,
    };
  });
}

export function transformMessage(msg: unknown): FullChatMessage {
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
    reactions: extractReactions(message.reactions),
    views: (message.views as number) || null,
    forwards: (message.forwards as number) || null,
  };
}


