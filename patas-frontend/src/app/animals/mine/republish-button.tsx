"use client";

import { useTransition } from "react";
import { republishAnimalAction } from "./actions";

// No confirmation: republishing is harmless and can be undone by unpublishing.
export function RepublishButton({ animalId }: { animalId: string }) {
  const [isPending, startTransition] = useTransition();

  const handleRepublish = () => {
    startTransition(async () => {
      const result = await republishAnimalAction(animalId);
      if (result?.error) {
        alert(result.error);
      }
    });
  };

  return (
    <button
      type="button"
      onClick={handleRepublish}
      disabled={isPending}
      className="inline-flex items-center justify-center rounded-xl border border-line bg-surface px-3 py-1.5 text-xs font-semibold text-muted transition hover:border-forest hover:text-forest focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-50"
    >
      {isPending ? "Republishing…" : "Republish"}
    </button>
  );
}
