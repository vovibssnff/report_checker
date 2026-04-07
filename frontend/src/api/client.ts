// Backend is mounted behind Caddy at `/api/*` and the FastAPI app is prefixed with `/api/v1`.
// In production we want relative URLs so cookies are automatically included.
const API_BASE = (import.meta as unknown as { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL ?? '/api/v1';

const fetchOpts: RequestInit = {
  credentials: 'include',
};

function getDefaultHeaders(): HeadersInit {
  return { 'Content-Type': 'application/json' };
}

async function handleResponse<T>(res: Response, path: string): Promise<T> {
  if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
  if (res.status === 204) return undefined as T;
  return res.json();
}

async function request<T>(path: string, init: RequestInit, parseResponse: (res: Response) => Promise<T>): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { ...fetchOpts, ...init });
  if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
  return parseResponse(res);
}

export async function apiGet<T>(path: string): Promise<T> {
  return request(path, { headers: getDefaultHeaders() }, (res) => handleResponse<T>(res, path));
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const bodySerialized = body !== undefined && body !== null ? JSON.stringify(body) : undefined;
  return request(
    path,
    {
      method: 'POST',
      headers: getDefaultHeaders(),
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
      headers: getDefaultHeaders(),
      body: body != null ? JSON.stringify(body) : undefined,
    },
    (res) => handleResponse<T>(res, path)
  );
}

export async function apiDelete<T = void>(path: string): Promise<T> {
  return request(
    path,
    { method: 'DELETE', headers: getDefaultHeaders() },
    (res) => handleResponse<T>(res, path)
  );
}

export function getWsUrl(): string {
  // Current backend implementation does not expose WebSocket endpoints, but keep this helper
  // for any future realtime features.
  const origin =
    typeof window !== 'undefined' && window.location?.origin ? window.location.origin : 'http://localhost';
  return `${origin.replace(/^http/, 'ws')}/ws`;
}
