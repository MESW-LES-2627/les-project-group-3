"use client";

import type { LucideIcon } from "lucide-react";
import { useId } from "react";

import { FieldError } from "./field-error";

type YesNoFieldProps = {
  name: string;
  question: string;
  icon: LucideIcon;
  value: boolean | null;
  onChange: (value: boolean) => void;
  error?: string | null;
};

const CHOICES = [
  { answer: true, value: "yes", label: "Yes" },
  { answer: false, value: "no", label: "No" },
] as const;

// A yes/no row. The question is the fieldset's legend for screen readers; the
// visible copy is hidden from them so it is not read twice.
export function YesNoField({
  name,
  question,
  icon: Icon,
  value,
  onChange,
  error,
}: YesNoFieldProps) {
  const errorId = useId();
  const invalid = Boolean(error) && value === null;

  return (
    <fieldset
      aria-describedby={error ? errorId : undefined}
      className="min-w-0 py-4"
    >
      <legend className="sr-only">{question}</legend>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-3">
        <span
          aria-hidden="true"
          className="grid size-10 shrink-0 place-items-center rounded-xl bg-leaf/10 text-leaf"
        >
          <Icon className="size-5" strokeWidth={1.75} />
        </span>
        <span
          aria-hidden="true"
          className="min-w-0 flex-1 basis-48 text-base font-medium text-forest"
        >
          {question}
        </span>
        <div
          className={`inline-flex rounded-xl border bg-surface p-1 shadow-sm ${
            invalid ? "border-red-700" : "border-muted/75"
          }`}
        >
          {CHOICES.map((choice) => (
            <label key={choice.value} className="relative flex cursor-pointer">
              <input
                type="radio"
                name={name}
                value={choice.value}
                checked={value === choice.answer}
                onChange={() => onChange(choice.answer)}
                required
                className="peer sr-only"
              />
              <span className="grid min-h-10 min-w-16 place-items-center rounded-lg px-4 text-sm font-semibold text-forest transition-[background-color,color] duration-150 ease-out-expo peer-checked:bg-forest peer-checked:text-white peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-forest peer-not-checked:hover:bg-leaf/10 motion-reduce:transition-none">
                {choice.label}
              </span>
            </label>
          ))}
        </div>
      </div>
      {error && <FieldError id={errorId}>{error}</FieldError>}
    </fieldset>
  );
}
