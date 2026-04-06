import { makeAutoObservable, runInAction } from 'mobx';
import type { DocType, DocumentItem, DocumentStatus } from '../types/document';
import {
  deleteDocument,
  getDocumentDownloadUrl,
  listDocuments,
  uploadDocuments,
  type BackendDocumentResponse,
} from '../api/documentApi';

function mapBackendDocTypeToFrontend(docType: string): DocType {
  if (docType === 'vkr_template') return 'masters';
  if (docType === 'practice_report') return 'bachelors';
  return 'masters';
}

function mapBackendStatusToFrontend(status: string): DocumentStatus {
  if (status === 'passed') return 'passed';
  if (status === 'failed') return 'failed';
  if (status === 'warning') return 'warnings';
  // Treat checking/checking as pending for UI purposes.
  if (status === 'pending' || status === 'checking') return 'pending';
  return 'pending';
}

function mapBackendDocToItem(d: BackendDocumentResponse): DocumentItem {
  const createdAt = d.uploaded_at ? new Date(d.uploaded_at) : new Date();
  const docType = mapBackendDocTypeToFrontend(d.document_type);
  const status = mapBackendStatusToFrontend(d.status);

  return {
    id: d.id,
    title: d.filename,
    pages: d.page_count ?? 0,
    status,
    createdAt,
    pdfUrl: getDocumentDownloadUrl(d.id),
    author: d.source || '—',
    docType,
  };
}

export class DocumentsStore {
  documents: DocumentItem[] = [];
  loadingDocuments = false;
  uploading = false;
  error: string | null = null;
  private _lastLoadParams?: { backendDocumentType?: string };
  private _pollTimer: number | null = null;
  private _pollStartAtMs: number | null = null;

  constructor() {
    makeAutoObservable(this);
  }

  loadDocuments = async (params?: { backendDocumentType?: string }): Promise<void> => {
    this._lastLoadParams = params;
    this.loadingDocuments = true;
    this.error = null;
    try {
      const resp = await listDocuments({
        page: 1,
        size: 100,
        document_type: params?.backendDocumentType,
      });
      runInAction(() => {
        this.documents = resp.items.map(mapBackendDocToItem);
        this.loadingDocuments = false;
      });
    } catch (e) {
      runInAction(() => {
        this.error = e instanceof Error ? e.message : 'Failed to load documents';
        this.loadingDocuments = false;
      });
    }

    this._schedulePendingPolling();
  };

  uploadDocument = async (file: File, backendDocumentType: string): Promise<void> => {
    this.uploading = true;
    this.error = null;
    try {
      await uploadDocuments([file], backendDocumentType);
      await this.loadDocuments();
    } catch (e) {
      runInAction(() => {
        this.error = e instanceof Error ? e.message : 'Failed to upload document';
      });
      throw e;
    } finally {
      runInAction(() => {
        this.uploading = false;
      });
    }
  };

  deleteDocument = async (documentId: string): Promise<void> => {
    this.error = null;
    try {
      await deleteDocument(documentId);
      runInAction(() => {
        this.documents = this.documents.filter((doc) => doc.id !== documentId);
      });
      this._schedulePendingPolling();
    } catch (e) {
      runInAction(() => {
        this.error = e instanceof Error ? e.message : 'Failed to delete document';
      });
      throw e;
    }
  };

  private _schedulePendingPolling() {
    if (typeof window === 'undefined') return;

    // Stop polling after a reasonable amount of time to avoid infinite loops.
    const maxPollMs = 5 * 60 * 1000; // 5 minutes
    if (this._pollStartAtMs === null) this._pollStartAtMs = Date.now();
    if (this._pollStartAtMs !== null && Date.now() - this._pollStartAtMs > maxPollMs) {
      this._stopPendingPolling();
      return;
    }

    const hasPending = this.documents.some((d) => d.status === 'pending');
    if (!hasPending) {
      this._stopPendingPolling();
      return;
    }

    if (this._pollTimer !== null) return; // already scheduled

    this._pollTimer = window.setTimeout(async () => {
      this._pollTimer = null;
      // Use the last filter params we were loaded with.
      await this.loadDocuments(this._lastLoadParams);
    }, 2000);
  }

  private _stopPendingPolling() {
    if (this._pollTimer !== null) {
      window.clearTimeout(this._pollTimer);
      this._pollTimer = null;
    }
    this._pollStartAtMs = null;
  }
}

export const documentsStore = new DocumentsStore();

