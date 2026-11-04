"use client";

import {
  Check,
  CircleAlert,
  CircleQuestionMark,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { useState, useTransition } from "react";

import {
  DEFAULT_MODE,
  MODE_HINT,
  MODE_LABEL,
  MODES,
  TALLY_LABEL,
  groupReasons,
  type Fit,
  type FitOutcome,
  type Mode,
  type ReasonKind,
} from "@/lib/compatibility";

import { ScoreRing } from "./score-ring";

type FitCardProps = {
  animalId: string;
  animalName: string;
  action: (animalId: string, mode: Mode) => Promise<FitOutcome>;
};

const BUTTON =
  "inline-flex min-h-11 shrink-0 items-center justify-center rounded-xl bg-forest px-5 text-sm font-semibold text-white transition hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-60";

const STAGGER_MS = 40;
const STAGGER_CAP = 8;

// Each kind has an icon, a colour and a hidden text label, so its meaning never
// rests on colour alone.
const KIND_STYLE: Record<
  ReasonKind,
  { Icon: LucideIcon; icon: string; dot: string }
> = {
  strength: { Icon: Check, icon: "text-leaf", dot: "bg-leaf" },
  concern: { Icon: TriangleAlert, icon: "text-amber-700", dot: "bg-sunlight" },
  unknown: { Icon: CircleQuestionMark, icon: "text-muted", dot: "bg-line" },
};

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

  // While a mode change loads, the last result stays on screen, dimmed. Only the
  // first press (or a retry after an error) has nothing to show yet.
  const fit = outcome?.ok ? outcome.fit : null;

  return (
    <section aria-labelledby="fit-heading">
      {!fit && (
        <div className="flex flex-col gap-4 rounded-xl bg-leaf-tint p-4 sm:flex-row sm:items-center sm:justify-between sm:pl-5">
          <div>
            <h2 id="fit-heading" className="font-semibold text-forest">
              How well does {animalName} fit your home?
            </h2>
            <p className="mt-0.5 text-sm text-muted">
              We compare your Matchmaker profile with what the owner told us.
            </p>
          </div>
          <button
            type="button"
            className={BUTTON}
            disabled={pending}
            onClick={() => calculate(mode)}
          >
            {pending
              ? "Calculating…"
              : outcome
                ? "Try again"
                : "Calculate my fit"}
          </button>
        </div>
      )}

      <div aria-live="polite">
        {fit && (
          <Result
            fit={fit}
            animalName={animalName}
            mode={mode}
            pending={pending}
            onModeChange={calculate}
          />
        )}
        {outcome && !outcome.ok && (
          <p className="mt-4 flex items-start gap-1.5 text-sm font-medium text-red-700">
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

function Result({
  fit,
  animalName,
  mode,
  pending,
  onModeChange,
}: {
  fit: Fit;
  animalName: string;
  mode: Mode;
  pending: boolean;
  onModeChange: (mode: Mode) => void;
}) {
  const groups = groupReasons(fit.reasons);
  // One list in group order, so each reason knows its place for the stagger.
  const reasons = groups.flatMap(({ kind, heading, texts }) =>
    texts.map((text) => ({ kind, heading, text })),
  );

  return (
    <div
      aria-busy={pending}
      className={`flex flex-col gap-5 transition-opacity motion-safe:animate-rise-in motion-reduce:transition-none ${pending ? "opacity-60" : ""}`}
    >
      <div className="flex flex-wrap items-center gap-x-5 gap-y-4">
        {fit.is_compatible ? (
          <>
            <ScoreRing score={fit.score} />
            <div className="min-w-0 flex-1">
              <h2 id="fit-heading" className="font-semibold text-forest">
                Your fit with {animalName}
              </h2>
              <p className="mt-1 flex flex-wrap gap-x-3.5 gap-y-1 text-sm text-muted">
                {groups.map(({ kind, texts }) => (
                  <span key={kind} className="inline-flex items-center gap-1.5">
                    <span
                      aria-hidden="true"
                      className={`size-2 rounded-full ${KIND_STYLE[kind].dot}`}
                    />
                    {texts.length} {TALLY_LABEL[kind]}
                  </span>
                ))}
              </p>
              <p className="mt-1 text-xs text-muted">{MODE_HINT[fit.mode]}</p>
            </div>
          </>
        ) : (
          <div className="flex min-w-0 flex-1 items-center gap-3 rounded-xl bg-red-50 px-4 py-3.5 text-red-700">
            <CircleAlert aria-hidden="true" className="size-5 shrink-0" />
            <h2 id="fit-heading" className="font-semibold">
              Not suitable for your home
            </h2>
          </div>
        )}
        <ModeSwitch mode={mode} pending={pending} onChange={onModeChange} />
      </div>

      <ul className="grid gap-x-7 gap-y-2.5 text-sm text-forest sm:grid-cols-2">
        {reasons.map(({ kind, heading, text }, index) => {
          const { Icon, icon } = KIND_STYLE[kind];
          return (
            <li
              key={`${kind}-${text}`}
              // Each reason arrives a little after the one before; capped so a long
              // list is still done in well under a second.
              style={{ animationDelay: `${Math.min(index, STAGGER_CAP) * STAGGER_MS}ms` }}
              className="flex items-start gap-2.5 motion-safe:animate-rise-in"
            >
              <Icon
                aria-hidden="true"
                strokeWidth={2.25}
                className={`mt-0.5 size-4 shrink-0 ${icon}`}
              />
              <span>
                <span className="sr-only">{heading}: </span>
                {text}
              </span>
            </li>
          );
        })}
      </ul>

      <p className="text-xs text-muted">A guide, not a decision.</p>
    </div>
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
    <div
      role="group"
      aria-label="How strict the match is"
      className="relative grid grid-cols-2 rounded-full border border-line bg-background p-0.5"
    >
      {/* One white thumb behind the buttons, slid to the selected column. The
          columns are equal, so one column is 100% of the thumb's own width. */}
      <span
        aria-hidden="true"
        style={{ transform: `translateX(${MODES.indexOf(mode) * 100}%)` }}
        className="absolute inset-y-0.5 left-0.5 w-[calc(50%-0.125rem)] rounded-full bg-surface shadow-sm transition-transform duration-300 ease-out-expo motion-reduce:transition-none"
      />
      {MODES.map((option) => (
        <button
          key={option}
          type="button"
          aria-pressed={mode === option}
          disabled={pending}
          onClick={() => option !== mode && onChange(option)}
          className={`relative min-h-9 rounded-full px-3.5 text-sm font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:cursor-wait ${
            mode === option ? "text-forest" : "text-muted hover:text-forest"
          }`}
        >
          {MODE_LABEL[option]}
        </button>
      ))}
    </div>
  );
}
