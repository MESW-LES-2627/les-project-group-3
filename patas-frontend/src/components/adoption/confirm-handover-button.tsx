"use client";

import { startTransition, useActionState } from "react";

import type {
  ConfirmHandoverAction,
  ConfirmHandoverOutcome,
} from "@/lib/adoption";

type ConfirmHandoverButtonProps = {
  applicationId: string;
  animalId: string;
  otherSideConfirmed: boolean;
  action: ConfirmHandoverAction;
};

const initialState: ConfirmHandoverOutcome | null = null;

export function ConfirmHandoverButton({
  applicationId,
  animalId,
  otherSideConfirmed,
  action,
}: ConfirmHandoverButtonProps) {
  const [state, runAction, pending] = useActionState(
    async () => action(applicationId, animalId),
    initialState,
  );

  function handleClick() {
    startTransition(() => {
      runAction();
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
      {state && !state.ok && (
        <p role="alert" className="text-sm font-medium text-red-700">
          {state.message}
        </p>
      )}
      <button
        type="button"
        onClick={handleClick}
        disabled={pending}
        className="inline-flex min-h-11 items-center justify-center rounded-xl bg-forest px-5 text-sm font-semibold text-white transition hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-60"
      >
        {pending ? "Confirming..." : "Confirm handover"}
      </button>
    </div>
  );
}
