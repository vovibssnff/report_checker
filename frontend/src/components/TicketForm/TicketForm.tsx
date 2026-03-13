import React, { useEffect, useRef, useState } from 'react';
import { observer } from 'mobx-react-lite';
import { AnimatePresence, motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { Search, ChevronDown } from 'lucide-react';
import { ticketStore } from '../../store/ticketStore';
import useEmblaCarousel from 'embla-carousel-react';
import Button from '../Button/Button';
import CrossIcon from '../icons/CrossIcon/CrossIcon';
import ItemCard from '../ItemCard/ItemCard';
import DocumentDetailModal from '../DocumentDetailModal/DocumentDetailModal';
import type { DocumentItem, DocumentStatus, DocType } from '../../types/document';
import { documentsList } from '../../data';

const PDF_ACCEPT = '.pdf,application/pdf';

type TFunc = (key: string, options?: Record<string, unknown>) => string;

function formatDayHeader(date: Date, t: TFunc): string {
  const weekdays = t('documents.weekdays', { returnObjects: true }) as unknown as string[];
  const months = t('documents.monthsGenitive', { returnObjects: true }) as unknown as string[];
  return `${weekdays[date.getDay()]}, ${date.getDate()} ${months[date.getMonth()]}`;
}

function pluralDocuments(n: number, t: TFunc): string {
  const mod100 = n % 100;
  const mod10 = n % 10;
  let form: string;
  if (mod100 >= 11 && mod100 <= 19) form = t('documents.document_many');
  else if (mod10 === 1) form = t('documents.document_one');
  else if (mod10 >= 2 && mod10 <= 4) form = t('documents.document_few');
  else form = t('documents.document_many');
  return `${n} ${form}`;
}

function dateKey(d: Date): string {
  return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
}

type ItemStatus = DocumentStatus;

type ReadinessFilter = 'all' | 'checked' | 'pending';
type StatusFilter = 'all' | 'passed' | 'failed' | 'warnings';

const isChecked = (s: ItemStatus) => s === 'passed' || s === 'failed' || s === 'warnings';

function countByReadiness(cards: DocumentItem[]) {
  let checked = 0, pending = 0;
  for (const c of cards) {
    if (isChecked(c.status)) checked++; else pending++;
  }
  return { checked, pending };
}

function countByStatus(cards: DocumentItem[]) {
  let passed = 0, failed = 0, warnings = 0;
  for (const c of cards) {
    if (c.status === 'passed') passed++;
    else if (c.status === 'failed') failed++;
    else if (c.status === 'warnings') warnings++;
  }
  return { passed, failed, warnings };
}

type DocTypeFilter = 'all' | DocType;

function applyFilters(
  cards: DocumentItem[],
  readiness: ReadinessFilter,
  status: StatusFilter,
  authorQuery: string,
  docTypeFilter: DocTypeFilter,
): DocumentItem[] {
  const q = authorQuery.trim().toLowerCase();
  return cards.filter((c) => {
    if (readiness === 'checked' && !isChecked(c.status)) return false;
    if (readiness === 'pending' && c.status !== 'pending') return false;
    if (status !== 'all' && c.status !== status) return false;
    if (q && !c.author.toLowerCase().includes(q)) return false;
    if (docTypeFilter !== 'all' && c.docType !== docTypeFilter) return false;
    return true;
  });
}

interface FilterChipProps {
  label: string;
  count?: number;
  active: boolean;
  onClick: () => void;
}

const FilterChip: React.FC<FilterChipProps> = ({ label, count, active, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    className={`shrink-0 flex items-center gap-1.5 py-1.5 text-sm font-medium transition-colors whitespace-nowrap ${
      active ? 'text-black' : 'text-gray-400 hover:text-gray-600'
    }`}
  >
    {label}
    {count !== undefined && (
      <span className={`inline-flex items-center justify-center min-w-5 h-5 px-1.5 text-sm rounded-full font-semibold ${
        active ? 'bg-black text-white' : 'bg-[rgba(0,0,0,0.06)]'
      }`}>
        {count}
      </span>
    )}
  </button>
);

function groupByDay(cards: DocumentItem[]): { date: Date; cards: DocumentItem[] }[] {
  const map = new Map<string, { date: Date; cards: DocumentItem[] }>();
  for (const card of cards) {
    const key = dateKey(card.createdAt);
    if (!map.has(key)) map.set(key, { date: card.createdAt, cards: [] });
    map.get(key)!.cards.push(card);
  }
  return [...map.values()].sort((a, b) => b.date.getTime() - a.date.getTime());
}

interface TicketFormProps {
  className?: string;
}

const TicketForm: React.FC<TicketFormProps> = observer((props) => {
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragOverBlock, setDragOverBlock] = useState(false);
  const [dragOverWindow, setDragOverWindow] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [readinessFilter, setReadinessFilter] = useState<ReadinessFilter>('all');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [authorSearch, setAuthorSearch] = useState('');
  const [docTypeFilter, setDocTypeFilter] = useState<DocTypeFilter>('all');
  const [docTypeOpen, setDocTypeOpen] = useState(false);
  const docTypeRef = useRef<HTMLDivElement>(null);
  const [selectedCard, setSelectedCard] = useState<DocumentItem | null>(null);
  const [transitionStartRect, setTransitionStartRect] = useState<{ left: number; top: number; width: number; height: number } | null>(null);
  const [transitionPreviewImage, setTransitionPreviewImage] = useState<string | null>(null);

  const handleCardClick = (card: DocumentItem, e: React.MouseEvent | React.KeyboardEvent) => {
    if (card.status === 'pending') return;
    const cardEl = e.currentTarget as HTMLElement;
    const previewEl = cardEl.querySelector('[data-preview-container]');
    if (previewEl) {
      const rect = previewEl.getBoundingClientRect();
      const canvas = previewEl.querySelector('canvas');
      let dataUrl: string | null = null;
      if (canvas && canvas instanceof HTMLCanvasElement && canvas.width > 0) {
        dataUrl = canvas.toDataURL('image/png');
      }
      setTransitionStartRect({ left: rect.left, top: rect.top, width: rect.width, height: rect.height });
      setTransitionPreviewImage(dataUrl);
    }
    setSelectedCard(card);
  };

  const handleCloseModal = () => {
    setSelectedCard(null);
    setTransitionStartRect(null);
    setTransitionPreviewImage(null);
  };

  const handleTransitionComplete = () => {
    setTransitionStartRect(null);
    setTransitionPreviewImage(null);
  };

  useEffect(() => {
    if (!docTypeOpen) return;
    function handler(e: MouseEvent) {
      if (!docTypeRef.current?.contains(e.target as Node)) setDocTypeOpen(false);
    }
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [docTypeOpen]);

  const readinessCounts = countByReadiness(documentsList);
  const statusCounts = countByStatus(documentsList);
  const filteredCards = applyFilters(documentsList, readinessFilter, statusFilter, authorSearch, docTypeFilter);

  const { createTicket, creatingTicket } = ticketStore;

  const [emblaRef, emblaApi] = useEmblaCarousel({
    loop: false,
    duration: 16,
    watchDrag: false
  });

  useEffect(() => {
    if (emblaApi) {
      emblaApi.scrollTo(currentStep);
    }
  }, [emblaApi, currentStep]);

  const pickFiles = (files: FileList | null) => {
    if (!files?.length) return;
    const file = files[0];
    if (file.type !== 'application/pdf') return;
    setSelectedFile(file);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    pickFiles(e.target.files ?? null);
    e.target.value = '';
  };

  const handleUploadBlockClick = () => {
    fileInputRef.current?.click();
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.types.includes('Files')) setDragOverBlock(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOverBlock(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOverBlock(false);
    setDragOverWindow(false);
    pickFiles(e.dataTransfer.files);
  };

  const handleWindowDragEnter = (e: React.DragEvent) => {
    if (e.dataTransfer.types.includes('Files')) setDragOverWindow(true);
  };

  const handleWindowDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOverWindow(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || creatingTicket) return;
    try {
      await createTicket({
        question: selectedFile.name,
      });
      setSelectedFile(null);
    } catch {
      // keep file on error
    }
  };

  const finalClassName = 'relative w-[90%] max-w-3xl mx-auto h-[calc(100%)]' + (props.className || '');

  return (
    <>
      <form onSubmit={handleSubmit} className={finalClassName}>
        <div className="embla col-start-1 col-end-4 h-full relative z-0 " ref={emblaRef}>
          <div className="embla__container h-full flex w-full">
            <div className={`embla__slide relative h-full transition-all duration-200 ${currentStep !== 0 ? 'opacity-0 pointer-events-none' : ''} `}>
              <div className="flex flex-col h-full px-5 relative overflow-y-auto no-scrollbar">
                <div className="flex flex-col gap-1 shrink-0 pb-8 sticky top-0 w-full bg-linear-to-b from-90% from-white to-transparent z-10 px-5">
                  <h1 className="text-2xl pb-4">
                    {t('documents.checkedOfTotal', { checked: readinessCounts.checked, total: documentsList.length })}{' '}
                    {pluralDocuments(documentsList.length, t).replace(/^\d+\s/, '')}
                  </h1>

                  <div className="flex flex-row gap-4 overflow-x-auto no-scrollbar">
                    <FilterChip label={t('documents.filterAll')} active={readinessFilter === 'all'} onClick={() => setReadinessFilter('all')} />
                    <FilterChip label={t('documents.filterChecked')} count={readinessCounts.checked} active={readinessFilter === 'checked'} onClick={() => setReadinessFilter('checked')} />
                    <FilterChip label={t('documents.filterPending')} count={readinessCounts.pending} active={readinessFilter === 'pending'} onClick={() => setReadinessFilter('pending')} />
                  </div>

                  <div className="h-px w-full bg-[rgba(0,0,0,0.06)]" />

                  <div className="flex flex-row gap-4 overflow-x-auto no-scrollbar">
                    <FilterChip label={t('documents.filterAll')} active={statusFilter === 'all'} onClick={() => setStatusFilter('all')} />
                    <FilterChip label={t('documents.filterPassed')} count={statusCounts.passed} active={statusFilter === 'passed'} onClick={() => setStatusFilter('passed')} />
                    <FilterChip label={t('documents.filterFailed')} count={statusCounts.failed} active={statusFilter === 'failed'} onClick={() => setStatusFilter('failed')} />
                    <FilterChip label={t('documents.filterWarnings')} count={statusCounts.warnings} active={statusFilter === 'warnings'} onClick={() => setStatusFilter('warnings')} />
                  </div>

                  <div className="flex flex-row gap-2 pt-2 -mx-2">
                    <div className="relative flex-1 min-w-0">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-gray-400 pointer-events-none" />
                      <input
                        type="text"
                        value={authorSearch}
                        onChange={(e) => setAuthorSearch(e.target.value)}
                        placeholder={t('documents.searchByAuthor')}
                        className="w-full h-9 pl-9 pr-3 text-sm rounded-full bg-[rgba(0,0,0,0.04)] outline-none placeholder:text-gray-400 focus:bg-[rgba(0,0,0,0.06)] transition-colors"
                      />
                    </div>
                    <div className="relative shrink-0" ref={docTypeRef}>
                      <button
                        type="button"
                        onClick={() => setDocTypeOpen((v) => !v)}
                        className="h-9 pr-3 pl-4 flex items-center gap-1.5 text-sm rounded-full bg-[rgba(0,0,0,0.04)] hover:bg-[rgba(0,0,0,0.06)] transition-colors whitespace-nowrap"
                      >
                        {docTypeFilter === 'all' ? t('documents.docTypeAll') : t(`documents.${docTypeFilter}`)}
                        <ChevronDown className={`size-3.5 text-gray-500 transition-transform ${docTypeOpen ? 'rotate-180' : ''}`} />
                      </button>
                      <AnimatePresence>
                        {docTypeOpen && (
                          <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            transition={{ duration: 0.1 }}
                            className="absolute right-0 top-[calc(100%+6px)] bg-white rounded-xl shadow-lg border border-[rgba(0,0,0,0.06)] py-1.5 z-50 min-w-[160px]"
                          >
                            {(['all', 'masters', 'bachelors'] as const).map((opt) => (
                              <button
                                key={opt}
                                type="button"
                                onClick={() => { setDocTypeFilter(opt); setDocTypeOpen(false); }}
                                className={`w-full text-left px-4 py-2 text-sm transition-colors hover:bg-[rgba(0,0,0,0.04)] ${docTypeFilter === opt ? 'font-medium' : ''}`}
                              >
                                {opt === 'all' ? t('documents.docTypeAll') : t(`documents.${opt}`)}
                              </button>
                            ))}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>
                </div>

                <div className="relative flex-1 pb-20 no-scrollbar">
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={`${readinessFilter}-${statusFilter}-${docTypeFilter}-${authorSearch}`}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.15 }}
                      className="flex flex-col gap-6"
                    >
                      {groupByDay(filteredCards).map((group) => (
                        <div key={dateKey(group.date)} className="flex flex-col gap-3 pt-2">
                          <div className="flex flex-col gap-[2px] px-5 pb-1">
                        <p className="text-sm font-medium">{formatDayHeader(group.date, t)}</p>
                        <p className="text-sm opacity-60">{pluralDocuments(group.cards.length, t)}</p>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {group.cards.map((card, i) => (
                              <div
                                key={i}
                                role={card.status !== 'pending' ? 'button' : undefined}
                                tabIndex={card.status !== 'pending' ? 0 : undefined}
                                onClick={(e) => handleCardClick(card, e)}
                                onKeyDown={card.status !== 'pending' ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleCardClick(card, e); } } : undefined}
                                className={card.status !== 'pending' ? 'cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-black/20 focus-visible:ring-offset-2 rounded-[26px]' : 'rounded-[26px]'}
                              >
                                <ItemCard
                                  title={card.title}
                                  type={t(`documents.${card.docType}`)}
                                  pages={card.pages}
                                  status={card.status}
                                  createdAt={card.createdAt}
                                  pdfUrl={card.pdfUrl}
                                  author={card.author}
                                  onDownloadClick={(e) => e.stopPropagation()}
                                  previewHidden={selectedCard !== null && selectedCard === card}
                                />
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </motion.div>
                  </AnimatePresence>
                </div>
              </div>
            </div>

            <div
              className={`embla__slide relative h-full flex items-center justify-center transition-all duration-200 ${currentStep !== 1 ? 'opacity-0 pointer-events-none' : ''} `}
              onDragEnter={handleWindowDragEnter}
              onDragLeave={handleWindowDragLeave}
            >
              <div className="flex flex-col gap-4 w-full">
                <div className='flex flex-col gap-2 w-full col-span-full mb-4 px-6'>
                  <h1 className="text-2xl">{t('tickets.newCheck')}</h1>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={PDF_ACCEPT}
                  className="hidden"
                  onChange={handleFileInputChange}
                />
                <motion.div
                  animate={{
                    scale: isFocused || dragOverBlock ? 1.05 : 1,
                    boxShadow: isFocused || dragOverBlock
                      ? '0 8px 16px rgba(0, 0, 0, 0.1)'
                      : '0 8px 16px rgba(0, 0, 0, 0.)',
                  }}
                  transition={{
                    type: 'spring',
                    stiffness: 400,
                    damping: 17,
                  }}
                  className="w-full h-14 bg-white border box-border border-[rgb(228,228,228)] backdrop-blur-2xl bg-[rgba(248,248,248,0.6)] rounded-[4rem] relative flex flex-row gap-4 items-center pr-[6px] pl-6 cursor-pointer select-none isolate"
                  onClick={handleUploadBlockClick}
                  onMouseEnter={() => setIsFocused(true)}
                  onMouseLeave={() => setIsFocused(false)}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <div className="min-w-0 flex-1 flex items-center relative z-0">
                    {selectedFile ? (
                      <p className="text-[0.9375rem] text-gray-800 truncate" title={selectedFile.name}>
                        {selectedFile.name}
                      </p>
                    ) : (
                      <p className="text-[0.9375rem] text-gray-500">{t('tickets.uploadDocument')}</p>
                    )}
                  </div>
                  {selectedFile && (
                    <>
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}
                        className="shrink-0 p-1.5 rounded-full text-gray-500 hover:text-gray-800 hover:bg-gray-100 transition-colors relative z-0"
                        aria-label={t('common.clear')}
                      >
                        <CrossIcon size="1rem" fill="currentColor" />
                      </button>
                      <Button
                        type="submit"
                        disabled={creatingTicket}
                        size="m"
                        className="shrink-0 transition-all duration-150 relative z-0"
                      >
                        {creatingTicket ? t('tickets.working') : t('tickets.send')}
                      </Button>
                    </>
                  )}
                  {(dragOverWindow || dragOverBlock) && (
                    <div className="absolute inset-0 rounded-[4rem] bg-black/5 flex items-center justify-center z-[100] pointer-events-none">
                      <p className="text-sm font-medium text-gray-700">
                        {dragOverBlock ? t('tickets.releaseHere') : t('tickets.dragHere')}
                      </p>
                    </div>
                  )}
                </motion.div>
                <p className="text-xs opacity-60 pl-6 mt-1">{t('tickets.uploadHint')}</p>
              </div>
            </div>
          </div>
        </div>

        <div className='absolute bottom-5 left-0 w-full flex items-center justify-center px-4 z-10 pointer-events-none'>
          <div className='flex flex-row gap-3 pointer-events-auto'>
            {currentStep > 0 && (
              <Button
                type="button"
                typeStyle="secondary"
                size="s"
                onClick={() => setCurrentStep(Math.max(currentStep - 1, 0))}
              >
                {t('documents.documentsButton')}
              </Button>
            )}
            {currentStep < 1 && (
              <Button
                type="button"
                size="s"
                onClick={() => setCurrentStep(1)}
              >
                {t('tickets.newCheck')}
              </Button>
            )}
          </div>
        </div>
      </form>
      <DocumentDetailModal
        open={selectedCard !== null}
        onClose={handleCloseModal}
        title={selectedCard?.title ?? ''}
        typeLabel={selectedCard ? t(`documents.${selectedCard.docType}`) : ''}
        pages={selectedCard?.pages ?? 0}
        status={selectedCard?.status ?? 'pending'}
        author={selectedCard?.author}
        pdfUrl={selectedCard?.pdfUrl}
        report={selectedCard?.report}
        transitionStartRect={transitionStartRect}
        transitionPreviewImage={transitionPreviewImage}
        onTransitionComplete={handleTransitionComplete}
      />
    </>
  );
});

export default TicketForm;
