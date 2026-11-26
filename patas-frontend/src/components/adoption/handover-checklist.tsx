"use client";

import { useState, useTransition } from "react";

import type { TickAction } from "@/lib/adoption";
import {
  BASIS_LABEL,
  HANDOVER_CHECKLIST,
  HANDOVER_DISCLAIMER,
  HANDOVER_ITEM_KEYS,
  checkedCount,
  type HandoverItemKey,
} from "@/lib/handover-checklist";

type HandoverChecklistProps = {
  applicationId: string;
  // What the backend says is ticked, read when the page was rendered.
  checked: readonly string[];
  editable: boolean;
  action: TickAction;
  // False where something around it already collapses (the conversation's side panel).
  collapsible?: boolean;
};

// Ticks are shared by both sides and saved by the backend (US-25, ADR 0028). The
// checklist never blocks the handover.
export function HandoverChecklist({
  applicationId,
  checked,
  editable,
  action,
  collapsible = true,
}: HandoverChecklistProps) {
  const [pendingKey, setPendingKey] = useState<HandoverItemKey | null>(null);
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function toggle(key: HandoverItemKey, next: boolean) {
    setError(null);
    setPendingKey(key);
    startTransition(async () => {
      const outcome = await action(applicationId, key, next);
      // On success the action revalidated the page, which now shows the new ticks.
      if (!outcome.ok) {
        setError(outcome.message);
      }
      setPendingKey(null);
    });
  }

  const summary = `Handover checklist: ${checkedCount(checked)} of ${HANDOVER_ITEM_KEYS.length} done`;
  const body = (
    <>
      <p className="mt-3 text-sm text-muted">
        {editable
          ? "You can confirm the handover without ticking everything."
          : "The adoption is complete: the checklist can no longer be changed."}
      </p>
      <ul className="mt-3 grid gap-4 text-sm text-forest">
        {HANDOVER_CHECKLIST.map((item) => (
          <li key={item.key}>
            <label className="flex items-start gap-3 font-semibold">
              <input
                type="checkbox"
                checked={checked.includes(item.key)}
                disabled={!editable || (pending && pendingKey === item.key)}
                onChange={(event) => toggle(item.key, event.target.checked)}
                className="mt-1 size-4 accent-forest"
              />
              {item.title}
            </label>
            <div className="mt-1 grid gap-1 pl-7 text-muted">
              <p className="text-xs font-semibold uppercase tracking-wide">
                {BASIS_LABEL[item.basis]}
              </p>
              {item.rule ? <p>{item.rule}</p> : null}
              <ul className="grid list-disc gap-1 pl-4">
                {item.steps.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ul>
            </div>
          </li>
        ))}
      </ul>
      {error ? (
        <p role="alert" className="mt-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}
      <p className="mt-4 text-xs text-muted">{HANDOVER_DISCLAIMER}</p>
    </>
  );

  if (!collapsible) {
    return (
      <div>
        <p className="text-sm font-semibold text-forest">{summary}</p>
        {body}
      </div>
    );
  }
  return (
    <details open className="rounded-xl bg-leaf/5 p-4">
      <summary className="cursor-pointer text-sm font-semibold text-forest focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest">
        {summary}
      </summary>
      {body}
    </details>
  );
}
