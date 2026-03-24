import type { DevLoginPayload, User } from '../types/user';
import { apiGet, apiPost } from './client';

export async function devLogin(payload: DevLoginPayload): Promise<User> {
  // Backend sets an HttpOnly cookie `access_token` and returns the current user in JSON.
  const data = await apiPost<User>('/auth/dev/login', { email: payload.email, name: payload.name });
  return data;
}

export async function logout(): Promise<void> {
  return apiPost<void>('/auth/logout');
}

export async function fetchMe(): Promise<User> {
  const data = await apiGet<User>('/auth/me');
  return data;
}
