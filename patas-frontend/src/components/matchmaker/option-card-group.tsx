"use client";

import { Check, type LucideIcon } from "lucide-react";
import { useId } from "react";

import type { Option } from "@/lib/matchmaker-profile";

import { FieldError } from "./field-error";

type OptionCardGroupProps<T extends string> = {
  name: string;
  legend: string;
  options: readonly Option<T>[];
  value: T | null;
  onChange: (value: T) => void;
  icons?: Partial<Record<T, LucideIcon>>;
  error?: string | null;
  optional?: boolean;
};

// One question, answered by picking a card. Native radio inputs sit under the cards
// (visually hidden, still focusable), so the arrow keys, Space and screen readers
// work without any custom keyboard code.
export function OptionCardGroup<T extends string>({
  name,
  legend,
  options,
  value,
  onChange,
  icons,
  error,
  optional = false,
}: OptionCardGroupProps<T>) {
  const errorId = useId();
  const invalid = Boolean(error) && value === null;

  return (
    <fieldset
      aria-describedby={error ? errorId : undefined}
      className="min-w-0"
    >
      <legend className="mb-3 text-base font-semibold text-forest">
        {legend}
      </legend>
      <div className="grid gap-3 sm:grid-cols-3">
        {options.map((option) => {
          // Annotated: TypeScript cannot use a lookup by a generic key as a component.
          const Icon: LucideIcon | undefined = icons?.[option.value];
          return (
            <label key={option.value} className="relative flex cursor-pointer">
              <input
                type="radio"
                name={name}
                value={option.value}
                checked={value === option.value}
                onChange={() => onChange(option.value)}
                required={!optional}
                className="peer sr-only"
              />
              <span
                className={`flex w-full flex-col gap-2 rounded-2xl border bg-surface p-4 pr-12 shadow-sm transition-[background-color,border-color,box-shadow] duration-150 ease-out-expo motion-reduce:transition-none peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-forest peer-checked:border-leaf peer-checked:bg-leaf-tint peer-checked:shadow-md peer-checked:ring-1 peer-checked:ring-leaf peer-not-checked:hover:border-leaf ${
                  invalid ? "border-red-700" : "border-muted/75"
                }`}
              >
                {Icon && (
                  <span className="grid size-10 place-items-center rounded-xl bg-leaf/10 text-leaf">
                    <Icon
                      aria-hidden="true"
                      className="size-5"
                      strokeWidth={1.75}
                    />
                  </span>
                )}
                <span className="font-semibold text-forest">
                  {option.label}
                </span>
                {option.description && (
                  <span className="text-sm leading-5 text-muted">
                    {option.description}
                  </span>
                )}
              </span>
              <span
                aria-hidden="true"
                className="pointer-events-none absolute right-3 top-3 grid size-6 scale-75 place-items-center rounded-full bg-leaf text-white opacity-0 transition duration-150 ease-out-expo peer-checked:scale-100 peer-checked:opacity-100 motion-reduce:transition-none"
              >
                <Check className="size-3.5" strokeWidth={3} />
              </span>
            </label>
          );
        })}
      </div>
      {error && <FieldError id={errorId}>{error}</FieldError>}
    </fieldset>
  );
}
