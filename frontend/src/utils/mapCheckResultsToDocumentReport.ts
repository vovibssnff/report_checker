import i18n from '../i18n';
import type { BackendCheckResultResponse, BackendDocumentDetailResponse } from '../api/documentApi';
import type { DocumentReport, MarginIssue, ReportCheckItem, ReportCheckStatus, ReportSection, RichDetail, TextHighlight } from '../types/documentReport';

const t = (key: string, params?: Record<string, unknown>) => i18n.t(key, params ?? {});

function mapCheckStatus(cr: BackendCheckResultResponse): ReportCheckStatus {
  if (cr.status === 'passed') return 'passed';
  if (cr.status === 'failed' && cr.severity === 'warning') return 'warning';
  return 'failed';
}

function getRuleLabelKey(cr: BackendCheckResultResponse): string {
  if (cr.rule_code === 'vkr.formatting.font' || cr.rule_code === 'practice.formatting.font') {
    const prefix = cr.rule_code.startsWith('practice') ? 'practice' : 'vkr';
    if (cr.message === 'font_size_small') {
      return `report.ruleLabels.${prefix}.formatting.font_size`;
    }
    return `report.ruleLabels.${prefix}.formatting.font_family`;
  }

  if (cr.rule_code.startsWith('vkr.') || cr.rule_code.startsWith('practice.')) {
    return `report.ruleLabels.${cr.rule_code}`;
  }

  return cr.rule_code;
}

function mapRuleToSection(ruleCode: string): 'structure' | 'formatting' | 'content' {
  if (ruleCode.startsWith('vkr.structure.') || ruleCode.startsWith('vkr.headings.')) return 'structure';
  if (ruleCode.startsWith('vkr.formatting.')) return 'formatting';
  if (ruleCode.startsWith('practice.structure.')) return 'structure';
  if (ruleCode.startsWith('practice.formatting.')) return 'formatting';
  if (ruleCode.startsWith('practice.content.')) return 'content';
  return 'content';
}

function translateMessage(cr: BackendCheckResultResponse): string {
  const d = cr.details ?? {};
  const params: Record<string, unknown> = {};

  if (d.dominant_font) params.dominant = d.dominant_font;
  if (d.expected) params.expected = d.expected;
  if (d.min_size != null) params.min_size = d.min_size;
  if (typeof d.expected === 'number') params.expected = d.expected;
  if (d.count != null) params.count = d.count;
  if (d.page_count != null) params.page_count = d.page_count;
  if (d.min_pages != null) params.min_pages = d.min_pages;
  if (d.found != null) params.found = d.found;
  if (d.required != null) params.required = d.required;

  const key = `report.messages.${cr.message}`;
  const translated = t(key, params);
  return translated !== key ? translated : cr.message;
}

function translateIssue(issue: string | Record<string, unknown>): string {
  if (typeof issue === 'string') {
    const key = `report.issues.${issue}`;
    const translated = t(key);
    return translated !== key ? translated : issue;
  }
  if (typeof issue === 'object' && issue !== null && 'type' in issue) {
    const issueType = issue.type as string;
    const key = `report.issues.${issueType}`;
    const translated = t(key, issue as Record<string, unknown>);
    return translated !== key ? translated : JSON.stringify(issue);
  }
  return String(issue);
}

function translateSection(code: string): string {
  const key = `report.sections.${code}`;
  const translated = t(key);
  return translated !== key ? translated : code;
}

const MARGIN_SIDE_MAP: Record<string, string> = {
  левое: 'left', правое: 'right', верхнее: 'top', нижнее: 'bottom',
  left: 'left', right: 'right', top: 'top', bottom: 'bottom',
};

function normalizeMarginIssue(raw: unknown): MarginIssue {
  if (typeof raw === 'object' && raw !== null && 'side' in raw && 'value_mm' in raw) {
    return raw as MarginIssue;
  }
  if (typeof raw === 'string') {
    const m = raw.match(/^(левое|правое|верхнее|нижнее|left|right|top|bottom)\s+([\d.]+)/i);
    if (m) {
      return { side: MARGIN_SIDE_MAP[m[1].toLowerCase()] ?? m[1], value_mm: parseFloat(m[2]) };
    }
  }
  return { side: 'left', value_mm: 0 };
}

