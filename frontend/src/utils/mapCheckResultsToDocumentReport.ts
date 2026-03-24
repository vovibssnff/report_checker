import type { BackendCheckResultResponse, BackendDocumentDetailResponse } from '../api/documentApi';
import type { DocumentReport, ReportCheckItem, ReportCheckStatus, ReportSection } from '../types/documentReport';

function mapCheckStatus(cr: BackendCheckResultResponse): ReportCheckStatus {
  if (cr.status === 'passed') return 'passed';
  if (cr.status === 'failed' && cr.severity === 'warning') return 'warning';
  return 'failed';
}

function humanizeRuleCode(ruleCode: string): string {
  // Keep it readable for UI without requiring a perfect translation mapping.
  return ruleCode
    .replace(/^vkr\./, '')
    .replace(/\./g, ' ')
    .replace(/_/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function mapRuleToSection(ruleCode: string): 'structure' | 'formatting' | 'content' {
  if (ruleCode.startsWith('vkr.structure.') || ruleCode.startsWith('vkr.headings.')) return 'structure';
  if (ruleCode.startsWith('vkr.formatting.')) return 'formatting';
  return 'content';
}

function buildSection(title: string, checkResults: BackendCheckResultResponse[]): ReportSection {
  const items: ReportCheckItem[] = checkResults.map((cr) => ({
    label: humanizeRuleCode(cr.rule_code),
    status: mapCheckStatus(cr),
    detail: cr.message,
  }));

  const passed = items.filter((i) => i.status === 'passed').length;
  const total = items.length;

  return { title, passed, total, items };
}

export function mapCheckResultsToDocumentReport(detail: BackendDocumentDetailResponse): DocumentReport {
  const checkDate =
    detail.checked_at ??
    detail.check_results[0]?.created_at ??
    new Date().toISOString();

  const structure: BackendCheckResultResponse[] = [];
  const formatting: BackendCheckResultResponse[] = [];
  const content: BackendCheckResultResponse[] = [];

  for (const cr of detail.check_results) {
    const section = mapRuleToSection(cr.rule_code);
    if (section === 'structure') structure.push(cr);
    else if (section === 'formatting') formatting.push(cr);
    else content.push(cr);
  }

  const structureSection = buildSection('report.structure', structure);
  const formattingSection = buildSection('report.formatting', formatting);
  const contentSection = buildSection('report.content', content);

  const totalChecks = detail.check_results.length;
  const totalPassed = detail.check_results.filter((cr) => mapCheckStatus(cr) === 'passed').length;

  const overallStatus =
    totalPassed === totalChecks ? 'report.noWarnings' : 'report.statusRequiresRefinement';

  return {
    checkDate,
    structure: structureSection,
    formatting: formattingSection,
    content: contentSection,
    totalPassed,
    totalChecks,
    overallStatus,
  };
}

