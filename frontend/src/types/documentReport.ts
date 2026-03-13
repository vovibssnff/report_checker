export type ReportCheckStatus = 'passed' | 'failed' | 'warning';

export interface ReportCheckItem {
  label: string;
  status: ReportCheckStatus;
  detail?: string;
}

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
