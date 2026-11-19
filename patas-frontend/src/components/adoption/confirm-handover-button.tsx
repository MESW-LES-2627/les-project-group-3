"use client";

import { useState, useTransition } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import {
  handoverConfirmation,
  type ConfirmHandoverAction,
} from "@/lib/adoption";

type ConfirmHandoverButtonProps = {
  applicationId: string;
  animalId: string;
  animalName: string;
  otherSideConfirmed: boolean;
  action: ConfirmHandoverAction;
};

export function ConfirmHandoverButton({
  applicationId,
  animalId,
  animalName,
  otherSideConfirmed,
  action,
}: ConfirmHandoverButtonProps) {
  const [open, setOpen] = useState(false);
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function handleConfirm() {
    setError(null);
    startTransition(async () => {
      const outcome = await action(applicationId, animalId);
      // On success the action revalidated the page, which now shows the new state.
      if (outcome.ok) {
        setOpen(false);
      } else {
        setError(outcome.message);
      }
    });
  }

  return (
    <div className="flex flex-col items-start gap-2">
      {otherSideConfirmed && (
        <p className="text-sm font-medium text-leaf">
          The other side has confirmed the handover. Confirm to complete the
          adoption.
        </p>
      )}
      <button
        type="button"
        onClick={() => setOpen(true)}
        disabled={pending}
        className="inline-flex min-h-11 items-center justify-center rounded-xl bg-forest px-5 text-sm font-semibold text-white transition hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-60"
      >
        Confirm handover
      </button>
      <ConfirmDialog
        open={open}
        confirmation={handoverConfirmation(animalName, otherSideConfirmed)}
        confirmLabel="Confirm handover"
        pendingLabel="Confirming…"
        pending={pending}
        error={error}
        onConfirm={handleConfirm}
        onCancel={() => {
          setOpen(false);
          setError(null);
        }}
      />
    </div>
  );
}
