export interface UnreadMessage {
  id: number;
  sender: string;
  message: string;
  date: string;
  isOut: boolean;
}

// Get chat messages types
export interface GetChatMessagesParams {
  phone: string;
  chatId: string;
  limit: number;
}

export interface MediaInfo {
  type: 'photo' | 'video' | 'document' | 'audio' | 'sticker' | 'voice' | 'video_note' | 'animation' | 'contact' | 'location' | 'poll' | 'unknown';
  fileName?: string;
  fileSize?: number;
  duration?: number;
  mimeType?: string;
}

export interface MessageReaction {
  emoji: string;      
  count: number;     
}
export interface FullChatMessage {
  id: number;
  date: string;
  text: string | null;
  senderId: string | null;
  senderUsername: string | null;
  senderFirstName: string | null;
  senderLastName: string | null;
  isOutgoing: boolean;
  isForwarded: boolean;
  replyToMessageId: number | null;
  media: MediaInfo | null;
  reactions: MessageReaction[];
  views: number | null;
  forwards: number | null;
}

export interface GetChatMessagesResponse {
  success: true;
  chatId: string;
  chatTitle: string;
  phone: string;
  messagesCount: number;
  messages: FullChatMessage[];
}

// Send message types
export interface SendMessageContent {
  type: 'text' | 'emoji';
  value: string;
}

export interface SendMessageRequest {
  fromPhone: string;
  toTarget: string;
  content: SendMessageContent;
  replyTo?: number;
}

export interface SendMessageResponse {
  success: true;
  sentTo: string;
  messageId?: number;
}
