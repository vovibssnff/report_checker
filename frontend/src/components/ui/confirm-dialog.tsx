interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'default';
}

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
}: ConfirmDialogProps) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/20" onClick={onClose} aria-hidden />
      <div
        className="relative z-10 w-full max-w-sm rounded-[1.5rem] bg-white p-4 shadow-lg outline outline-[rgba(0,0,0,0.06)]"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
      >
        <div className="flex flex-col p-2">
          <h2 id="confirm-dialog-title" className="text-xl">
            {title}
          </h2>
          {description && <p className="mt-1 opacity-60">{description}</p>}
        </div>
        <div className="mt-10 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-[3rem] px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 cursor-pointer"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className={
              variant === 'danger'
                ? 'rounded-[3rem] px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 cursor-pointer'
                : 'rounded-[3rem] px-4 py-2 text-sm font-medium bg-gray-900 text-white hover:bg-gray-800'
            }
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
