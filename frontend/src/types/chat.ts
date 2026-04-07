export type Source = 'script' | 'docs' | 'expert' | 'new_doc';
export type MessageRole = 'user' | 'assistant';
export type MessageStatus = 'sending' | 'sent' | 'delivered' | 'error';

export interface ChatSummary {
  id: string;
  title: string;
  description?: string;
  sources?: Source[];
  updatedAt: string;
  lastMessagePreview?: string;
}

export interface ChatMessage {
  id: string;
  chatId: string;
  role: MessageRole;
  body: string;
  sources?: Source[];
  status?: MessageStatus;
  createdAt: string;
}

export interface ChatDetail extends ChatSummary {
  messages: ChatMessage[];
}

export interface SendMessagePayload {
  chatId: string;
  body: string;
}

export interface IncomingMessagePayload {
  chatId: string;
  message: ChatMessage;
}
