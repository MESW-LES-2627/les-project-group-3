"use client";

import { Heart, X } from "lucide-react";
import Link from "next/link";
import { useRef, useState, useTransition } from "react";

import { districtLabel } from "@/lib/animal-profile";
import { personLabel } from "@/lib/username";
import {
  SWIPE_MESSAGES,
  type SwipeAnimal,
  type SwipeDisposition,
  type SwipeFeedOutcome,
  type SwipeOutcome,
} from "@/lib/matchmaker-swipes";

type Props = {
  initialAnimals: SwipeAnimal[];
  loadMore: () => Promise<SwipeFeedOutcome>;
  swipe: (animalId: string, disposition: SwipeDisposition) => Promise<SwipeOutcome>;
};

const ACTION_BUTTON =
  "inline-flex min-h-12 items-center justify-center gap-2 rounded-xl px-5 text-sm font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:cursor-wait disabled:opacity-60";
const CARD_FADE_DURATION_MS = 200;

export function MatchmakerSwipeFeed({ initialAnimals, loadMore, swipe }: Props) {
  const [animals, setAnimals] = useState(initialAnimals);
  const [index, setIndex] = useState(0);
  const [dragX, setDragX] = useState(0);
  const [leaving, setLeaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const pointer = useRef<{ id: number; x: number } | null>(null);
  const current = animals[index];

  function decide(disposition: SwipeDisposition) {
    if (!current || pending) return;
    const swiped = current;
    setError(null);
    setDragX(0);
    pointer.current = null;
    startTransition(async () => {
      const result = await swipe(swiped.id, disposition);
      if (!result.ok) {
        setError(result.message);
        return;
      }
      setLeaving(true);
      await new Promise((resolve) =>
        setTimeout(resolve, CARD_FADE_DURATION_MS),
      );
      if (index + 1 < animals.length) {
        setIndex(index + 1);
        setLeaving(false);
        return;
      }
      const next = await loadMore();
      if (!next.ok) {
        setError(next.message);
        setAnimals([]);
        setIndex(0);
        setLeaving(false);
        return;
      }
      setAnimals(next.animals);
      setIndex(0);
      setLeaving(false);
    });
  }

  function onPointerDown(event: React.PointerEvent<HTMLElement>) {
    if (
      pending ||
      event.button !== 0 ||
      (event.target instanceof HTMLElement &&
        event.target.closest("button, a") !== null)
    ) {
      return;
    }
    pointer.current = { id: event.pointerId, x: event.clientX };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function onPointerMove(event: React.PointerEvent<HTMLElement>) {
    if (pointer.current?.id === event.pointerId) {
      setDragX(event.clientX - pointer.current.x);
    }
  }

  function onPointerUp(event: React.PointerEvent<HTMLElement>) {
    if (pointer.current?.id !== event.pointerId) return;
    const distance = event.clientX - pointer.current.x;
    pointer.current = null;
    if (distance > 90) {
      decide("saved");
    } else if (distance < -90) {
      decide("passed");
    } else {
      setDragX(0);
    }
  }

  if (!current) {
    return (
      <section
        aria-live="polite"
        className="rounded-2xl border border-dashed border-line bg-surface px-6 py-12 text-center"
      >
        <h2 className="text-xl font-semibold text-forest">
          You&apos;re all caught up
        </h2>
        <p className="mt-2 text-sm leading-6 text-muted">
          There are no more animals in this sample. Your passes and saves stay
          out of future swipes.
        </p>
        {error && <p role="alert" className="mt-4 text-sm text-red-700">{error}</p>}
      </section>
    );
  }

  const fit = current.fit;
  const rotation = Math.max(-12, Math.min(12, dragX / 18));

  return (
    <section aria-label="Swipe animals" aria-busy={pending}>
      <p className="mb-4 text-sm text-muted">
        Swipe right to save, or left to pass. You can also use the buttons.
      </p>
      <article
        key={current.id}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={() => {
          pointer.current = null;
          setDragX(0);
        }}
        style={{
          transform: `translateX(${dragX}px) rotate(${rotation}deg)`,
          touchAction: "pan-y",
        }}
        className={`mx-auto max-w-xl cursor-grab select-none rounded-3xl border border-line bg-surface p-6 shadow-lg transition-opacity transition-transform duration-200 motion-reduce:transition-none motion-safe:animate-rise-in sm:p-8 active:cursor-grabbing ${
          leaving ? "opacity-0" : "opacity-100"
        }`}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-leaf">
              {current.species}
            </p>
            <h2 className="mt-2 text-3xl font-semibold text-forest">
              <Link
                href={`/animals/${current.id}`}
                className="rounded-sm hover:underline focus-visible:outline-2 focus-visible:outline-forest"
                onPointerDown={(event) => event.stopPropagation()}
              >
                {current.name}
              </Link>
            </h2>
            <p className="mt-1 text-sm text-muted">
              Published by {personLabel(current.owner_name, current.owner_username)}
            </p>
          </div>
          {fit && (
            <div className="shrink-0 rounded-2xl bg-leaf-tint px-4 py-3 text-center">
              <p className="text-2xl font-bold text-forest">{fit.score}</p>
              <p className="text-xs font-medium text-muted">fit score</p>
            </div>
          )}
        </div>

        <dl className="mt-6 grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-xl bg-background p-3">
            <dt className="text-xs text-muted">Age</dt>
            <dd className="mt-1 font-medium text-forest">
              {current.age_in_months === null
                ? "Not listed"
                : `${current.age_in_months} months`}
            </dd>
          </div>
          <div className="rounded-xl bg-background p-3">
            <dt className="text-xs text-muted">District</dt>
            <dd className="mt-1 font-medium text-forest">
              {current.district ? districtLabel(current.district) : "Not listed"}
            </dd>
          </div>
        </dl>

        {fit && (
          <div className="mt-6">
            <p
              className={
                fit.is_compatible
                  ? "font-semibold text-forest"
                  : "font-semibold text-amber-800"
              }
            >
              {fit.is_compatible
                ? "Looks like a fit"
                : "Not suitable for your home"}
            </p>
            <ul className="mt-2 space-y-2 text-sm leading-5 text-muted">
              {fit.reasons.map((reason, reasonIndex) => (
                <li key={`${reason.kind}-${reasonIndex}`} className="flex gap-2">
                  <span aria-hidden="true" className="text-leaf">•</span>
                  {reason.text}
                </li>
              ))}
            </ul>
          </div>
        )}
      </article>

      <div className="mx-auto mt-5 flex max-w-xl justify-center gap-4">
        <button
          type="button"
          disabled={pending}
          aria-label={`Pass on ${current.name}`}
          onClick={() => decide("passed")}
          className={`${ACTION_BUTTON} border border-line bg-surface text-forest hover:bg-background`}
        >
          <X aria-hidden="true" className="size-5" />
          Pass
        </button>
        <button
          type="button"
          disabled={pending}
          aria-label={`Save ${current.name}`}
          onClick={() => decide("saved")}
          className={`${ACTION_BUTTON} bg-forest text-white hover:bg-leaf`}
        >
          <Heart aria-hidden="true" className="size-5" />
          Save
        </button>
      </div>
      {error && (
        <p role="alert" className="mx-auto mt-4 max-w-xl text-sm text-red-700">
          {error}
          {error === SWIPE_MESSAGES["no-profile"] && (
            <>
              {" "}
              <Link href="/matchmaker?tab=profile" className="underline">
                Create your profile
              </Link>
            </>
          )}
        </p>
      )}
    </section>
  );
}
