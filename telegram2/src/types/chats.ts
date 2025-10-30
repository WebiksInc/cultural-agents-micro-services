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
