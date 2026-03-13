const API_BASE = import.meta.env.VITE_API_URL ?? 'http://185.137.232.199:8000/api';

const TOKEN_KEY = 'auth_access_token';
const REFRESH_TOKEN_KEY = 'auth_refresh_token';

function getHeaders(): HeadersInit {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null;
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

export function getStoredToken(): string | null {
  return typeof localStorage !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null;
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function getStoredRefreshToken(): string | null {
  return typeof localStorage !== 'undefined' ? localStorage.getItem(REFRESH_TOKEN_KEY) : null;
}

export function setStoredRefreshToken(token: string): void {
  localStorage.setItem(REFRESH_TOKEN_KEY, token);
}

export function clearStoredRefreshToken(): void {
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

const fetchOpts: RequestInit = {
  credentials: 'include',
};

interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: { id: string; email: string; name: string; organization?: string };
}

async function doRefresh(): Promise<void> {
  const refreshToken = getStoredRefreshToken();
  if (!refreshToken) throw new Error('No refresh token');
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    ...fetchOpts,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) throw new Error(`Refresh failed: ${res.status}`);
  const data = (await res.json()) as AuthResponse;
  setStoredToken(data.access_token);
  setStoredRefreshToken(data.refresh_token);
}

function clearAuth(): void {
  clearStoredToken();
  clearStoredRefreshToken();
}

async function handleResponse<T>(res: Response, path: string): Promise<T> {
  if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
  if (res.status === 204) return undefined as T;
  return res.json();
}

async function request<T>(
  path: string,
  init: RequestInit,
  parseResponse: (res: Response) => Promise<T>,
  retried = false
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { ...fetchOpts, ...init });
  if (res.status === 401 && !retried && getStoredRefreshToken()) {
    try {
      await doRefresh();
      const retryInit = { ...init, headers: getHeaders() };
      const retryRes = await fetch(`${API_BASE}${path}`, { ...fetchOpts, ...retryInit });
      return parseResponse(retryRes);
    } catch {
      clearAuth();
      throw new Error(`API ${path}: 401`);
    }
  }
  if (!res.ok) {
    if (res.status === 401) clearAuth();
    throw new Error(`API ${path}: ${res.status}`);
  }
  return parseResponse(res);
}

export async function apiGet<T>(path: string): Promise<T> {
  return request(path, { headers: getHeaders() }, (res) => handleResponse<T>(res, path));
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const bodySerialized = body !== undefined && body !== null ? JSON.stringify(body) : undefined;
  return request(
    path,
    {
      method: 'POST',
      headers: getHeaders(),
      ...(bodySerialized != null && { body: bodySerialized }),
    },
    (res) => handleResponse<T>(res, path)
  );
}

export async function apiPatch<T>(path: string, body?: unknown): Promise<T> {
  return request(
    path,
    {
      method: 'PATCH',
      headers: getHeaders(),
      body: body != null ? JSON.stringify(body) : undefined,
    },
    (res) => handleResponse<T>(res, path)
  );
}

export async function apiDelete(path: string): Promise<void> {
  return request(
    path,
    { method: 'DELETE', headers: getHeaders() },
    (res) => handleResponse<void>(res, path)
  );
}

export function getWsUrl(): string {
  const base = import.meta.env.VITE_WS_URL ?? new URL(API_BASE).origin.replace(/^http/, 'ws');
  return `${base}/ws`;
}
