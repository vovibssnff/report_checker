import type { ChatDetail, ChatSummary, SendMessagePayload } from '../types/chat';
import { apiGet, apiPost } from './client';

export async function fetchChats(): Promise<ChatSummary[]> {
  return apiGet<ChatSummary[]>('/chats');
}

export async function fetchChatById(id: string): Promise<ChatDetail> {
  return apiGet<ChatDetail>(`/chats/${id}`);
}

export async function sendMessage(payload: SendMessagePayload): Promise<{ messageId: string }> {
  return apiPost<{ messageId: string }>(`/chats/${payload.chatId}/messages`, { body: payload.body });
}

export async function createChat(): Promise<ChatSummary> {
  return apiPost<ChatSummary>('/chats', { title: 'New Chat' });
}
