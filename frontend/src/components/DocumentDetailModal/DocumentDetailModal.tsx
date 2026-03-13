import React, { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { X, ChevronLeft, ChevronRight, CheckCircle2, XCircle, AlertCircle, Loader2 } from 'lucide-react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/TextLayer.css';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import type { DocumentReport, ReportCheckStatus } from '../../types/documentReport';
import { Spinner } from '../ui/spinner';

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
  report?: DocumentReport;
  transitionStartRect?: { left: number; top: number; width: number; height: number } | null;
  transitionPreviewImage?: string | null;  /** Вызов по окончании анимации перехода */
  onTransitionComplete?: () => void;
}

const DocumentDetailModal: React.FC<DocumentDetailModalProps> = (props) => {
  const { t, i18n } = useTranslation();
  const containerRef = useRef<HTMLDivElement>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [numPages, setNumPages] = useState(0);
  const [containerWidth, setContainerWidth] = useState(360);
  const [targetRect, setTargetRect] = useState<{ left: number; top: number; width: number; height: number } | null>(null);
  const [revealPreviewBeforeUnmount, setRevealPreviewBeforeUnmount] = useState(false);

  const source = props.pdfUrl;
  const hasPdf = Boolean(source);
  const isTransitioning = Boolean(props.transitionStartRect && props.transitionPreviewImage);
  const fileUrl = source
    ? source.startsWith('http')
      ? source
      : `${window.location.origin}${source.startsWith('/') ? '' : '/'}${source}`
    : null;

  useEffect(() => {
    if (!props.open || !containerRef.current || !hasPdf) return;
    const el = containerRef.current;
    const ro = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width;
      if (typeof w === 'number' && w > 0) setContainerWidth(w);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [props.open, hasPdf]);

  useEffect(() => {
    if (!props.open) {
      setNumPages(0);
      setCurrentPage(1);
      setTargetRect(null);
      setRevealPreviewBeforeUnmount(false);
    }
  }, [props.open]);

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

  useEffect(() => {
    if (!props.open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') props.onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [props.open, props.onClose]);

  useEffect(() => {
    if (!revealPreviewBeforeUnmount) return;
    let cancelled = false;
    const id = requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (!cancelled) props.onTransitionComplete?.();
      });
    });
    return () => {
      cancelled = true;
      cancelAnimationFrame(id);
    };
  }, [revealPreviewBeforeUnmount, props.onTransitionComplete]);

  const canPrev = currentPage > 1;
  const canNext = currentPage < numPages;

  const startRect = props.transitionStartRect ?? null;
  const showFlyout = isTransitioning && startRect;

  return (
    <AnimatePresence>
      {props.open && (
        <motion.div
          key="document-detail-modal"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-[200] bg-white flex flex-col overflow-hidden"
          onClick={props.onClose}
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

          <div className="flex-1 min-h-0 overflow-auto">
            <div className="w-[90%] max-w-3xl mx-auto px-4 py-6 md:py-8 min-h-full">
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); props.onClose(); }}
                className="fixed top-16 right-5 p-2 rounded-full bg-black/5 hover:bg-black/10 transition-colors z-10"
                aria-label={t('common.close')}
              >
                <X className="size-5" />
              </button>

              <div className="flex flex-col gap-6 md:gap-8 pt-10 md:pt-12">
                <div className="flex flex-col md:flex-row gap-6 md:gap-8 md:items-start">
                  <div className="w-full md:w-1/2 shrink-0 flex flex-col gap-3">
                    {hasPdf && fileUrl && (
                      <>
                        <div
                          ref={containerRef}
                          className="relative w-full bg-gray-100 rounded-xl overflow-hidden flex items-center justify-center transition-opacity duration-200"
                          style={{
                            aspectRatio: '210/297',
                            opacity: (revealPreviewBeforeUnmount || !isTransitioning) ? 1 : 0,
                            boxShadow: '0 4px 24px rgba(0,0,0,0.07)'
                          }}
                        >
                          {numPages > 0 && (
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
                          )}
                          <Document
                            file={fileUrl}
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
                            <Page
                              pageNumber={currentPage}
                              width={containerWidth}
                              renderTextLayer={false}
                              renderAnnotationLayer={false}
                              className="max-w-full max-h-full object-contain"
                            />
                          </Document>
                        </div>
                      </>
                    )}
                  </div>

                  <div className="w-full md:w-1/2 flex flex-col gap-2 min-w-0">
                    <p className="font-medium text-2xl">{props.title}</p>
                    <table className="w-full text-sm border-separate border-spacing-y-1.5 ">
                      <tbody>
                        <tr>
                          <td className="pr-4 text-gray-500 text-xs uppercase">{t('documents.type')}</td>
                          <td className="text-right">{props.typeLabel}</td>
                        </tr>
                        <tr>
                          <td className="pr-4 text-gray-500 text-xs uppercase">{t('documents.pages')}</td>
                          <td className="text-right">{numPages > 0 ? numPages : props.pages}</td>
                        </tr>
                        {props.author && (
                          <tr>
                            <td className="pr-4 text-gray-500 text-xs uppercase">{t('documents.author')}</td>
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
                            {props.report?.checkDate && (
                              <span className="text-xs text-gray-600">
                                {t('report.checkDate')} {formatCheckDateAndTime(props.report.checkDate, i18n.language)}
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                </div>

                <div className="h-px w-full bg-[rgba(0,0,0,0.05)]" />

                {props.report ? (
                  <div className="flex flex-col gap-4">
                    {[props.report.structure, props.report.formatting, props.report.content].map((section) => (
                      <div>
                        <div className='flex items-center justify-between'>
                          <div className="pb-2 pt-4 text-sm uppercase">
                            {t(section.title)}
                          </div>
                          <div className="px-2 py-1 bg-black/5 rounded-full text-sm mr-4">
                            {section.passed}/{section.total}
                          </div>
                        </div>
                        <div key={section.title} className="overflow-hidden">
                          <ul className="divide-y divide-black/6">
                            {section.items.map((item, i) => (
                              <li key={i} className="py-3 flex flex-col gap-0.5">
                                <div className="flex items-center gap-2">
                                  <ReportIcon status={item.status} />
                                  <span className="text-sm">{typeof item.label === 'string' && item.label.startsWith('report.') ? t(item.label) : item.label}</span>
                                </div>
                                {item.detail && (
                                  <span className="text-sm text-gray-500 pl-5.5">
                                    {item.detail.startsWith('report.') ? t(item.detail) : item.detail}
                                  </span>
                                )}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ))}
{/* 
                    <div className="border-t-2 border-black/10 pt-4 flex flex-wrap items-baseline gap-2">
                      <span className="font-medium">{t('report.total')}:</span>
                      <span>{props.report.totalPassed}/{props.report.totalChecks} ({Math.round((props.report.totalPassed / props.report.totalChecks) * 100)}%)</span>
                      <span className="text-gray-500 ml-2">{t('report.status')}:</span>
                      <span className="font-medium">{t(props.report.overallStatus)}</span>
                    </div> */}
                  </div>
                ) : (
                  <div className="flex items-center justify-center py-8 text-gray-400 text-sm">
                    {t('report.noReport')}
                  </div>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default DocumentDetailModal;
