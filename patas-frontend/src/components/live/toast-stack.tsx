"use client";

import Link from "next/link";

import type { Toast } from "@/lib/live-events";

export type ShownToast = Toast & { id: string };

type Props = {
  toasts: readonly ShownToast[];
  onDismiss: (id: string) => void;
};

// The toasts of new messages, in a corner of every page. Screen readers announce them.
export function ToastStack({ toasts, onDismiss }: Props) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="pointer-events-none fixed inset-x-4 bottom-4 z-50 flex flex-col items-end gap-3 sm:left-auto sm:right-6 sm:w-96"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className="pointer-events-auto flex w-full items-start gap-3 rounded-2xl bg-surface p-4 shadow-lg ring-1 ring-line"
        >
          <div className="flex-1">
            <p className="text-sm font-medium text-ink">{toast.text}</p>
            <Link
              href={toast.href}
              onClick={() => onDismiss(toast.id)}
              className="mt-1 inline-block text-sm font-semibold text-leaf underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
            >
              Open conversation
            </Link>
          </div>
          <button
            type="button"
            onClick={() => onDismiss(toast.id)}
            aria-label="Dismiss"
            className="rounded-lg px-2 text-lg leading-none text-muted hover:text-forest focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
