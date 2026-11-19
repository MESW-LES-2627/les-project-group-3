"use client";

import { useEffect, useId, useRef } from "react";

import { FieldError } from "@/components/matchmaker/field-error";
import type { Confirmation } from "@/lib/confirmation";

const CONFIRM =
  "inline-flex min-h-11 items-center justify-center rounded-xl bg-forest px-5 text-sm font-semibold text-white transition hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-60";
const CANCEL =
  "inline-flex min-h-11 items-center justify-center rounded-xl border border-line bg-surface px-5 text-sm font-semibold text-muted transition hover:border-forest hover:text-forest focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-60";

type ConfirmDialogProps = {
  open: boolean;
  confirmation: Confirmation;
  confirmLabel: string;
  pendingLabel: string;
  pending: boolean;
  error: string | null;
  onConfirm: () => void;
  onCancel: () => void;
};

// The browser's own modal <dialog>: showModal() gives the backdrop, Escape, an
// inert page behind it and focus kept inside; closing returns focus to the
// button that opened it. A failed action keeps it open with the error inside.
export function ConfirmDialog({
  open,
  confirmation,
  confirmLabel,
  pendingLabel,
  pending,
  error,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const id = useId();
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (dialog === null) {
      return;
    }
    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={`${id}-title`}
      aria-describedby={confirmation.message ? `${id}-message` : undefined}
      onCancel={(event) => {
        // Escape: the open prop decides, and nothing closes mid-action.
        event.preventDefault();
        if (!pending) {
          onCancel();
        }
      }}
      onClose={() => {
        // A second Escape closes it anyway (Chrome). Mid-action, open it again so
        // the result still shows; otherwise tell the opener, or the open prop
        // stays true and the button can no longer reopen it.
        if (pending) {
          ref.current?.showModal();
        } else if (open) {
          onCancel();
        }
      }}
      className="m-auto w-[min(28rem,calc(100%-2rem))] rounded-2xl border border-line bg-surface p-6 text-left shadow-lg backdrop:bg-forest/40"
    >
      <h2 id={`${id}-title`} className="text-lg font-semibold text-forest">
        {confirmation.title}
      </h2>
      {confirmation.message ? (
        <p id={`${id}-message`} className="mt-2 text-sm text-muted">
          {confirmation.message}
        </p>
      ) : null}
      {error ? (
        <div role="alert">
          <FieldError id={`${id}-error`}>{error}</FieldError>
        </div>
      ) : null}
      <div className="mt-6 flex flex-wrap justify-end gap-2">
        {/* First, so it gets the focus: the safe choice is the default. */}
        <button type="button" onClick={onCancel} disabled={pending} className={CANCEL}>
          Cancel
        </button>
        <button type="button" onClick={onConfirm} disabled={pending} className={CONFIRM}>
          {pending ? pendingLabel : confirmLabel}
        </button>
      </div>
    </dialog>
  );
}
