// Keep in sync with `frontend/src/api/client.ts`
const API_BASE = (import.meta as unknown as { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL ?? '/api/v1';

export type BackendDocumentStatus = 'pending' | 'checking' | 'passed' | 'failed' | 'warning';

export interface BackendDocumentResponse {
  id: string;
  document_type: string;
  filename: string;
  file_size: number;
  status: BackendDocumentStatus | string;
  source: string;
  uploader_name?: string | null;
  uploaded_at: string;
  checked_at: string | null;
  page_count: number | null;
}

export interface BackendCheckResultResponse {
  id: string;
  rule_code: string;
  severity: string;
  status: string;
  message: string;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface BackendDocumentDetailResponse extends BackendDocumentResponse {
  check_results: BackendCheckResultResponse[];
}

export interface BackendPaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ListDocumentsParams {
  page?: number;
  size?: number;
  document_type?: string;
  status?: string;
}

function buildQuery(params: ListDocumentsParams): string {
  const search = new URLSearchParams();
  if (params.page !== undefined) search.set('page', String(params.page));
  if (params.size !== undefined) search.set('size', String(params.size));
  if (params.document_type) search.set('document_type', params.document_type);
  if (params.status) search.set('status', params.status); // backend expects alias="status"
  const q = search.toString();
  return q ? `?${q}` : '';
}

async function fetchJson<T>(url: string, init: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(`API ${res.status}: ${url}`);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export async function uploadDocuments(files: File[], documentType: string): Promise<BackendDocumentResponse[]> {
  const form = new FormData();
  for (const f of files) form.append('files', f);
  form.append('document_type', documentType);

  return fetchJson<BackendDocumentResponse[]>(`${API_BASE}/documents/`, {
    method: 'POST',
    credentials: 'include',
    body: form,
  });
}

export async function listDocuments(params: ListDocumentsParams = {}): Promise<BackendPaginatedResponse<BackendDocumentResponse>> {
  const query = buildQuery(params);
  return fetchJson<BackendPaginatedResponse<BackendDocumentResponse>>(`${API_BASE}/documents/${query}`, {
    method: 'GET',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function getDocument(documentId: string): Promise<BackendDocumentDetailResponse> {
  return fetchJson<BackendDocumentDetailResponse>(`${API_BASE}/documents/${documentId}`, {
    method: 'GET',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function deleteDocument(documentId: string): Promise<void> {
  await fetchJson<void>(`${API_BASE}/documents/${documentId}`, {
    method: 'DELETE',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
  });
}

export function getDocumentDownloadUrl(documentId: string): string {
  return `${API_BASE}/documents/${documentId}/download`;
}

export function getDocumentReportUrl(documentId: string, format: 'csv' | 'pdf' = 'csv'): string {
  // backend supports `format=csv` (and a placeholder PDF report)
  return `${API_BASE}/documents/${documentId}/report?format=${encodeURIComponent(format)}`;
}

