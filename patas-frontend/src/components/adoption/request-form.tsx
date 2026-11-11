"use client";

import { TriangleAlert } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useId, useState, useTransition } from "react";

import { FieldError } from "@/components/matchmaker/field-error";
import {
  NOTE_MAX,
  noteProblem,
  noteProblemMessage,
  type RequestOutcome,
  type RequestProblem,
} from "@/lib/adoption";

type RequestFormProps = {
  animalId: string;
  animalName: string;
  action: (animalId: string, note: string) => Promise<RequestOutcome>;
};

const BUTTON =
  "inline-flex min-h-11 shrink-0 items-center justify-center rounded-xl bg-forest px-5 text-sm font-semibold text-white transition hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-60";
const TEXTAREA =
  "w-full rounded-xl border border-muted/75 bg-surface px-3 py-2.5 text-sm text-forest outline-none transition focus-visible:border-leaf focus-visible:ring-2 focus-visible:ring-leaf/30";

type Failure = { problem: RequestProblem; message: string };

export function RequestForm({ animalId, animalName, action }: RequestFormProps) {
  const router = useRouter();
  const id = useId();
  const [note, setNote] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [failure, setFailure] = useState<Failure | null>(null);
  const [pending, startTransition] = useTransition();

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    // The obvious mistakes are caught here without calling the server. The backend
    // checks the same rules again.
    const problem = noteProblem(note);
    if (problem !== null) {
      setFieldError(noteProblemMessage(problem));
      return;
    }
    setFieldError(null);
    setFailure(null);

    startTransition(async () => {
      const outcome = await action(animalId, note);
      if (outcome.ok) {
        // Nothing to do here: the action revalidated the page, which now shows the
        // request in place of this form.
        return;
      }
      if (outcome.problem === "invalid-note") {
        setFieldError(outcome.message);
        return;
      }
      setFailure({ problem: outcome.problem, message: outcome.message });
      if (
        outcome.problem === "already-requested" ||
        outcome.problem === "not-available"
      ) {
        // The page was out of date: show what is true now.
        router.refresh();
      }
    });
  }

  const trimmedLength = note.trim().length;
  const errorId = `${id}-error`;
  const countId = `${id}-count`;

  return (
    <form onSubmit={submit} noValidate aria-busy={pending}>
      {failure?.problem === "no-profile" ? (
        <div
          role="alert"
          className="mb-4 flex flex-col gap-3 rounded-xl border border-line bg-surface p-4 sm:flex-row sm:items-center sm:justify-between"
        >
          <p className="flex items-start gap-2 text-sm text-forest">
            <TriangleAlert
              aria-hidden="true"
              className="mt-0.5 size-4 shrink-0 text-amber-700"
            />
            {failure.message}
          </p>
          <Link href="/matchmaker" className={BUTTON}>
            Create profile
          </Link>
        </div>
      ) : failure !== null ? (
        <div role="alert">
          <FieldError id={`${id}-failure`}>{failure.message}</FieldError>
        </div>
      ) : null}

      <label
        htmlFor={`${id}-note`}
        className="block text-sm font-medium text-forest"
      >
        Tell the owner about you and your home
      </label>
      <textarea
        id={`${id}-note`}
        name="note"
        rows={5}
        value={note}
        onChange={(event) => setNote(event.target.value)}
        aria-invalid={fieldError !== null}
        aria-describedby={fieldError ? `${countId} ${errorId}` : countId}
        className={`mt-2 ${TEXTAREA}`}
      />
      <div className="mt-1 flex items-start justify-between gap-4">
        <div>
          {fieldError ? <FieldError id={errorId}>{fieldError}</FieldError> : null}
        </div>
        <p
          id={countId}
          className={
            trimmedLength > NOTE_MAX
              ? "text-xs font-medium text-red-700"
              : "text-xs text-muted"
          }
        >
          {trimmedLength} / {NOTE_MAX}
        </p>
      </div>

      <div className="mt-4">
        <button type="submit" disabled={pending} className={BUTTON}>
          {pending ? "Sending..." : `Request to adopt ${animalName}`}
        </button>
      </div>
    </form>
  );
}
