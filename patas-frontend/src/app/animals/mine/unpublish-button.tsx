"use client";

import { useTransition } from "react";
import { unpublishAnimalAction } from "./actions";

export function UnpublishButton({
  animalId,
  animalName,
}: {
  animalId: string;
  animalName: string;
}) {
  const [isPending, startTransition] = useTransition();

  const handleUnpublish = () => {
    if (confirm(`Are you sure you want to unpublish ${animalName}? It will no longer appear in the catalog.`)) {
      startTransition(async () => {
        const result = await unpublishAnimalAction(animalId);
        if (result?.error) {
          alert(result.error);
        }
      });
    }
  };

  return (
    <button
      type="button"
      onClick={handleUnpublish}
      disabled={isPending}
      className="inline-flex items-center justify-center rounded-xl border border-line bg-surface px-3 py-1.5 text-xs font-semibold text-muted transition hover:border-forest hover:text-forest focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-50"
    >
      {isPending ? "Unpublishing…" : "Unpublish"}
    </button>
  );
}
