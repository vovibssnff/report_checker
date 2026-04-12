import React, { useState, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useTranslation } from 'react-i18next';
import { Check, FileText, X } from 'lucide-react';
import { Document, Page } from 'react-pdf';
import type { MarginIssue, RichDetail, TextHighlight } from '../../types/documentReport';

interface RichDetailViewProps {
  detail: RichDetail;
  onGoToPage?: (page: number) => void;
  tooltip?: string;
  highlights?: TextHighlight[];
  pdfHighlights?: TextHighlight[];
  onHighlightHover?: (highlights: TextHighlight[]) => void;
  onHighlightLeave?: () => void;
  pdfFile?: string | null;
}

type PageRange = { from: number; to: number };

function normalizeText(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .replace(/[.!,;:]+$/g, '');
}

function pickTooltip(tooltipText: string | undefined, groupDescription: string | undefined): string | undefined {
  if (!tooltipText) return undefined;
  if (!groupDescription) return tooltipText;
  return normalizeText(tooltipText) === normalizeText(groupDescription) ? undefined : tooltipText;
}

function groupPages(pages: number[]): PageRange[] {
  if (pages.length === 0) return [];
  const sorted = [...pages].sort((a, b) => a - b);
  const ranges: PageRange[] = [{ from: sorted[0], to: sorted[0] }];
  for (let i = 1; i < sorted.length; i++) {
    const last = ranges[ranges.length - 1];
    if (sorted[i] === last.to + 1) {
      last.to = sorted[i];
    } else {
      ranges.push({ from: sorted[i], to: sorted[i] });
    }
  }
  return ranges;
}

const PortalTooltip: React.FC<{ text: string; anchorRect: DOMRect; visible: boolean }> = ({ text, anchorRect, visible }) => {
  return createPortal(
    <div
      className="fixed pointer-events-none z-9999 flex justify-center"
      style={{
        left: anchorRect.left + anchorRect.width / 2,
        top: anchorRect.top,
        transform: 'translate(-50%, -100%)',
        paddingBottom: 6,
      }}
    >
      <div
        className={`px-2.5 py-1.5 rounded-[1rem] bg-white drop-shadow-xl text-black w-max text-xs whitespace-pre-line max-w-64 text-center transition-all duration-150 ${
          visible ? 'opacity-100 scale-100' : 'opacity-0 scale-95'
        }`}
      >
        {text}
      </div>
    </div>,
    document.body,
  );
};

const PageChip: React.FC<{
  range: PageRange;
  onClick?: (page: number) => void;
  tooltip?: string;
  className?: string;
  style?: React.CSSProperties;
  onHoverStart?: () => void;
  onHoverEnd?: () => void;
}> = ({ range, onClick, tooltip, className = '', style, onHoverStart, onHoverEnd }) => {
  const label = range.from === range.to ? `${range.from}` : `${range.from}–${range.to}`;
  const ref = useRef<HTMLButtonElement>(null);
  const [hovered, setHovered] = useState(false);
  const [rect, setRect] = useState<DOMRect | null>(null);

  const onEnter = useCallback(() => {
    onHoverStart?.();
    if (tooltip && ref.current) {
      setRect(ref.current.getBoundingClientRect());
      setHovered(true);
    }
  }, [tooltip, onHoverStart]);

  const onLeave = useCallback(() => {
    setHovered(false);
    onHoverEnd?.();
  }, [onHoverEnd]);

  return (
    <>
      <button
        ref={ref}
        type="button"
        onClick={onClick ? () => onClick(range.from) : undefined}
        onMouseEnter={onEnter}
        onMouseLeave={onLeave}
        style={style}
        className={`relative inline-flex items-center gap-1 px-2.5 py-1.5 w-max rounded-full text-xs font-medium tabular-nums transition-all border border-transparent ${
          onClick
            ? 'bg-[rgb(240,240,240)] hover:bg-[rgb(220,220,220)] hover:border-black/10 cursor-pointer'
            : 'bg-[rgb(240,240,240)] text-gray-600'
        } ${className}`}
      >
        <FileText className="size-3 opacity-70" />
        {label}
      </button>
      {tooltip && rect && <PortalTooltip text={tooltip} anchorRect={rect} visible={hovered} />}
    </>
  );
};

