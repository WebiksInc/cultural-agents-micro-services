export type EntityType = 'user' | 'group' | 'channel' | 'bot';

export interface ChatInfo {
  id: string;
  name: string;
  type: EntityType;
  username?: string;
}

export interface ChatsResponse {
  chats: Record<string, string>;
  details: ChatInfo[];
}

export interface ChatParticipant {
  userId: string | null;
  firstName: string | null;
  lastName: string | null;
  username: string | null;
  isBot: boolean;
  isSelf: boolean;
}

export interface ChatParticipantsResponse {
  chatId: string;
  chatTitle: string;
  chatType: string;
  participantsCount: number;
  participants: ChatParticipant[];
}

export interface TelegramEntity {
  id: any;
  className?: string;
  firstName?: string;
  lastName?: string;
  username?: string;
  title?: string;
  bot?: boolean;
  broadcast?: boolean;
}

export interface TelegramDialog {
  entity: TelegramEntity;
  title?: string;
}
