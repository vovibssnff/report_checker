import { makeAutoObservable, runInAction } from 'mobx';
import type { ChatMessage, ChatSummary } from '../types/chat';
import * as chatApi from '../api/chatApi';
import { subscribeToMessages } from '../api/wsClient';

export class ChatStore {
  chats: ChatSummary[] = [];
  selectedChatId: string | null = null;
  messagesByChatId: Record<string, ChatMessage[]> = {};
  loadingChats = false;
  loadingChat = false;
  sendingMessage = false;
  error: string | null = null;

  private unsubscribeWs: (() => void) | null = null;

  constructor() {
    makeAutoObservable(this);
    this.unsubscribeWs = subscribeToMessages((payload: unknown) => {
      runInAction(() => this.handleIncomingMessage(payload as { chatId: string; message: ChatMessage }));
    });
  }

  private handleIncomingMessage(payload: { chatId: string; message: ChatMessage }) {
    const list = this.messagesByChatId[payload.chatId] ?? [];
    if (list.some((m) => m.id === payload.message.id)) return;
    this.messagesByChatId[payload.chatId] = [...list, payload.message];
  }

  get selectedChat(): ChatSummary | null {
    if (!this.selectedChatId) return null;
    return this.chats.find((c) => c.id === this.selectedChatId!) ?? null;
  }

  get currentMessages(): ChatMessage[] {
    if (!this.selectedChatId) return [];
    return this.messagesByChatId[this.selectedChatId] ?? [];
  }

  setSelectedChat = (id: string | null) => {
    this.selectedChatId = id;
    if (id) this.loadChatById(id);
  };

  loadChats = async () => {
    this.loadingChats = true;
    this.error = null;
    try {
      const list = await chatApi.fetchChats();
      runInAction(() => {
        this.chats = list;
        this.loadingChats = false;
      });
    } catch (e) {
      runInAction(() => {
        this.error = e instanceof Error ? e.message : 'Failed to load chats';
        this.loadingChats = false;
      });
    }
  };

  loadChatById = async (id: string) => {
    this.loadingChat = true;
    this.error = null;
    try {
      const detail = await chatApi.fetchChatById(id);
      runInAction(() => {
        this.messagesByChatId[id] = detail.messages;
        const summary = { id: detail.id, title: detail.title, description: detail.description, sources: detail.sources, updatedAt: detail.updatedAt, lastMessagePreview: detail.lastMessagePreview };
        const idx = this.chats.findIndex((c) => c.id === id);
        if (idx >= 0) {
          const next = [...this.chats];
          next[idx] = summary;
          this.chats = next;
        } else {
          this.chats = [...this.chats, summary];
        }
        this.loadingChat = false;
      });
    } catch (e) {
      runInAction(() => {
        this.error = e instanceof Error ? e.message : 'Failed to load chat';
        this.loadingChat = false;
      });
    }
  };

  sendMessage = async (body: string) => {
    const chatId = this.selectedChatId;
    if (!chatId || !body.trim()) return;

    this.sendingMessage = true;
    this.error = null;
    const tempId = `temp-${Date.now()}`;
    const tempMessage: ChatMessage = {
      id: tempId,
      chatId,
      role: 'user',
      body: body.trim(),
      status: 'sending',
      createdAt: new Date().toISOString(),
    };

    runInAction(() => {
      const list = this.messagesByChatId[chatId] ?? [];
      this.messagesByChatId[chatId] = [...list, tempMessage];
    });

    try {
      const { messageId } = await chatApi.sendMessage({ chatId, body: body.trim() });
      runInAction(() => {
        const list = this.messagesByChatId[chatId] ?? [];
        this.messagesByChatId[chatId] = list.map((m) =>
          m.id === tempId ? { ...m, id: messageId, status: 'sent' as const } : m
        );
        this.sendingMessage = false;
      });
    } catch (e) {
      runInAction(() => {
        const list = this.messagesByChatId[chatId] ?? [];
        this.messagesByChatId[chatId] = list.map((m) =>
          m.id === tempId ? { ...m, status: 'error' as const } : m
        );
        this.error = e instanceof Error ? e.message : 'Failed to send message';
        this.sendingMessage = false;
      });
    }
  };

  createChat = async () => {
    this.error = null;
    try {
      const chat = await chatApi.createChat();
      runInAction(() => {
        this.chats = [chat, ...this.chats];
        this.selectedChatId = chat.id;
        this.messagesByChatId[chat.id] = [];
      });
    } catch (e) {
      runInAction(() => {
        this.error = e instanceof Error ? e.message : 'Failed to create chat';
      });
    }
  };

  dispose = () => {
    this.unsubscribeWs?.();
  };
}

export const chatStore = new ChatStore();
