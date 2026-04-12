export type ReportCheckStatus = 'passed' | 'failed' | 'warning';

export interface TextHighlight {
  page: number;
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  message: string;
}

export interface MarginIssue {
  side: string;
  value_mm: number;
}

export interface ReportCheckItem {
  label: string;
  status: ReportCheckStatus;
  detail?: string;
  detailParams?: Record<string, string | number>;
  richDetail?: RichDetail;
  highlights?: TextHighlight[];
  chipHighlights?: TextHighlight[];
}

export type RichDetail =
  | { type: 'pages'; pages: number[] }
  | { type: 'font'; dominant: string; expected: string }
  | { type: 'counter'; found: number; required: number; unit?: string }
  | { type: 'sections'; missing: string[] }
  | { type: 'stages'; missing: number[] }
  | { type: 'margins'; violations: { page: number; issues: MarginIssue[] }[] }
  | { type: 'bullets'; items: string[] };

export interface ReportSection {
  title: string;
  passed: number;
  total: number;
  items: ReportCheckItem[];
}

export interface DocumentReport {
  checkDate: string;
  structure: ReportSection;
  formatting: ReportSection;
  content: ReportSection;
  totalPassed: number;
  totalChecks: number;
  overallStatus: string;
}
