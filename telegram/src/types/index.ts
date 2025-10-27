export interface PhoneConfig {
  phone: string;
  apiId: number;
  apiHash: string;
  verified: boolean;
}

export interface SendMessageRequest {
  senderPhone: string;
  receiverPhone: string;
  message: string;
}

export interface GetMessagesRequest {
  phone: string;
  chatId?: string;
  chatPhone?: string;
}

export interface Message {
  id: number;
  senderId: string;
  senderName?: string;
  text: string;
  timestamp: Date;
}
