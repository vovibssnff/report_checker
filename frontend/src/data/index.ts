import type { DocumentItem, DocumentItemJson } from '../types/document';
import { documentsFromJson } from '../types/document';
import documentsJson from './documents.json';

const documentsData = documentsJson as { documents: DocumentItemJson[] };

/** Список документов с датами, готовый для UI (из единого JSON) */
export const documentsList: DocumentItem[] = documentsFromJson(documentsData.documents);