function extractRichDetail(cr: BackendCheckResultResponse): RichDetail | undefined {
  const d = cr.details;
  if (!d) return undefined;

  if ('dominant_font' in d && typeof d.dominant_font === 'string') {
    const expected = (d.expected as string) || 'Times New Roman';
    return { type: 'font', dominant: d.dominant_font as string, expected };
  }

  if ('page_count' in d && 'min_pages' in d) {
    return { type: 'counter', found: d.page_count as number, required: d.min_pages as number, unit: 'pages' };
  }

  if ('found' in d && 'required' in d) {
    return { type: 'counter', found: d.found as number, required: d.required as number, unit: 'images' };
  }

  if ('missing_sections' in d && Array.isArray(d.missing_sections)) {
    const translated = (d.missing_sections as string[]).map(translateSection);
    return { type: 'sections', missing: translated };
  }

  if ('missing_stages' in d && Array.isArray(d.missing_stages)) {
    return { type: 'stages', missing: d.missing_stages as number[] };
  }

  if ('order_violations' in d && Array.isArray(d.order_violations)) {
    const ov = d.order_violations as { before: string; after: string }[];
    const items = ov.map((o) =>
      t('report.issues.section_wrong_order_pdf', {
        earlier: translateSection(o.before),
        later: translateSection(o.after),
      }),
    );
    return { type: 'bullets', items };
  }

  if ('issues' in d && Array.isArray(d.issues) && cr.message === 'toc_invalid') {
    const items = (d.issues as string[]).map((issue) => translateIssue(issue));
    return { type: 'bullets', items };
  }

  if ('violations' in d && Array.isArray(d.violations) && (cr.rule_code.includes('.margins') || cr.rule_code.includes('.formatting.margins'))) {
    const violations = (d.violations as { page: number; issues: unknown[] }[]).map((v) => ({
      page: v.page,
      issues: (v.issues ?? []).map(normalizeMarginIssue),
    }));
    return { type: 'margins', violations };
  }

  if ('pages' in d && Array.isArray(d.pages)) {
    return { type: 'pages', pages: d.pages as number[] };
  }

  if ('violations' in d && Array.isArray(d.violations)) {
    const pages = [...new Set((d.violations as { page: number }[]).map((v) => v.page))].sort((a, b) => a - b);
    if (pages.length > 0) return { type: 'pages', pages };
  }

  return undefined;
}

interface LocationEntry {
  page: number;
  text?: string;
  font_size?: number;
  issues?: (string | Record<string, unknown>)[];
  location: { x0: number; y0: number; x1: number; y1: number };
}

function pushLocations(
  arr: LocationEntry[],
  message: string,
  out: TextHighlight[],
  messageFn?: (entry: LocationEntry) => string,
) {
  for (const entry of arr) {
    if (!entry.location) continue;
    const loc = entry.location;
    out.push({
      page: entry.page,
      x0: loc.x0,
      y0: loc.y0,
      x1: loc.x1,
      y1: loc.y1,
      message: messageFn ? messageFn(entry) : message,
    });
  }
}

function extractHighlights(cr: BackendCheckResultResponse): TextHighlight[] | undefined {
  const d = cr.details;
  if (!d) return undefined;

  const highlights: TextHighlight[] = [];
  const msg = translateMessage(cr);

  if (Array.isArray(d.bad_captions)) {
    pushLocations(d.bad_captions as LocationEntry[], msg, highlights);
  }

  if (Array.isArray(d.locations)) {
    pushLocations(d.locations as LocationEntry[], msg, highlights, (entry) => {
      if (entry.font_size != null) return t('report.messages.font_size_tooltip', { size: entry.font_size });
      return msg;
    });
  }

  if (Array.isArray(d.violations)) {
    const withLoc = (d.violations as LocationEntry[]).filter((v) => v.location);
    pushLocations(withLoc, msg, highlights, (entry) => {
      if (entry.issues && entry.issues.length > 0) {
        return entry.issues.map(translateIssue).join('\n');
      }
      return msg;
    });
  }

  return highlights.length > 0 ? highlights : undefined;
}

function extractChipHighlights(cr: BackendCheckResultResponse): TextHighlight[] | undefined {
  const d = cr.details;
  if (!d) return undefined;

  const highlights: TextHighlight[] = [];
  const msg = translateMessage(cr);

  if (Array.isArray(d.bad_captions)) {
    for (const entry of d.bad_captions as LocationEntry[]) {
      if (!entry.location) continue;
      highlights.push({
        page: entry.page,
        x0: entry.location.x0, y0: entry.location.y0,
        x1: entry.location.x1, y1: entry.location.y1,
        message: entry.text ?? msg,
      });
    }
  }

  if (Array.isArray(d.violations)) {
    for (const entry of d.violations as LocationEntry[]) {
      if (!entry.location) continue;
      highlights.push({
        page: entry.page,
        x0: entry.location.x0, y0: entry.location.y0,
        x1: entry.location.x1, y1: entry.location.y1,
        message: entry.issues ? entry.issues.map(translateIssue).join('\n') : (entry.text ?? msg),
      });
    }
  }

  return highlights.length > 0 ? highlights : undefined;
}

function buildSection(title: string, checkResults: BackendCheckResultResponse[]): ReportSection {
  const items: ReportCheckItem[] = checkResults.map((cr) => ({
    label: getRuleLabelKey(cr),
    status: mapCheckStatus(cr),
    detail: translateMessage(cr),
    richDetail: extractRichDetail(cr),
    highlights: extractHighlights(cr),
    chipHighlights: extractChipHighlights(cr),
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
