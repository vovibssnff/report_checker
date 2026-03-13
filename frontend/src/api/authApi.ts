import type { AuthResponse, LoginPayload, RegisterPayload, User } from '../types/user';
import { apiGet, apiPost } from './client';

function normalizeAuthResponse(data: Record<string, unknown>): AuthResponse {
  const token = (data.token ?? data.access_token) as string | undefined;
  const userRaw = data.user as Record<string, unknown> | undefined;
  if (!token || !userRaw) throw new Error('Invalid auth response');
  const user: User = {
    id: (userRaw.id ?? userRaw.user_id) as string,
    email: (userRaw.email as string) ?? '',
    name: (userRaw.name as string) ?? '',
    organization: (userRaw.organization ?? userRaw.account_name) as string | undefined,
  };
  return {
    access_token: token,
    refresh_token: (data.refresh_token as string) ?? token,
    token_type: (data.token_type as string) ?? 'Bearer',
    user,
  };
}

export async function login(payload: LoginPayload): Promise<AuthResponse> {
  const body = { email: payload.email, password: payload.password };
  const data = await apiPost<Record<string, unknown>>('/auth/login', body);
  return normalizeAuthResponse(data);
}

export async function register(payload: RegisterPayload): Promise<AuthResponse> {
  const data = await apiPost<Record<string, unknown>>('/auth/register', payload);
  return normalizeAuthResponse(data);
}

export async function refresh(): Promise<AuthResponse> {
  return apiPost<AuthResponse>('/auth/refresh');
}

export async function logout(): Promise<void> {
  return apiPost<void>('/auth/logout');
}

export async function fetchMe(): Promise<User> {
  const data = await apiGet<Record<string, unknown>>('/auth/me');
  return {
    id: (data.id ?? data.user_id) as string,
    email: (data.email as string) ?? '',
    name: (data.name as string) ?? '',
    organization: (data.organization ?? data.account_name) as string | undefined,
  };
}
