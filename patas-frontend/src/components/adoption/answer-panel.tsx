"use client";

import { useEffect, useId, useRef, useState, useTransition } from "react";

import { FieldError } from "@/components/matchmaker/field-error";
import {
  ANSWER_MESSAGES,
  NOTE_MAX,
  answerNoteProblem,
  answersAvailable,
  type AnswerAction,
  type OwnerAnswer,
} from "@/lib/adoption";

type AnswerPanelProps = {
  applicationId: string;
  animalId: string;
  status: string;
  action: AnswerAction;
};

const PRIMARY =
  "inline-flex min-h-11 items-center justify-center rounded-xl bg-forest px-5 text-sm font-semibold text-white transition hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-60";
const SECONDARY =
  "inline-flex min-h-11 items-center justify-center rounded-xl border border-line bg-surface px-5 text-sm font-semibold text-muted transition hover:border-forest hover:text-forest focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-60";
const TEXTAREA =
  "w-full rounded-xl border border-muted/75 bg-surface px-3 py-2.5 text-sm text-forest outline-none transition focus-visible:border-leaf focus-visible:ring-2 focus-visible:ring-leaf/30";

const BUTTON_LABEL: Record<OwnerAnswer, string> = {
  accept: "Accept",
  decline: "Decline",
};

const COPY: Record<
  OwnerAnswer,
  { question: string; confirm: string; pending: string }
> = {
  accept: {
    question: "Accept this request?",
    confirm: "Confirm accept",
    pending: "Accepting…",
  },
  decline: {
    question: "Decline this request?",
    confirm: "Confirm decline",
    pending: "Declining…",
  },
};

export function AnswerPanel({
  applicationId,
  animalId,
  status,
  action,
}: AnswerPanelProps) {
  const id = useId();
  const [choice, setChoice] = useState<OwnerAnswer | null>(null);
  const [note, setNote] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const noteRef = useRef<HTMLTextAreaElement>(null);
  const firstButtonRef = useRef<HTMLButtonElement>(null);
  const wasOpen = useRef(false);

  // Opening the panel moves focus to the note; closing it gives focus back to the
  // buttons, so a keyboard user does not lose their place.
  useEffect(() => {
    if (choice !== null) {
      wasOpen.current = true;
      noteRef.current?.focus();
    } else if (wasOpen.current) {
      wasOpen.current = false;
      firstButtonRef.current?.focus();
    }
  }, [choice]);

  const answers = answersAvailable(status);
  if (answers.length === 0) {
    return null;
  }

  function cancel() {
    setChoice(null);
    setNote("");
    setFieldError(null);
    setFailure(null);
  }

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (choice === null) {
      return;
    }
    // The obvious mistake is caught here without calling the server. The backend
    // checks the same rule again.
    if (answerNoteProblem(note) !== null) {
      setFieldError(ANSWER_MESSAGES["invalid-note"]);
      return;
    }
    setFieldError(null);
    setFailure(null);

    startTransition(async () => {
      const outcome = await action(applicationId, animalId, choice, note);
      if (outcome.ok) {
        // The action revalidated the page: the card now shows the new status.
        cancel();
        return;
      }
      if (outcome.problem === "invalid-note") {
        setFieldError(outcome.message);
        return;
      }
      // The panel stays open, so the owner sees why, for example that the animal
      // is already reserved for another request.
      setFailure(outcome.message);
    });
  }

  if (choice === null) {
    return (
      <div className="mt-4 flex flex-wrap gap-2 border-t border-line pt-4">
        {answers.map((answer, index) => (
          <button
            key={answer}
            ref={index === 0 ? firstButtonRef : undefined}
            type="button"
            onClick={() => setChoice(answer)}
            className={answer === "accept" ? PRIMARY : SECONDARY}
          >
            {BUTTON_LABEL[answer]}
          </button>
        ))}
      </div>
    );
  }

  const copy = COPY[choice];
  const trimmedLength = note.trim().length;
  const titleId = `${id}-title`;
  const noteId = `${id}-note`;
  const countId = `${id}-count`;
  const errorId = `${id}-error`;

  return (
    <form
      onSubmit={submit}
      noValidate
      aria-labelledby={titleId}
      aria-busy={pending}
      className="mt-4 border-t border-line pt-4"
    >
      <h4 id={titleId} className="text-sm font-semibold text-forest">
        {copy.question}
      </h4>

      {failure !== null ? (
        <div role="alert">
          <FieldError id={`${id}-failure`}>{failure}</FieldError>
        </div>
      ) : null}

      <label
        htmlFor={noteId}
        className="mt-3 block text-sm font-medium text-forest"
      >
        Note for the applicant (optional)
      </label>
      <textarea
        ref={noteRef}
        id={noteId}
        name="note"
        rows={3}
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

      <div className="mt-4 flex flex-wrap gap-2">
        <button type="submit" disabled={pending} className={PRIMARY}>
          {pending ? copy.pending : copy.confirm}
        </button>
        <button
          type="button"
          onClick={cancel}
          disabled={pending}
          className={SECONDARY}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
