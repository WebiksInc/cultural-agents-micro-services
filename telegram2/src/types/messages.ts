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
