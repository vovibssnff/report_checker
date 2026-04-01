import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { X, CheckCircle2, XCircle, AlertCircle, Loader2 } from 'lucide-react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/TextLayer.css';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import type { DocumentReport, ReportCheckStatus, TextHighlight } from '../../types/documentReport';
import { getDocument } from '../../api/documentApi';
import { Spinner } from '../ui/spinner';
import { mapCheckResultsToDocumentReport } from '../../utils/mapCheckResultsToDocumentReport';
import RichDetailView from './RichDetailView';

pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

type ItemStatus = 'failed' | 'passed' | 'warnings' | 'pending';

const statusKeys: Record<ItemStatus, { labelKey: string }> = {
  pending: { labelKey: 'documents.statusPending' },
  failed: { labelKey: 'documents.statusFailed' },
  passed: { labelKey: 'documents.statusPassed' },
  warnings: { labelKey: 'documents.statusWarnings' },
};

const ReportIcon: React.FC<{ status: ReportCheckStatus }> = ({ status }) => {
  if (status === 'passed') {
    return <span className="text-green-600 font-bold">✓</span>;
  }
  if (status === 'failed') {
    return <span className="text-red-600 font-bold">✗</span>;
  }
  return <span className="text-amber-500 font-bold">⚠</span>;
};

const statusCardConfig: Record<ItemStatus, { icon: React.ComponentType<{ className?: string }>; bgClass: string; iconClass: string }> = {
  passed: {
    icon: CheckCircle2,
    bgClass: 'bg-emerald-500/10',
    iconClass: 'text-emerald-600',
  },
  failed: {
    icon: XCircle,
    bgClass: 'bg-red-500/10',
    iconClass: 'text-red-600',
  },
  warnings: {
    icon: AlertCircle,
    bgClass: 'bg-amber-500/10',
    iconClass: 'text-amber-600',
  },
  pending: {
    icon: Loader2,
    bgClass: 'bg-slate-400/10',
    iconClass: 'text-slate-500',
  },
};

import type { RichDetail } from '../../types/documentReport';

const HighlightTooltip: React.FC<{ text: string; anchorRect: DOMRect; visible: boolean }> = ({ text, anchorRect, visible }) =>
  createPortal(
    <div
      className="fixed pointer-events-none z-9999 flex justify-center"
      style={{
        left: anchorRect.left + anchorRect.width / 2,
        top: anchorRect.top,
        transform: 'translate(-50%, -100%)',
        paddingBottom: 4,
      }}
    >
      <div
        className={`px-2.5 py-1.5 rounded-lg bg-white drop-shadow-xl text-black text-xs whitespace-pre-line max-w-64 text-center transition-all duration-150 ${
          visible ? 'opacity-100 scale-100' : 'opacity-0 scale-95'
        }`}
      >
        {text}
      </div>
    </div>,
    document.body,
  );

function hlKey(h: TextHighlight): string {
  return `${h.page}:${h.x0}:${h.y0}:${h.x1}:${h.y1}`;
}

interface MergedHighlight {
  page: number;
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  messages: string[];
  keys: string[];
}

const HighlightRect: React.FC<{
  h: MergedHighlight;
  scale: number;
  emphasized?: boolean;
}> = ({ h, scale, emphasized }) => {
  const ref = useRef<HTMLDivElement>(null);
  const [hovered, setHovered] = useState(false);
  const [rect, setRect] = useState<DOMRect | null>(null);

  const onEnter = useCallback(() => {
    if (ref.current) setRect(ref.current.getBoundingClientRect());
    setHovered(true);
  }, []);
  const onLeave = useCallback(() => setHovered(false), []);

  const active = hovered || emphasized;
  const PAD = 2;
  const style: React.CSSProperties = {
    position: 'absolute',
    left: h.x0 * scale - PAD,
    top: h.y0 * scale - PAD,
    width: (h.x1 - h.x0) * scale + PAD * 2,
    height: (h.y1 - h.y0) * scale + PAD * 2,
    borderRadius: 4,
    cursor: 'default',
    transition: 'background-color 150ms, box-shadow 150ms',
    backgroundColor: active ? 'rgba(239, 68, 68, 0.25)' : 'rgba(239, 68, 68, 0.14)',
    boxShadow: active ? '0 0 0 2px rgba(239, 68, 68, 0.4)' : 'none',
  };

  const tooltipText = h.messages.join('\n');

  return (
    <>
      <div
        ref={ref}
        style={style}
        onMouseEnter={onEnter}
        onMouseLeave={onLeave}
      />
      {rect && <HighlightTooltip text={tooltipText} anchorRect={rect} visible={hovered} />}
    </>
  );
};

