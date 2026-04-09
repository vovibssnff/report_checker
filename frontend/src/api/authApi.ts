import type { DevLoginPayload, DevRegisterPayload, User } from '../types/user';
import { apiGet, apiPost } from './client';

export interface LoginRedirectResponse {
  redirect_url: string;
}

export interface AuthModeResponse {
  mode: 'dev' | 'itmo_id';
}

export async function devLogin(payload: DevLoginPayload): Promise<User> {
  const data = await apiPost<User>('/auth/dev/login', { email: payload.email, password: payload.password });
  return data;
}

export async function devRegister(payload: DevRegisterPayload): Promise<User> {
  const data = await apiPost<User>('/auth/dev/register', payload);
  return data;
}

export async function logout(): Promise<void> {
  return apiPost<void>('/auth/logout');
}

export async function fetchMe(): Promise<User> {
  const data = await apiGet<User>('/auth/me');
  return data;
}

export async function getLoginUrl(): Promise<string> {
  const data = await apiGet<LoginRedirectResponse>('/auth/login');
  return data.redirect_url;
}

export async function getAuthMode(): Promise<AuthModeResponse['mode']> {
  const data = await apiGet<AuthModeResponse>('/auth/mode');
  return data.mode;
}
