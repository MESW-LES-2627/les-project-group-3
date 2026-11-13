"use client";

import { useId, useState, useTransition } from "react";

import { FieldError } from "@/components/matchmaker/field-error";
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
  const id = useId();
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function handleClick() {
    // Task #58 replaces this with the shared dialog, like the unpublish one.
    if (!window.confirm(withdrawConfirmation(animalName, status))) {
      return;
    }
    setError(null);
    startTransition(async () => {
      const outcome = await action(applicationId, animalId);
      // On success the action revalidated the page, which now shows it withdrawn.
      if (!outcome.ok) {
        setError(outcome.message);
      }
    });
  }

  return (
    <div>
      <button
        type="button"
        onClick={handleClick}
        disabled={pending}
        aria-describedby={error ? `${id}-error` : undefined}
        className="inline-flex items-center justify-center rounded-xl border border-line bg-surface px-3 py-1.5 text-xs font-semibold text-muted transition hover:border-forest hover:text-forest focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-50"
      >
        {pending ? "Withdrawing…" : "Withdraw"}
      </button>
      {error ? (
        <div role="alert">
          <FieldError id={`${id}-error`}>{error}</FieldError>
        </div>
      ) : null}
    </div>
  );
}
