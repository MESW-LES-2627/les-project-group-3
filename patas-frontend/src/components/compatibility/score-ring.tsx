import type { CSSProperties } from "react";

const SIZE = 84;
const STROKE = 8;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

// The score as a ring that fills clockwise from 12 o'clock.
export function ScoreRing({ score }: { score: number }) {
  // How much of the ring is left empty: none at 100 points, all of it at 0.
  const offset = CIRCUMFERENCE * (1 - score / 100);

  return (
    <div
      role="img"
      aria-label={`${score} out of 100`}
      className="relative size-21 shrink-0"
    >
      <svg
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        aria-hidden="true"
        className="size-full -rotate-90"
      >
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          strokeWidth={STROKE}
          className="stroke-line"
        />
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          strokeWidth={STROKE}
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
          style={{ "--ring-empty": CIRCUMFERENCE } as CSSProperties}
          className="stroke-leaf transition-[stroke-dashoffset] duration-700 ease-out-expo motion-safe:animate-ring-fill motion-reduce:transition-none"
        />
      </svg>
      <span
        aria-hidden="true"
        className="absolute inset-0 grid place-items-center font-mono text-2xl font-semibold tabular-nums text-forest"
      >
        {score}
      </span>
    </div>
  );
}
