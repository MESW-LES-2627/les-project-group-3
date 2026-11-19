"use client";

import { useId, useState, useTransition } from "react";

import { FieldError } from "@/components/matchmaker/field-error";
import { republishAnimalAction } from "./actions";

// No confirmation: republishing is harmless and can be undone by unpublishing.
export function RepublishButton({ animalId }: { animalId: string }) {
  const id = useId();
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const handleRepublish = () => {
    setError(null);
    startTransition(async () => {
      const result = await republishAnimalAction(animalId);
      if (result?.error) {
        setError(result.error);
      }
    });
  };

  return (
    <div>
      <button
        type="button"
        onClick={handleRepublish}
        disabled={isPending}
        aria-describedby={error ? `${id}-error` : undefined}
        className="inline-flex items-center justify-center rounded-xl border border-line bg-surface px-3 py-1.5 text-xs font-semibold text-muted transition hover:border-forest hover:text-forest focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-50"
      >
        {isPending ? "Republishing…" : "Republish"}
      </button>
      {error ? (
        <div role="alert">
          <FieldError id={`${id}-error`}>{error}</FieldError>
        </div>
      ) : null}
    </div>
  );
}
