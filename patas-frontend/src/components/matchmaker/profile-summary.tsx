"use client";

import { CircleCheck } from "lucide-react";

import {
  ANSWER_KEYS,
  answeredCount,
  isComplete,
  sentence,
  type AnswerKey,
  type Draft,
} from "@/lib/matchmaker-profile";

// The answer the user just changed. The id grows on every change, so changing the
// same answer twice restarts the highlight.
export type ChangedAnswer = { key: AnswerKey; id: number };

type ProfileSummaryProps = {
  draft: Draft;
  changed: ChangedAnswer | null;
  // Placement in the page grid, decided by whoever hosts the summary.
  className?: string;
};

// Progress and a live sentence. On a phone it is a slim bar (the meter and the count);
// from lg up it is a panel that also reads the answers back as a sentence.
export function ProfileSummary({
  draft,
  changed,
  className,
}: ProfileSummaryProps) {
  const count = answeredCount(draft);
  const total = ANSWER_KEYS.length;

  return (
    <aside
      aria-label="Your profile so far"
      className={`sticky top-0 z-10 border-b border-line bg-background py-3 lg:top-24 lg:rounded-2xl lg:border lg:bg-surface lg:p-6 lg:shadow-sm ${className ?? ""}`}
    >
      <h2 className="mb-3 hidden text-lg font-semibold text-forest lg:block">
        Your profile
      </h2>

      <div className="flex items-center gap-3 lg:flex-col lg:items-stretch lg:gap-2">
        <p
          role="status"
          className="flex shrink-0 items-center gap-1.5 text-sm font-medium text-forest"
        >
          {isComplete(draft) && (
            <CircleCheck aria-hidden="true" className="size-4 text-leaf" />
          )}
          {isComplete(draft)
            ? `All ${total} answered`
            : `${count} of ${total} answered`}
        </p>
        <div aria-hidden="true" className="flex flex-1 gap-1.5">
          {ANSWER_KEYS.map((key) => (
            <span
              key={key}
              className={`h-1.5 flex-1 rounded-full transition-colors duration-200 ease-out-expo motion-reduce:transition-none ${
                draft[key] === null ? "bg-line" : "bg-leaf"
              }`}
            />
          ))}
        </div>
      </div>

      <p className="mt-5 hidden text-base leading-7 text-ink lg:block">
        {sentence(draft).map((segment, index) => {
          if (segment.kind === "text") {
            return <span key={index}>{segment.text}</span>;
          }
          if (segment.text === null) {
            return (
              <span
                key={index}
                className="text-muted underline decoration-dashed underline-offset-4"
              >
                …
              </span>
            );
          }
          const justChanged = changed?.key === segment.key;
          return (
            <span
              key={justChanged ? `${index}-${changed.id}` : index}
              className={`rounded font-semibold text-forest ${
                justChanged
                  ? "animate-phrase-flash motion-reduce:animate-none"
                  : ""
              }`}
            >
              {segment.text}
            </span>
          );
        })}
      </p>
    </aside>
  );
}
