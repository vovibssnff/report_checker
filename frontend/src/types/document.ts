import type { DocumentReport } from './documentReport';

/** Статус проверки документа */
export type DocumentStatus = 'failed' | 'passed' | 'warnings' | 'pending';

/** Тип документа (уровень образования) */
export type DocType = 'masters' | 'bachelors';

/** Документ для отображения в списке и модалке (с датой как объект Date) */
export interface DocumentItem {
  id?: string;
  title: string;
  pages: number;
  status: DocumentStatus;
  createdAt: Date;
  pdfUrl?: string;
  author: string;
  docType: DocType;
  report?: DocumentReport;
}

/** Документ в формате JSON (createdAt — строка ISO для хранения/API) */
export interface DocumentItemJson {
  id?: string;
  title: string;
  pages: number;
  status: DocumentStatus;
  createdAt: string;
  pdfUrl?: string;
  author: string;
  docType: DocType;
  report?: DocumentReport;
}

export function documentFromJson(item: DocumentItemJson): DocumentItem {
  return {
    ...item,
    createdAt: new Date(item.createdAt),
  };
}

export function documentsFromJson(items: DocumentItemJson[]): DocumentItem[] {
  return items.map(documentFromJson);
}
