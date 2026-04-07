import React, { useState } from 'react';
import { Trash2 } from 'lucide-react';
import './Card.css';
import SourceTag from '../SourceTag/SourceTag';
import { Spinner } from '../ui/spinner';
import { ConfirmDialog } from '../ui/confirm-dialog';

export type Source = 'script' | 'docs' | 'expert' | 'new_doc';
export type Status = 'resolved' | 'pending' | 'rejected';

export type SolutionStatusBadge = 'pending' | 'processed' | 'done';

const SOLUTION_STATUS_LABEL: Record<SolutionStatusBadge, string> = {
  pending: 'Pending',
  processed: 'Processed',
  done: '',
};

export interface CardProps {
  className?: string;
  id?: string;
  title: string;
  description?: string;
  sources?: Source[];
  status?: Status;
  solutionStatus?: SolutionStatusBadge;
  active?: boolean;
  onClick?: (id: string) => void;
  onDelete?: (id: string) => void;
}

const Card: React.FC<CardProps> = (props) => {
  const [hover, setHover] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const finalClassName =
    'card w-full h-fit flex flex-col gap-1 hover:bg-[rgba(0,0,0,0.05)] rounded-[0.875rem] p-3 cursor-pointer ' +
    (props.active && 'active-card bg-[rgba(0,0,0,0.05)] ') +
    (props.className || '');

  const handleClick = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.card__delete-btn')) return;
    props.id && props.onClick?.(props.id);
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setConfirmOpen(true);
  };

  const handleConfirmDelete = () => {
    if (props.id && props.onDelete) props.onDelete(props.id);
  };

  return (
    <>
      <div
        className={finalClassName + (hover && props.onDelete ? ' card--hover-delete' : '')}
        onClick={handleClick}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && props.id && props.onClick?.(props.id)}
      >
        <div className="flex flex-row justify-between gap-4 items-center">
          <h3 className="w-full min-w-0 truncate card__title">{props.title}</h3>
          {props.onDelete && (
            <button
              type="button"
              className="card__delete-btn absolute top-[10px] right-3 p-1.5 rounded-md text-gray-500 hover:text-red-600 opacity-0 transition-opacity"
              onClick={handleDeleteClick}
              aria-label="Delete"
            >
              <Trash2 className="size-4" />
            </button>
          )}
          <div className="flex flex-row mr-1 items-center gap-1 shrink-0 card__meta">
            {props.solutionStatus != null && (
              <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs opacity-70">
                {SOLUTION_STATUS_LABEL[props.solutionStatus]}
                {props.solutionStatus === 'pending' && <Spinner className="size-3" />}
              </span>
            )}
            {props.solutionStatus !== 'pending' && props.sources && props.sources.length > 0 &&
              props.sources.map((source) => <SourceTag compact key={source} source={source} />)}
          </div>
        </div>
        {props.description && <p className="opacity-60 text-xs max-w-[75%] truncate card__description">{props.description}</p>}
      </div>
      <ConfirmDialog
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={handleConfirmDelete}
        title="Delete Dialogue?"
        description="This action cannot be undone."
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
      />
    </>
  );
};

export default Card;