const CounterBar: React.FC<{ found: number; required: number; unit?: string }> = ({ found, required }) => {
  const { t } = useTranslation();
  const ratio = required > 0 ? Math.min(found / required, 1) : 0;
  const isMet = found >= required;

  return (
    <div className="flex items-center gap-3 w-full">
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${isMet ? 'bg-emerald-500' : 'bg-amber-500'}`}
          style={{ width: `${ratio * 100}%` }}
        />
      </div>
      <span className="text-xs tabular-nums text-gray-500 shrink-0">
        <span className={isMet ? 'text-emerald-600 font-semibold' : 'text-amber-600 font-semibold'}>{found}</span>
        {' '}{t('report.richDetail.of')}{' '}{required}
      </span>
    </div>
  );
};

type BadgeVariant = 'red' | 'green';
const badgeStyles: Record<BadgeVariant, string> = {
  red: 'bg-red-50 text-red-700 border-red-100',
  green: 'bg-emerald-50 text-emerald-700 border-emerald-100',
};

interface BadgeItem {
  label: string;
  variant?: BadgeVariant;
  mono?: boolean;
}

function capitalizeFirst(value: string): string {
  if (!value) return value;
  return value.charAt(0).toUpperCase() + value.slice(1);
}

const badgeStateIcon: Record<BadgeVariant, React.ReactNode> = {
  red: <X className="size-3.5" />,
  green: <Check className="size-3.5" />,
};

const BadgeList: React.FC<{ items: BadgeItem[]; separator?: React.ReactNode }> = ({ items, separator }) => (
  <div className="flex flex-wrap items-center gap-1.75">
    {items.map((item, i) => (
      <React.Fragment key={i}>
        {separator && i > 0 && <span className="text-gray-400 text-xs">{separator}</span>}
        {(() => {
          const variant = item.variant ?? 'red';
          return (
        <span
          className={`inline-flex items-center px-2.5 pl-2 py-1 rounded-full -ml-0.5 text-xs border tabular-nums ${
            item.mono ? 'font-mono' : ''
          } ${badgeStyles[variant]}`}
        >
          <span className="mr-1 leading-none">{badgeStateIcon[variant]}</span>
          {capitalizeFirst(item.label)}
        </span>
          );
        })()}
      </React.Fragment>
    ))}
  </div>
);

type MarginRangeGroup = { range: PageRange; issues: MarginIssue[] };

function buildMarginRanges(violations: { page: number; issues: MarginIssue[] }[]): MarginRangeGroup[] {
  if (violations.length === 0) return [];
  const sorted = [...violations].sort((a, b) => a.page - b.page);
  const issueKey = (issues: MarginIssue[]) =>
    [...issues].sort((a, b) => a.side.localeCompare(b.side)).map((i) => `${i.side}:${i.value_mm}`).join('\n');

  const result: MarginRangeGroup[] = [];
  let cur: MarginRangeGroup = {
    range: { from: sorted[0].page, to: sorted[0].page },
    issues: sorted[0].issues,
  };
  for (let i = 1; i < sorted.length; i++) {
    const v = sorted[i];
    if (v.page === cur.range.to + 1 && issueKey(v.issues) === issueKey(cur.issues)) {
      cur.range.to = v.page;
    } else {
      result.push(cur);
      cur = { range: { from: v.page, to: v.page }, issues: v.issues };
    }
  }
  result.push(cur);
  return result;
}

const STACK_OFFSET_REM = 1.55;

function highlightsForRange(
  highlights: TextHighlight[] | undefined,
  range: PageRange,
): TextHighlight[] {
  if (!highlights || highlights.length === 0) return [];
  return highlights.filter((h) => h.page >= range.from && h.page <= range.to);
}

type MarginSide = 'left' | 'right' | 'top' | 'bottom';
const VALID_SIDES = new Set<string>(['left', 'right', 'top', 'bottom']);

function parseMarginIssues(issues: MarginIssue[]): { side: MarginSide; value: string }[] {
  return issues
    .filter((i) => VALID_SIDES.has(i.side))
    .map((i) => ({ side: i.side as MarginSide, value: `${i.value_mm}mm` }));
}

const THUMB_W = 96;
const THUMB_H = Math.round(THUMB_W * (297 / 210));

const MarginDiagram: React.FC<{
  margins: { side: MarginSide; value: string }[];
  pdfFile?: string | null;
  pageNumber: number;
}> = ({ margins, pdfFile, pageNumber }) => {
  const sides = new Set(margins.map((m) => m.side));
  const byName = Object.fromEntries(margins.map((m) => [m.side, m.value])) as Partial<Record<MarginSide, string>>;

  const BAD = 'rgba(239, 68, 68, 0.18)';
  const BORDER_BAD = 'rgba(239, 68, 68, 0.55)';

  return (
    <div
      className="relative rounded-[12px] superellipse overflow-hidden bg-white"
      style={{ width: THUMB_W, height: THUMB_H }}
    >
      {pdfFile && (
        <Document file={pdfFile} loading={null} error={null} className="absolute inset-0 opacity-50">
          <Page
            pageNumber={pageNumber}
            width={THUMB_W}
            renderTextLayer={false}
            renderAnnotationLayer={false}
            loading={null}
          />
        </Document>
      )}

      {/* top margin */}
      {sides.has('top') && (
        <div
          className="absolute superellipse left-1 right-1 top-1 flex items-center justify-center"
          style={{
            height: '22%',
            backgroundColor: BAD,
            borderRadius: '6px',
            border: `1px solid ${BORDER_BAD}`,
          }}
        >
          <span className="text-red-600 font-medium leading-none text-xs">{byName.top}</span>
        </div>
      )}

      {/* bottom margin */}
      {sides.has('bottom') && (
        <div
          className="absolute superellipse left-1 right-1 bottom-1 flex items-center justify-center"
          style={{
            height: '16%',
            backgroundColor: BAD,
            borderRadius: '6px',
            border: `1px solid ${BORDER_BAD}`,
          }}
        >
          <span className="text-red-600 font-medium leading-none text-xs">{byName.bottom}</span>
        </div>
      )}

      {/* left margin */}
      {sides.has('left') && (
        <div
          className="absolute superellipse left-1 bottom-1 flex items-center justify-center"
          style={{
            width: '25%',
            top: sides.has('top') ? 'calc(22% + 8px)' : '4px',
            bottom: sides.has('bottom') ? 'calc(16% + 8px)' : '4px',
            backgroundColor: BAD,
            borderRadius: '6px',
            border: `1px solid ${BORDER_BAD}`,
          }}
        >
          <span
            className="text-red-600 font-medium leading-none text-xs"
            style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
          >
            {byName.left}
          </span>
        </div>
      )}

      {/* right margin */}
      {sides.has('right') && (
        <div
          className="absolute superellipse right-1 flex items-center justify-center"
          style={{
            width: '25%',
            top: sides.has('top') ? 'calc(22% + 8px)' : '4px',
            bottom: sides.has('bottom') ? 'calc(16% + 8px)' : '4px',
            backgroundColor: BAD,
            borderRadius: '6px',
            border: `1px solid ${BORDER_BAD}`,
          }}
        >
          <span
            className="text-red-600 font-medium leading-none text-xs"
            style={{ writingMode: 'vertical-rl' }}
          >
            {byName.right}
          </span>
        </div>
      )}
    </div>
  );
};

const MarginsDetail: React.FC<{
  violations: { page: number; issues: MarginIssue[] }[];
  onGoToPage?: (page: number) => void;
  highlights?: TextHighlight[];
  onHighlightHover?: (highlights: TextHighlight[]) => void;
  onHighlightLeave?: () => void;
  pdfFile?: string | null;
}> = ({ violations, onGoToPage, highlights, onHighlightHover, onHighlightLeave, pdfFile }) => {
  const groups = buildMarginRanges(violations);
  return (
    <div className="flex flex-wrap items-start gap-3">
      {groups.map((g) => {
        const margins = parseMarginIssues(g.issues);
        const rangeHL = highlightsForRange(highlights, g.range);
        const label = g.range.from === g.range.to ? `${g.range.from}` : `${g.range.from}–${g.range.to}`;
        return (
          <button
            key={`${g.range.from}-${g.range.to}`}
            type="button"
            className="flex flex-col items-center gap-1 cursor-pointer group"
            onClick={onGoToPage ? () => onGoToPage(g.range.from) : undefined}
            onMouseEnter={() => onHighlightHover?.(rangeHL)}
            onMouseLeave={onHighlightLeave}
          >
            <div className="rounded-md overflow-hidden drop-shadow-xl">
              <MarginDiagram margins={margins} pdfFile={pdfFile} pageNumber={g.range.from} />
            </div>
            <span className="text-xs text-gray-500 tabular-nums group-hover:text-gray-900 transition-colors">{label}</span>
          </button>
        );
      })}
    </div>
  );
};

const RichDetailView: React.FC<RichDetailViewProps> = ({ detail, onGoToPage, tooltip, highlights, pdfHighlights, onHighlightHover, onHighlightLeave, pdfFile }) => {
  const { t } = useTranslation();
  switch (detail.type) {
    case 'pages': {
      if (highlights && highlights.length > 0) {
        type Chip = { page: number; tooltip: string; hl: TextHighlight };
        const chips: Chip[] = highlights.map((h) => ({
          page: h.page,
          tooltip: h.message,
          hl: h,
        }));

        // Group by page, sorted
        const byPage = new Map<number, Chip[]>();
        for (const c of chips) {
          if (!byPage.has(c.page)) byPage.set(c.page, []);
          byPage.get(c.page)!.push(c);
        }
        // Also include pages without highlights
        for (const p of detail.pages) {
          if (!byPage.has(p)) byPage.set(p, []);
        }
        const sortedPages = [...byPage.keys()].sort((a, b) => a - b);

        return (
          <div className="flex flex-wrap items-center gap-1.75">
            {sortedPages.map((page) => {
              const group = byPage.get(page)!;
              const range: PageRange = { from: page, to: page };
              const n = group.length;

              if (n <= 1) {
                const singleHL = group[0]?.hl ? [group[0].hl] : [];
                return (
                  <PageChip
                    key={page}
                    range={range}
                    onClick={onGoToPage}
                    tooltip={group[0]?.tooltip}
                    onHoverStart={singleHL.length > 0 ? () => onHighlightHover?.(singleHL) : undefined}
                    onHoverEnd={singleHL.length > 0 ? onHighlightLeave : undefined}
                  />
                );
              }

              return (
                <div
                  key={page}
                  className="relative inline-flex items-center"
                  style={{ marginRight: `${(n - 1) * STACK_OFFSET_REM + 0.5}rem` }}
                >
                  {group.map((chip, idx) => {
                    const isTop = idx === n - 1;
                    const chipHL = chip.hl ? [chip.hl] : [];
                    return (
                      <PageChip
                        key={idx}
                        range={range}
                        onClick={onGoToPage}
                        tooltip={chip.tooltip}
                        onHoverStart={chipHL.length > 0 ? () => onHighlightHover?.(chipHL) : undefined}
                        onHoverEnd={chipHL.length > 0 ? onHighlightLeave : undefined}
                        style={{
                          position: idx === 0 ? 'relative' : 'absolute',
                          left: `${idx * STACK_OFFSET_REM}rem`,
                          top: 0,
                          zIndex: idx + 1,
                          outline: idx > 0 ? '3px solid white' : undefined,
                          ...(!isTop && { paddingLeft: '0.45rem', paddingRight: '0.45rem' }),
                        }}
                      />
                    );
                  })}
                </div>
              );
            })}
          </div>
        );
      }

      const allHL = pdfHighlights ?? highlights;
      const ranges = groupPages(detail.pages);
      const pageTooltip = pickTooltip(tooltip, tooltip);
      return (
        <div className="flex flex-wrap gap-1.5">
          {ranges.map((r) => {
            const rangeHL = highlightsForRange(allHL, r);
            return (
              <PageChip
                key={`${r.from}-${r.to}`}
                range={r}
                onClick={onGoToPage}
                tooltip={pageTooltip}
                onHoverStart={rangeHL.length > 0 ? () => onHighlightHover?.(rangeHL) : undefined}
                onHoverEnd={rangeHL.length > 0 ? onHighlightLeave : undefined}
              />
            );
          })}
        </div>
      );
    }

    case 'font':
      return (
        <BadgeList
          items={[
            { label: detail.dominant, variant: 'red', mono: true },
            { label: `${detail.expected}`, variant: 'green', mono: true },
          ]}
          separator={<>&rarr;</>}
        />
      );

    case 'counter':
      return <CounterBar found={detail.found} required={detail.required} unit={detail.unit} />;

    case 'sections':
      return <BadgeList items={detail.missing.map((s) => ({ label: s }))} />;

    case 'stages':
      return <BadgeList items={detail.missing.map((s) => ({ label: `${t('report.richDetail.stage')} ${s}` }))} />;

    case 'margins':
      return <MarginsDetail violations={detail.violations} onGoToPage={onGoToPage} highlights={pdfHighlights ?? highlights} onHighlightHover={onHighlightHover} onHighlightLeave={onHighlightLeave} pdfFile={pdfFile} />;

    case 'bullets':
      return (
        <ul className="list-disc pl-4 text-xs text-gray-600 space-y-1 max-w-md">
          {detail.items.map((line, i) => (
            <li key={i}>{line}</li>
          ))}
        </ul>
      );

    default:
      return null;
  }
};

export default RichDetailView;
