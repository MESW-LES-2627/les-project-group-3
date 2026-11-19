"use client";

import { Heart, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState, useTransition } from "react";

import { RequestForm } from "@/components/adoption/request-form";
import { districtLabel } from "@/lib/animal-profile";
import type { RequestOutcome } from "@/lib/adoption";
import type { SwipeAnimal, SwipeOutcome } from "@/lib/matchmaker-swipes";

type Props = {
  initialAnimals: SwipeAnimal[];
  remove: (animalId: string) => Promise<SwipeOutcome>;
  request: (animalId: string, note: string) => Promise<RequestOutcome>;
};

const REMOVE_BUTTON =
  "inline-flex min-h-10 items-center justify-center gap-2 rounded-lg border border-line px-3 text-sm font-medium text-forest transition hover:bg-background focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-60";

export function MatchmakerSavedList({ initialAnimals, remove, request }: Props) {
  const [animals, setAnimals] = useState(initialAnimals);
  const [requested, setRequested] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function unsave(animalId: string) {
    setError(null);
    startTransition(async () => {
      const result = await remove(animalId);
      if (!result.ok) {
        setError(result.message);
        return;
      }
      setAnimals((current) => current.filter((animal) => animal.id !== animalId));
    });
  }

  if (animals.length === 0) {
    return (
      <section className="rounded-2xl border border-dashed border-line bg-surface px-6 py-12 text-center">
        <Heart aria-hidden="true" className="mx-auto size-8 text-leaf" />
        <h2 className="mt-3 text-xl font-semibold text-forest">
          No saved animals yet
        </h2>
        <p className="mt-2 text-sm text-muted">
          Save an animal while swiping and it will be waiting here.
        </p>
        <Link
          href="/matchmaker?tab=swipe"
          className="mt-5 inline-flex min-h-11 items-center rounded-xl bg-forest px-5 text-sm font-semibold text-white hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
        >
          Browse animals
        </Link>
      </section>
    );
  }

  return (
    <section aria-label="Saved animals" aria-busy={pending}>
      {error && (
        <p role="alert" className="mb-4 text-sm text-red-700">
          {error}
        </p>
      )}
      <ul className="grid gap-5 lg:grid-cols-2">
        {animals.map((animal) => (
          <li
            key={animal.id}
            className="rounded-2xl border border-line bg-surface p-5 shadow-sm"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-leaf">
                  {animal.species}
                </p>
                <h2 className="mt-1 text-2xl font-semibold text-forest">
                  <Link href={`/animals/${animal.id}`} className="hover:underline">
                    {animal.name}
                  </Link>
                </h2>
                <p className="mt-1 text-sm text-muted">
                  Published by {animal.owner_name}
                </p>
              </div>
              <button
                type="button"
                disabled={pending}
                onClick={() => unsave(animal.id)}
                className={REMOVE_BUTTON}
              >
                <Trash2 aria-hidden="true" className="size-4" />
                Remove
              </button>
            </div>
            <p className="mt-4 text-sm text-muted">
              {animal.age_in_months === null
                ? "Age not listed"
                : `${animal.age_in_months} months`}
              {" · "}
              {animal.district ? districtLabel(animal.district) : "District not listed"}
            </p>
            {animal.fit && (
              <div className="mt-4 rounded-xl bg-leaf-tint p-4">
                <p className="font-semibold text-forest">
                  {animal.fit.is_compatible
                    ? `${animal.fit.score} fit score`
                    : "Not suitable for your home"}
                </p>
                <ul className="mt-2 space-y-1 text-sm text-muted">
                  {animal.fit.reasons.map((reason, index) => (
                    <li key={`${reason.kind}-${index}`}>{reason.text}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="mt-5 border-t border-line pt-5">
              {requested.includes(animal.id) ? (
                <p role="status" className="text-sm font-medium text-forest">
                  Your adoption request has been sent.
                </p>
              ) : (
                <RequestForm
                  animalId={animal.id}
                  animalName={animal.name}
                  action={request}
                  onSuccess={() =>
                    setRequested((current) => [...current, animal.id])
                  }
                />
              )}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