function mergeHighlightsByPosition(highlights: TextHighlight[]): MergedHighlight[] {
  const map = new Map<string, MergedHighlight>();
  for (const h of highlights) {
    const posKey = `${h.x0}:${h.y0}:${h.x1}:${h.y1}`;
    const existing = map.get(posKey);
    if (existing) {
      if (!existing.messages.includes(h.message)) {
        existing.messages.push(h.message);
      }
      const hk = hlKey(h);
      if (!existing.keys.includes(hk)) {
        existing.keys.push(hk);
      }
    } else {
      map.set(posKey, {
        page: h.page,
        x0: h.x0,
        y0: h.y0,
        x1: h.x1,
        y1: h.y1,
        messages: [h.message],
        keys: [hlKey(h)],
      });
    }
  }
  return [...map.values()];
}

const HighlightOverlay: React.FC<{
  highlights: TextHighlight[];
  page: number;
  scale: number;
  activeKeys?: Set<string>;
}> = ({ highlights, page, scale, activeKeys }) => {
  const merged = useMemo(
    () => mergeHighlightsByPosition(highlights.filter((h) => h.page === page)),
    [highlights, page],
  );
  if (merged.length === 0) return null;
  return (
    <div className="absolute inset-0 z-5 pointer-events-none">
      <div className="relative size-full pointer-events-auto">
        {merged.map((h, i) => (
          <HighlightRect
            key={`${h.keys[0]}-${i}`}
            h={h}
            scale={scale}
            emphasized={activeKeys ? h.keys.some((k) => activeKeys.has(k)) : false}
          />
        ))}
      </div>
    </div>
  );
};

