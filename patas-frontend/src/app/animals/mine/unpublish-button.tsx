"use client";

import { useState, useTransition } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { unpublishConfirmation } from "@/lib/confirmation";
import { unpublishAnimalAction } from "./actions";

export function UnpublishButton({
  animalId,
  animalName,
}: {
  animalId: string;
  animalName: string;
}) {
  const [open, setOpen] = useState(false);
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function handleConfirm() {
    setError(null);
    startTransition(async () => {
      const result = await unpublishAnimalAction(animalId);
      if (result?.error) {
        setError(result.error);
      } else {
        setOpen(false);
      }
    });
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        disabled={pending}
        className="inline-flex items-center justify-center rounded-xl border border-line bg-surface px-3 py-1.5 text-xs font-semibold text-muted transition hover:border-forest hover:text-forest focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-50"
      >
        Unpublish
      </button>
      <ConfirmDialog
        open={open}
        confirmation={unpublishConfirmation(animalName)}
        confirmLabel="Unpublish"
        pendingLabel="Unpublishing…"
        pending={pending}
        error={error}
        onConfirm={handleConfirm}
        onCancel={() => {
          setOpen(false);
          setError(null);
        }}
      />
    </>
  );
}
