"use client";

import { CircleAlert } from "lucide-react";
import Link from "next/link";
import { useState, useTransition } from "react";

import {
  DEFAULT_MODE,
  MODE_LABEL,
  MODES,
  groupReasons,
  type Fit,
  type FitOutcome,
  type Mode,
} from "@/lib/compatibility";

type FitCardProps = {
  animalId: string;
  animalName: string;
  action: (animalId: string, mode: Mode) => Promise<FitOutcome>;
};

const BUTTON =
  "inline-flex min-h-11 items-center justify-center rounded-xl bg-forest px-5 text-sm font-semibold text-white transition hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-60";

// The reason groups carry their meaning in the heading, not in colour alone.
const GROUP_STYLE = {
  strength: "border-leaf",
  concern: "border-sunlight",
  unknown: "border-line",
} as const;

export function FitCard({ animalId, animalName, action }: FitCardProps) {
  const [mode, setMode] = useState<Mode>(DEFAULT_MODE);
  const [outcome, setOutcome] = useState<FitOutcome | null>(null);
  const [pending, startTransition] = useTransition();

  // The first press and a change of mode are the same request: ask the backend again
  // and replace whatever was shown. Nothing is stored.
  function calculate(next: Mode) {
    setMode(next);
    startTransition(async () => {
      setOutcome(await action(animalId, next));
    });
  }

  return (
    <section
      aria-labelledby="fit-heading"
      className="rounded-2xl border border-line bg-surface p-6 shadow-sm sm:p-8"
    >
      <h2 id="fit-heading" className="text-xl font-semibold text-forest">
        How well does {animalName} fit your home?
      </h2>
      <p className="mt-1 text-sm text-muted">
        We compare your Matchmaker profile with what the owner told us. It is a
        guide, not a decision.
      </p>

      {outcome?.ok ? (
        <ModeSwitch mode={mode} pending={pending} onChange={calculate} />
      ) : (
        <button
          type="button"
          className={`${BUTTON} mt-5`}
          disabled={pending}
          onClick={() => calculate(mode)}
        >
          {pending
            ? "Calculating…"
            : outcome
              ? "Try again"
              : "Calculate my fit"}
        </button>
      )}

      <div aria-live="polite" className="mt-6">
        {outcome?.ok && <Result fit={outcome.fit} />}
        {outcome && !outcome.ok && (
          <p className="flex items-start gap-1.5 text-sm font-medium text-red-700">
            <CircleAlert aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
            <span>
              {outcome.message}{" "}
              {outcome.problem === "no-profile" && (
                <Link href="/matchmaker" className="underline">
                  Go to my profile
                </Link>
              )}
            </span>
          </p>
        )}
      </div>
    </section>
  );
}

function ModeSwitch({
  mode,
  pending,
  onChange,
}: {
  mode: Mode;
  pending: boolean;
  onChange: (mode: Mode) => void;
}) {
  return (
    <div role="group" aria-label="How strict the match is" className="mt-5 flex gap-2">
      {MODES.map((option) => (
        <button
          key={option}
          type="button"
          aria-pressed={mode === option}
          disabled={pending}
          onClick={() => option !== mode && onChange(option)}
          className={`inline-flex min-h-11 items-center rounded-xl border px-4 text-sm font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-60 ${
            mode === option
              ? "border-forest bg-forest text-white"
              : "border-line bg-surface text-forest hover:border-leaf"
          }`}
        >
          {MODE_LABEL[option]}
        </button>
      ))}
    </div>
  );
}

function Result({ fit }: { fit: Fit }) {
  const groups = groupReasons(fit.reasons);
  return (
    <div className="space-y-5">
      {fit.is_compatible ? (
        <p className="text-forest">
          <span className="text-4xl font-bold">{fit.score}</span>
          <span className="text-sm text-muted"> out of 100</span>
          <span className="ml-2 text-xs font-medium text-muted">
            {MODE_LABEL[fit.mode]} match
          </span>
        </p>
      ) : (
        <p className="flex items-center gap-1.5 text-lg font-semibold text-red-700">
          <CircleAlert aria-hidden="true" className="size-5 shrink-0" />
          Not suitable for your home
        </p>
      )}
      {groups.map(({ kind, heading, texts }) => (
        <div key={kind} className={`border-l-4 pl-4 ${GROUP_STYLE[kind]}`}>
          <h3 className="text-sm font-semibold text-forest">{heading}</h3>
          <ul className="mt-1 space-y-1 text-sm text-muted">
            {texts.map((text) => (
              <li key={text}>{text}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
