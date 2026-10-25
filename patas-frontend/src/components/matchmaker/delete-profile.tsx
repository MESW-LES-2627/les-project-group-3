"use client";

import { Trash2 } from "lucide-react";
import { useState, useTransition } from "react";

import type { DeleteOutcome } from "@/lib/matchmaker-profile";

import { FieldError } from "./field-error";

type DeleteProfileProps = {
  remove: () => Promise<DeleteOutcome>;
  onDeleted: () => void;
};

const BUTTON =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-4 text-sm font-semibold transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-60";

// Deleting needs a second, deliberate step, inline rather than in a dialog.
export function DeleteProfile({ remove, onDeleted }: DeleteProfileProps) {
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function confirmDelete() {
    setError(null);
    startTransition(async () => {
      const result = await remove();
      if (result.ok) {
        onDeleted();
      } else {
        setError(result.error);
      }
    });
  }

  return (
    <section aria-labelledby="delete-heading" className="py-10">
      <h2 id="delete-heading" className="text-xl font-semibold text-forest">
        Delete my profile
      </h2>
      <p className="mt-1 max-w-prose text-sm leading-6 text-muted">
        This removes all your answers. You can fill them in again whenever you
        like.
      </p>
      {confirming ? (
        <div
          role="group"
          aria-label="Confirm deleting your profile"
          onKeyDown={(event) => {
            if (event.key === "Escape") setConfirming(false);
          }}
          className="mt-5 flex flex-wrap items-center gap-3"
        >
          <p className="w-full text-sm font-medium text-forest sm:w-auto">
            Delete your profile?
          </p>
          <button
            type="button"
            autoFocus
            disabled={pending}
            onClick={() => setConfirming(false)}
            className={`${BUTTON} border border-muted/75 text-forest hover:bg-leaf/10`}
          >
            Keep it
          </button>
          <button
            type="button"
            disabled={pending}
            onClick={confirmDelete}
            className={`${BUTTON} bg-red-700 text-white hover:bg-red-800`}
          >
            {pending ? "Deleting…" : "Yes, delete"}
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setConfirming(true)}
          className={`${BUTTON} mt-5 border border-red-700 text-red-700 hover:bg-red-700 hover:text-white`}
        >
          <Trash2 aria-hidden="true" className="size-4" />
          Delete my profile
        </button>
      )}
      {error && <FieldError id="delete-error">{error}</FieldError>}
    </section>
  );
}
