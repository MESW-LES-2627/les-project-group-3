"use client";

import { useState, useTransition } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { withdrawConfirmation, type WithdrawAction } from "@/lib/adoption";

type WithdrawButtonProps = {
  applicationId: string;
  animalId: string;
  animalName: string;
  status: string;
  action: WithdrawAction;
};

export function WithdrawButton({
  applicationId,
  animalId,
  animalName,
  status,
  action,
}: WithdrawButtonProps) {
  const [open, setOpen] = useState(false);
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function handleConfirm() {
    setError(null);
    startTransition(async () => {
      const outcome = await action(applicationId, animalId);
      // On success the action revalidated the page, which now shows it withdrawn.
      if (outcome.ok) {
        setOpen(false);
      } else {
        setError(outcome.message);
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
        Withdraw
      </button>
      <ConfirmDialog
        open={open}
        confirmation={withdrawConfirmation(animalName, status)}
        confirmLabel="Withdraw"
        pendingLabel="Withdrawing…"
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
