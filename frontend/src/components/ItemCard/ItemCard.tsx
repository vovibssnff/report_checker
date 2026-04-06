import React, { useRef, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/TextLayer.css';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import './ItemCard.css';
import DownloadIcon from '../icons/DownloadIcon/DownloadIcon';
import LoadingText from '../LoadingText/LoadingText';
import { Spinner } from '../ui/spinner';

pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

type ItemStatus = 'failed' | 'passed' | 'warnings' | 'pending';

const statusKeys: Record<ItemStatus, { labelKey: string; subtitleKey: string }> = {
  pending: { labelKey: 'documents.statusPending', subtitleKey: '' },
  failed: { labelKey: 'documents.statusFailed', subtitleKey: '' },
  passed: { labelKey: 'documents.statusPassed', subtitleKey: 'documents.noWarnings' },
  warnings: { labelKey: 'documents.statusWarnings', subtitleKey: '' },
};

const StatusIcon: React.FC<{ status: ItemStatus }> = ({ status }) => {
  if (status === 'passed') {
    return <span className="text-green-600 font-bold text-base shrink-0">✓</span>;
  }
  if (status === 'warnings') {
    return <span className="text-amber-500 font-bold text-base shrink-0">⚠</span>;
  }
  if (status === 'failed') {
    return <span className="text-red-600 font-bold text-base shrink-0">✗</span>;
  }
  return null;
};

interface ItemCardProps {
  className?: string;
  title: string;
  type: string;
  pages: number;
  status: ItemStatus;
  file?: File;
  pdfUrl?: string;
  createdAt?: Date;
  author?: string;
  onDownloadClick?: (e: React.MouseEvent) => void;
  /** Скрыть превью (например, во время анимации перехода в модалку) */
  previewHidden?: boolean;
}

const ItemCard: React.FC<ItemCardProps> = (props) => {
  const { t } = useTranslation();
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(0);
  const stableWidthRef = useRef(0);
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  const source = props.file ?? props.pdfUrl;
  const pdfAbsUrl =
    props.pdfUrl && !props.pdfUrl.startsWith('http')
      ? `${window.location.origin}${props.pdfUrl.startsWith('/') ? '' : '/'}${props.pdfUrl}`
      : props.pdfUrl;
  const fileProp = props.file ? objectUrl : pdfAbsUrl;

  useEffect(() => {
    let cancelled = false;
    if (props.file) {
      const url = URL.createObjectURL(props.file);
      setObjectUrl(url);
      return () => URL.revokeObjectURL(url);
    }

    if (!props.pdfUrl) {
      setObjectUrl(null);
      return;
    }

    const absUrl = pdfAbsUrl;
    if (!absUrl) {
      setObjectUrl(null);
      return;
    }

    (async () => {
      try {
        const res = await fetch(absUrl, { credentials: 'include' });
        const blob = await res.blob();
        if (cancelled) return;
        const url = URL.createObjectURL(blob);
        setObjectUrl(url);
      } catch {
        setObjectUrl(null);
      }
    })();

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.file, props.pdfUrl]);

  useEffect(() => {
    if (!containerRef.current || !source) return;
    const el = containerRef.current;
    const ro = new ResizeObserver((entries) => {
      if (props.previewHidden) return;
      const w = entries[0]?.contentRect.width;
      if (typeof w === 'number' && w > 0 && w <= (stableWidthRef.current || Infinity)) {
        stableWidthRef.current = w;
        setContainerWidth(w);
      } else if (stableWidthRef.current === 0 && typeof w === 'number' && w > 0) {
        stableWidthRef.current = w;
        setContainerWidth(w);
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [source, props.previewHidden]);

  const finalClassName = 'item-card p-5 rounded-[26px] bg-[rgba(0,0,0,0.03)]' + (props.className || '');
  const shouldRenderPreview = !props.previewHidden && Boolean(fileProp) && containerWidth > 0;
  // Guard against transient layout/transform measurements that can cause react-pdf
  // to render a huge page, especially right after mount/filters/animations.
  const renderWidth = shouldRenderPreview ? Math.min(containerWidth, 240) : 0;
  return (
    <div className={finalClassName}>
      <div className='flex flex-col gap-2'>
        <div className='flex flex-row gap-5'>
          <div className='flex flex-col gap-2'>
            <div
              data-preview-container
              className={`relative h-full w-auto aspect-[1/1.35] transition-opacity duration-200 ${props.previewHidden ? 'opacity-0' : 'opacity-100'}`}
              style={{
                filter: 'drop-shadow(0 4px 10px rgba(0,0,0,0.05))',
              }}
            >
              <div
                ref={containerRef}
                className='relative h-full w-full rounded-[8px] overflow-hidden min-h-[120px]'
                style={{
                  clipPath: 'polygon(0 0, calc(100% - 20px) 0, 100% 20px, 100% 100%, 0 100%)',
                }}
              >
                {shouldRenderPreview ? (
                  <Document
                    file={fileProp}
                    loading={
                      <div className="absolute inset-0 flex items-center justify-center">
                        <Spinner className="size-6 opacity-70" />
                      </div>
                    }
                  >
                    <Page
                      pageNumber={1}
                      width={renderWidth}
                      devicePixelRatio={4}
                      className="max-w-full! h-auto!"
                      renderTextLayer={false}
                      renderAnnotationLayer={false}
                    />
                  </Document>
                ) : null}
              </div>
            </div>
            <button
              type="button"
              className='flex flex-row gap-1 px-4 items-center pt-1 pb-1 opacity-80 hover:opacity-100 transition-opacity cursor-pointer'
              onClick={(e) => {
                props.onDownloadClick?.(e);
                if (props.file) {
                  const url = URL.createObjectURL(props.file);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = props.file.name;
                  a.click();
                  URL.revokeObjectURL(url);
                } else if (props.pdfUrl) {
                  const a = document.createElement('a');
                  a.href = props.pdfUrl;
                  a.download = props.title + '.pdf';
                  a.click();
                }
              }}
            >
              <DownloadIcon size='10px' fill='black' />
              <p className='text-sm'>{t('documents.download')}</p>
            </button>
          </div>
          <div className='flex flex-col gap-2 w-full justify-between pb-[34px]'>
            {props.status !== 'pending' ? <p className='font-medium break-all'>{props.title}</p>
              :
              <LoadingText className="font-medium break-all">{props.title}</LoadingText>
            }
            <table className="w-full text-sm border-separate border-spacing-y-1.5">
              <tbody>
                {/* <tr>
                  <td className="pr-4 text-gray-500">{t('documents.type')}</td>
                  <td className="text-right">{props.type}</td>
                </tr> */}
                {props.pages > 0 && (
                  <tr>
                    <td className="text-xs pr-4 text-gray-500 uppercase">{t('documents.pages')}</td>
                    <td className="text-right">{props.pages}</td>
                  </tr>
                )}
                {props.author && (
                  <tr>
                    <td className="text-xs pr-4 text-gray-500 uppercase">{t('documents.author')}</td>
                    <td className="text-right">{props.author}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
        <div className='h-px w-full bg-[rgba(0,0,0,0.05)]' />
        <div className='flex flex-row gap-2 items-center justify-between pt-[8px]'>
          {props.status === 'pending' ? (
            <div className="flex flex-row items-center gap-2">
              <Spinner className="size-4 opacity-70" />
              <p className="text-sm">{t(statusKeys[props.status].labelKey)}</p>
            </div>
          ) : (
            <>
              <div className="flex flex-row items-center gap-3">
                <StatusIcon status={props.status} />
                <p className="text-sm text-black">
                  {t(statusKeys[props.status].labelKey)}
                </p>
              </div>
              {statusKeys[props.status].subtitleKey && (
                <p className='text-xs text-gray-400'>{t(statusKeys[props.status].subtitleKey)}</p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ItemCard;