function stripRedundantTail(text: string, rich: RichDetail | undefined): string {
  if (!rich) return text;

  switch (rich.type) {
    case 'font': {
      const c = text
        .replace(/[«»'"]/g, '')
        .replace(/\s+(вместо|instead of)\s+/i, ' ')
        .replace(/\s{2,}/g, ' ');
      return c.trim() || text;
    }
    case 'counter': {
      const c = text.replace(/\(\d+\)/g, '').replace(/\s{2,}/g, ' ');
      return c.trim() || text;
    }
    default:
      return text;
  }
}

/** Парсит дату из "YYYY-MM-DD HH:mm:ss" или ISO и форматирует через Intl */
function formatCheckDateAndTime(raw: string, locale: string): string {
  const iso = raw.includes('T') ? raw : raw.replace(' ', 'T');
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return raw;
  const lang = locale.startsWith('ru') ? 'ru-RU' : locale.startsWith('en') ? 'en-GB' : locale;
  const dateStr = new Intl.DateTimeFormat(lang, { day: 'numeric', month: 'long', year: 'numeric' }).format(date);
  const timeStr = new Intl.DateTimeFormat(lang, { hour: '2-digit', minute: '2-digit' }).format(date);
  return `${dateStr}, ${timeStr}`;
}

export interface DocumentDetailModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  typeLabel: string;
  pages: number;
  status: ItemStatus;
  author?: string;
  pdfUrl?: string;
  documentId?: string;
  report?: DocumentReport;
  transitionStartRect?: { left: number; top: number; width: number; height: number } | null;
  transitionPreviewImage?: string | null;  /** Вызов по окончании анимации перехода */
  onTransitionComplete?: () => void;
}

type Rect = { left: number; top: number; width: number; height: number };

const DocumentDetailModal: React.FC<DocumentDetailModalProps> = (props) => {
  const { t, i18n } = useTranslation();
  const containerRef = useRef<HTMLDivElement>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [numPages, setNumPages] = useState(0);
  const [containerWidth, setContainerWidth] = useState(360);
  const [targetRect, setTargetRect] = useState<Rect | null>(null);
  const [revealPreviewBeforeUnmount, setRevealPreviewBeforeUnmount] = useState(false);

  const savedStartRectRef = useRef<Rect | null>(null);
  const [closingPhase, setClosingPhase] = useState(false);
  const [closeAnimData, setCloseAnimData] = useState<{ fromRect: Rect; toRect: Rect; image: string } | null>(null);
  const [previewTopPad, setPreviewTopPad] = useState(24);
  const [pdfPageWidthPt, setPdfPageWidthPt] = useState(595);
  const [activeHighlights, setActiveHighlights] = useState<TextHighlight[]>([]);

  const handleHighlightHover = useCallback((hl: TextHighlight[]) => setActiveHighlights(hl), []);
  const handleHighlightLeave = useCallback(() => setActiveHighlights([]), []);

  const source = props.pdfUrl;
  const hasPdf = Boolean(source);
  const isTransitioning = Boolean(props.transitionStartRect && props.transitionPreviewImage);
  const fileUrl = source
    ? source.startsWith('http')
      ? source
      : `${window.location.origin}${source.startsWith('/') ? '' : '/'}${source}`
    : null;
  const [pdfObjectUrl, setPdfObjectUrl] = useState<string | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);
  const [computedReport, setComputedReport] = useState<DocumentReport | undefined>(props.report);

  useEffect(() => {
    if (props.transitionStartRect) {
      savedStartRectRef.current = { ...props.transitionStartRect };
    }
  }, [props.transitionStartRect]);

  useEffect(() => {
    if (!props.open || !containerRef.current || !hasPdf) return;
    const el = containerRef.current;
    const measure = () => {
      const w = el.getBoundingClientRect().width;
      if (w > 0) setContainerWidth(w);
      const top = el.getBoundingClientRect().top;
      if (top > 0) setPreviewTopPad(top - 24);
    };
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    window.addEventListener('resize', measure);
    return () => { ro.disconnect(); window.removeEventListener('resize', measure); };
  }, [props.open, hasPdf]);

  useEffect(() => {
    if (!props.open) {
      setNumPages(0);
      setCurrentPage(1);
      setTargetRect(null);
      setRevealPreviewBeforeUnmount(false);
      savedStartRectRef.current = null;
      setReportLoading(false);
      setReportError(null);
      setComputedReport(props.report);
      if (pdfObjectUrl) {
        URL.revokeObjectURL(pdfObjectUrl);
        setPdfObjectUrl(null);
      }
      const id = setTimeout(() => {
        setClosingPhase(false);
        setCloseAnimData(null);
      }, 80);
      return () => clearTimeout(id);
    }
  }, [props.open, pdfObjectUrl]);

  useEffect(() => {
    let cancelled = false;
    // Ensure cookies/auth are included when loading via react-pdf.
    if (!props.open || !props.pdfUrl) {
      setPdfObjectUrl(null);
      return;
    }

    const absUrl = fileUrl;
    if (!absUrl) return;

    (async () => {
      try {
        const res = await fetch(absUrl, { credentials: 'include' });
        const blob = await res.blob();
        if (cancelled) return;
        const url = URL.createObjectURL(blob);
        setPdfObjectUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev);
          return url;
        });
      } catch {
        // Leave pdfObjectUrl null; Document will show its `error` renderer.
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [props.open, props.pdfUrl, fileUrl]);

  useEffect(() => {
    let cancelled = false;

    if (!props.open) return;

    // If a precomputed report is provided, prefer it.
    if (props.report) {
      setComputedReport(props.report);
      setReportLoading(false);
      setReportError(null);
      return;
    }

    if (!props.documentId) {
      setComputedReport(undefined);
      setReportLoading(false);
      setReportError(null);
      return;
    }

    setReportLoading(true);
    setReportError(null);

    (async () => {
      try {
        const detail = await getDocument(props.documentId!);
        if (cancelled) return;
        setComputedReport(mapCheckResultsToDocumentReport(detail));
      } catch (e) {
        if (cancelled) return;
        setComputedReport(undefined);
        setReportError(e instanceof Error ? e.message : 'Failed to load report');
      } finally {
        if (cancelled) return;
        setReportLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [props.open, props.documentId, props.report]);

  useEffect(() => {
    if (!props.open || !isTransitioning) return;
    let cancelled = false;
    const measure = () => {
      const node = containerRef.current;
      if (cancelled || !node) return;
      const rect = node.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        setTargetRect({ left: rect.left, top: rect.top, width: rect.width, height: rect.height });
      }
    };
    const id = setTimeout(() => {
      requestAnimationFrame(() => requestAnimationFrame(measure));
    }, 50);
    return () => {
      cancelled = true;
      clearTimeout(id);
    };
  }, [props.open, isTransitioning]);

  const handleClose = useCallback(() => {
    if (closingPhase) return;

    const savedRect = savedStartRectRef.current;
    const previewNode = containerRef.current;

    if (!savedRect || !previewNode) {
      props.onClose();
      return;
    }

    const currentRect = previewNode.getBoundingClientRect();
    if (currentRect.width === 0 || currentRect.height === 0) {
      props.onClose();
      return;
    }

    const canvas = previewNode.querySelector('canvas');
    let image = '';
    if (canvas instanceof HTMLCanvasElement && canvas.width > 0) {
      try { image = canvas.toDataURL('image/png'); } catch { /* tainted canvas */ }
    }

    if (!image) {
      props.onClose();
      return;
    }

    setCloseAnimData({
      fromRect: { left: currentRect.left, top: currentRect.top, width: currentRect.width, height: currentRect.height },
      toRect: savedRect,
      image,
    });
    setClosingPhase(true);
  }, [closingPhase, props]);

  useEffect(() => {
    if (!props.open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [props.open, handleClose]);

  useEffect(() => {
    if (!revealPreviewBeforeUnmount) return;
    props.onTransitionComplete?.();
  }, [revealPreviewBeforeUnmount, props.onTransitionComplete]);

  const goToPage = useCallback((page: number) => {
    if (numPages > 0 && (page < 1 || page > numPages)) return;
    setCurrentPage(page);
    containerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

  }, [numPages]);

  const startRect = props.transitionStartRect ?? null;
  const showFlyout = isTransitioning && startRect && !revealPreviewBeforeUnmount;
  const reportToShow = computedReport ?? props.report;

  const allHighlights = useMemo<TextHighlight[]>(() => {
    if (!reportToShow) return [];
    const hl: TextHighlight[] = [];
    for (const section of [reportToShow.structure, reportToShow.formatting, reportToShow.content]) {
      for (const item of section.items) {
        if (item.highlights) hl.push(...item.highlights);
      }
    }
    return hl;
  }, [reportToShow]);

  const pdfScale = containerWidth / pdfPageWidthPt;
  const activeKeySet = useMemo(() => new Set(activeHighlights.map(hlKey)), [activeHighlights]);

  return (
    <>
    <AnimatePresence>
      {props.open && !closingPhase && (
        <motion.div
          key="document-detail-modal"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-[200] bg-white flex flex-col overflow-hidden"
        >
          {showFlyout && startRect && (
            <motion.div
              className="fixed z-[250] pointer-events-none overflow-hidden rounded-[8px]"
              style={{ boxShadow: '0 4px 14px rgba(0,0,0,0.06)' }}
              initial={{
                left: startRect.left,
                top: startRect.top,
                width: startRect.width,
                height: startRect.height,
              }}
              animate={
                targetRect
                  ? {
                    left: targetRect.left,
                    top: targetRect.top,
                    width: targetRect.width,
                    height: targetRect.height,
                  }
                  : {
                    left: startRect.left,
                    top: startRect.top,
                    width: startRect.width,
                    height: startRect.height,
                  }
              }
              transition={{ type: 'tween', duration: 0.35, ease: [0.25, 0.1, 0.25, 1] }}
              onAnimationComplete={() => {
                if (targetRect) setRevealPreviewBeforeUnmount(true);
              }}
            >
              {props.transitionPreviewImage ? (
                <img
                  src={props.transitionPreviewImage}
                  alt=""
                  className="w-full h-full object-cover"
                  style={{ clipPath: 'polygon(0 0, calc(100% - 20px) 0, 100% 20px, 100% 100%, 0 100%)' }}
                />
              ) : (
                <div className="w-full h-full bg-gray-200" />
              )}
            </motion.div>
          )}

          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); handleClose(); }}
            className="fixed top-4 right-5 p-2 rounded-full bg-black/5 hover:bg-black/10 transition-colors z-10"
            aria-label={t('common.close')}
            style={{
              top: hasPdf && fileUrl ? previewTopPad : 24,
            }}
          >
            <X className="size-5" />
          </button>

          <div className="flex-1 min-h-0 overflow-y-auto">
            <div
              className="md:grid min-h-full py-6"
              style={{ gridTemplateColumns: 'repeat(24, 1fr)' }}
            >
            {/* Thumbnail sidebar — own grid column */}
            {hasPdf && fileUrl && numPages > 0 && (
              <div className="hidden md:block" style={{ gridColumn: '2 / 4' }}>
                <div className="sticky top-0 h-dvh flex flex-col">
                  <div className="flex-1 min-h-0 overflow-y-auto scrollbar-thin" style={{ paddingTop: previewTopPad, paddingBottom: 24 }}>
                    <Document file={pdfObjectUrl ?? fileUrl} loading={null} error={null}>
                      <div className="flex flex-col items-center gap-2 py-0.5 px-1">
                        {Array.from({ length: numPages }, (_, i) => i + 1).map((pageNum) => (
                          <button
                            key={pageNum}
                            type="button"
                            ref={(el) => {
                              if (el && pageNum === currentPage) {
                                el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
                              }
                            }}
                            onClick={() => setCurrentPage(pageNum)}
                            className="flex flex-col items-center gap-1 w-full group"
                          >
                            <div
                              className={`w-full rounded-md overflow-hidden transition-all duration-150 ${
                                pageNum === currentPage
                                  ? 'ring-2 ring-black/80 shadow-md'
                                  : 'ring-1 ring-black/8 hover:ring-black/20'
                              }`}
                              style={{ aspectRatio: '210 / 297' }}
                            >
                              <Page
                                pageNumber={pageNum}
                                width={80}
                                renderTextLayer={false}
                                renderAnnotationLayer={false}
                                loading={<div className="bg-gray-100 size-full" />}
                              />
                            </div>
                            <span className={`text-xs mt-2 mb-3 tabular-nums leading-none ${
                              pageNum === currentPage ? 'text-black font-semibold' : 'text-gray-400 group-hover:text-gray-600'
                            }`}>
                              {pageNum}
                            </span>
                          </button>
                        ))}
                      </div>
                    </Document>
                  </div>
                </div>
              </div>
            )}

            {/* PDF preview — own grid column */}
            {hasPdf && fileUrl && (
              <div className="px-4 md:px-0 mb-6 md:mb-0 ml-4" style={{ gridColumn: '4 / 12' }}>
                <div className="sticky top-0 h-dvh w-full flex items-center py-6">
                  <div
                    ref={containerRef}
                    className="relative w-full bg-gray-100 rounded-xl overflow-hidden flex items-center justify-center"
                    style={{
                      aspectRatio: '210/297',
                      maxHeight: '100%',
                      opacity: (revealPreviewBeforeUnmount || !isTransitioning) ? 1 : 0,
                      boxShadow: '0 4px 24px rgba(0,0,0,0.07)'
                    }}
                  >
                    {/* {numPages > 0 && (
                      <div className="flex items-center justify-center gap-3 absolute bottom-0 left-0 right-0 py-4 z-10 hover:opacity-100 opacity-0 transition-opacity duration-200 bg-linear-to-t from-white to-transparent">
                        <button
                          type="button"
                          disabled={!canPrev}
                          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                          className="p-1 rounded-full bg-black/5 hover:bg-black/10 disabled:opacity-30 disabled:pointer-events-none transition-colors"
                          aria-label={t('documents.pagePrev')}
                        >
                          <ChevronLeft className="size-5" />
                        </button>
                        <span className="text-xs opacity-60 font-medium tabular-nums min-w-16 text-center">
                          {currentPage} / {numPages}
                        </span>
                        <button
                          type="button"
                          disabled={!canNext}
                          onClick={() => setCurrentPage((p) => Math.min(numPages, p + 1))}
                          className="p-1 rounded-full bg-black/5 hover:bg-black/10 disabled:opacity-30 disabled:pointer-events-none transition-colors"
                          aria-label={t('documents.pageNext')}
                        >
                          <ChevronRight className="size-5" />
                        </button>
                      </div>
                    )} */}
                    <Document
                      file={pdfObjectUrl ?? fileUrl}
                      loading={
                        <div className="absolute inset-0 flex items-center justify-center">
                          <Spinner className="size-8 text-gray-400" />
                        </div>
                      }
                      error={
                        <div className="p-4 text-center text-sm text-red-600">
                          {t('report.noReport')}
                        </div>
                      }
                      onLoadSuccess={({ numPages: n }) => setNumPages(n)}
                      className="flex items-center justify-center size-full min-h-0"
                    >
                      <div className="relative">
                        <Page
                          pageNumber={currentPage}
                          width={containerWidth}
                          renderTextLayer={false}
                          renderAnnotationLayer={false}
                          className="max-w-full max-h-full object-contain"
                          onRenderSuccess={(page) => {
                            if (page.originalWidth) setPdfPageWidthPt(page.originalWidth);
                          }}
                        />
                        {allHighlights.length > 0 && (
                          <HighlightOverlay
                            highlights={allHighlights}
                            page={currentPage}
                            scale={pdfScale}
                            activeKeys={activeKeySet}
                          />
                        )}
                      </div>
                    </Document>
                  </div>
                </div>
              </div>
            )}

            {/* Right column — description + report */}
            <div
              className="px-4 md:px-0"
              style={{
                gridColumn: hasPdf && fileUrl ? '14 / 22' : '4 / 22',
                paddingTop: hasPdf && fileUrl ? previewTopPad : 24,
              }}
            >
              <div className="flex flex-col gap-5">
                {/* Document info */}
                <div className="flex flex-col gap-2">
                  <p className="font-medium text-2xl break-all">{props.title}</p>
                  <table className="w-full text-sm border-separate border-spacing-y-1.5">
                    <tbody>
                      <tr>
                        <td className="pr-4 text-gray-500 text-xs uppercase">{t('documents.type_full')}</td>
                        <td className="text-right">{props.typeLabel}</td>
                      </tr>
                      <tr>
                        <td className="pr-4 text-gray-500 text-xs uppercase">{t('documents.pages_full')}</td>
                        <td className="text-right">{numPages > 0 ? numPages : props.pages}</td>
                      </tr>
                      {props.author && (
                        <tr>
                          <td className="pr-4 text-gray-500 text-xs uppercase">{t('documents.author_full')}</td>
                          <td className="text-right">{props.author}</td>
                        </tr>
                      )}
                    </tbody>
                  </table>

                  {(() => {
                    const config = statusCardConfig[props.status];
                    const Icon = config.icon;
                    return (
                      <div
                        className={`rounded-full px-5 -mx-1 py-3 mt-2 flex items-center gap-3 ${config.bgClass}`}
                      >
                        <Icon
                          className={`size-6 shrink-0 ${config.iconClass} ${props.status === 'pending' ? 'animate-spin' : ''}`}
                        />
                        <div className="flex flex-col gap-0.5 min-w-0">
                          <span className="font-medium text-sm text-gray-900">
                            {t(statusKeys[props.status].labelKey)}
                          </span>
                          {reportToShow?.checkDate && (
                            <span className="text-xs text-gray-600">
                              {t('report.checkDate')} {formatCheckDateAndTime(reportToShow.checkDate, i18n.language)}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })()}
                </div>

                <div className="h-px w-full bg-black/5" />

                {/* Report sections */}
                {reportLoading ? (
                  <div className="flex items-center justify-center py-8 text-gray-400 text-sm">
                    <Spinner className="size-5 opacity-70" />
                  </div>
                ) : reportToShow ? (
                  <div className="flex flex-col gap-2 pb-6">
                    {[reportToShow.structure, reportToShow.formatting, reportToShow.content]
                      .filter((s) => s.items.length > 0)
                      .map((section) => (
                      <div key={section.title}>
                        <div className="flex items-center justify-between">
                          <div className="pb-2 pt-4 text-sm uppercase font-medium text-gray-500">
                            {t(section.title)}
                          </div>
                          <div className="px-2.5 py-1.5 bg-black/5 rounded-full text-xs tabular-nums">
                            {section.passed}/{section.total}
                          </div>
                        </div>
                        <div className="overflow-hidden">
                          <ul className="divide-y divide-black/6">
                            {section.items.map((item, i) => (
                              <li key={i} className="py-3 flex flex-col gap-1.5">
                                <div className="flex items-center gap-2">
                                  <ReportIcon status={item.status} />
                                  <span className="text-sm">{typeof item.label === 'string' && item.label.startsWith('report.') ? t(item.label) : item.label}</span>
                                </div>
                                {item.detail && (() => {
                                  const cleaned = stripRedundantTail(item.detail, item.richDetail);
                                  return cleaned ? (
                                    <span className="text-sm text-gray-500 pl-5.5">{cleaned}</span>
                                  ) : null;
                                })()}
                                {item.richDetail && (
                                  <div className="pl-5.5 mt-0.5">
                                    <RichDetailView
                                      detail={item.richDetail}
                                      onGoToPage={hasPdf ? goToPage : undefined}
                                      tooltip={item.detail ? stripRedundantTail(item.detail, item.richDetail) : undefined}
                                      highlights={item.chipHighlights}
                                      pdfHighlights={item.highlights}
                                      pdfFile={pdfObjectUrl ?? fileUrl}
                                      onHighlightHover={handleHighlightHover}
                                      onHighlightLeave={handleHighlightLeave}
                                    />
                                  </div>
                                )}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center justify-center py-8 text-gray-400 text-sm">
                    {reportError ? reportError : t('report.noReport')}
                  </div>
                )}
              </div>
            </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>

    {closingPhase && closeAnimData && (
      <motion.div
        key="close-flyout"
        className="fixed z-[300] pointer-events-none overflow-hidden rounded-[8px]"
        style={{ boxShadow: '0 4px 14px rgba(0,0,0,0.06)' }}
        initial={{
          left: closeAnimData.fromRect.left,
          top: closeAnimData.fromRect.top,
          width: closeAnimData.fromRect.width,
          height: closeAnimData.fromRect.height,
        }}
        animate={{
          left: closeAnimData.toRect.left,
          top: closeAnimData.toRect.top,
          width: closeAnimData.toRect.width,
          height: closeAnimData.toRect.height,
        }}
        transition={{ type: 'tween', duration: 0.35, ease: [0.25, 0.1, 0.25, 1] }}
        onAnimationComplete={() => {
          props.onClose();
        }}
      >
        <img
          src={closeAnimData.image}
          alt=""
          className="w-full h-full object-cover"
          style={{ clipPath: 'polygon(0 0, calc(100% - 20px) 0, 100% 20px, 100% 100%, 0 100%)' }}
        />
      </motion.div>
    )}
    </>
  );
};

export default DocumentDetailModal;
