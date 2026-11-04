"use client";

import {
  startTransition,
  useActionState,
  useLayoutEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";

import {
  ACTIVITY_OPTIONS,
  ANIMAL_SEX_OPTIONS,
  COMPATIBILITY_OPTIONS,
  DISTRICT_OPTIONS,
  FIRST_TIME_OWNER_OPTIONS,
  GROOMING_OPTIONS,
  NOISE_OPTIONS,
  NEUTERED_OPTIONS,
  OPTIONAL_ANIMAL_FIELDS,
  SHEDDING_OPTIONS,
  SIZE_OPTIONS,
  SPACE_OPTIONS,
  SPECIES_OPTIONS,
  TIME_ALONE_OPTIONS,
  TRAINING_OPTIONS,
} from "@/lib/animal-profile";
import {
  formValues,
  type AnimalDescription,
  type AnimalFormState,
} from "@/lib/animal-form";
import type { Option } from "@/lib/matchmaker-profile";

import { OptionCardGroup } from "@/components/matchmaker/option-card-group";

const initialState: AnimalFormState = { error: null };

const selectClassName =
  "w-full rounded-xl border border-muted/75 bg-surface px-3 py-2.5 text-sm text-forest outline-none focus-visible:border-leaf focus-visible:ring-2 focus-visible:ring-leaf/30";

function countDetails(values: Record<string, string>) {
  return OPTIONAL_ANIMAL_FIELDS.filter(
    (name) => (values[name] ?? "").trim() !== "",
  ).length;
}

function FormSection({
  title,
  why,
  children,
}: {
  title: string;
  why: string;
  children: React.ReactNode;
}) {
  return (
    <section className="py-10 first:pt-0">
      <h2 className="text-xl font-semibold text-forest">{title}</h2>
      <p className="mt-1 max-w-prose text-sm leading-6 text-muted">{why}</p>
      <div className="mt-6">{children}</div>
    </section>
  );
}

function TextField({
  label,
  name,
  type = "text",
  placeholder,
  min,
  maxLength,
  multiline = false,
  defaultValue,
}: {
  label: string;
  name: string;
  type?: string;
  placeholder?: string;
  min?: number;
  maxLength?: number;
  multiline?: boolean;
  defaultValue?: string;
}) {
  const className =
    "w-full rounded-xl border border-muted/75 bg-surface px-3 py-2.5 text-sm text-forest outline-none transition focus-visible:border-leaf focus-visible:ring-2 focus-visible:ring-leaf/30";
  return (
    <label className="flex flex-col gap-2 text-sm font-medium text-forest">
      {label}
      {multiline ? (
        <textarea
          name={name}
          rows={3}
          maxLength={maxLength}
          placeholder={placeholder}
          defaultValue={defaultValue}
          className={className}
        />
      ) : (
        <input
          name={name}
          type={type}
          min={min}
          maxLength={maxLength}
          placeholder={placeholder}
          defaultValue={defaultValue}
          required={name === "name"}
          className={className}
        />
      )}
    </label>
  );
}

type AnimalFormProps = {
  action: (
    previous: AnimalFormState,
    form: FormData,
  ) => Promise<AnimalFormState>;
  initial?: AnimalDescription;
  submitLabel: string;
  pendingLabel: string;
};

// Counts visits: Next keeps a visited page mounted but hidden, and hiding and
// showing it again run this effect's cleanup and setup.
function useVisit() {
  const [visit, setVisit] = useState(0);
  const hidden = useRef(false);
  const hiding = useRef<ReturnType<typeof setTimeout>>(undefined);
  useLayoutEffect(() => {
    // StrictMode and Fast Refresh re-run the effect at once; that is not a visit.
    clearTimeout(hiding.current);
    if (hidden.current) {
      hidden.current = false;
      setVisit((count) => count + 1);
    }
    return () => {
      hiding.current = setTimeout(() => {
        hidden.current = true;
      });
    };
  }, []);
  return visit;
}

export function AnimalForm(props: AnimalFormProps) {
  // A new key per visit restarts the form from the saved description.
  const visit = useVisit();
  return <DescriptionForm key={visit} {...props} />;
}

function DescriptionForm({
  action,
  initial,
  submitLabel,
  pendingLabel,
}: AnimalFormProps) {
  const [state, formAction, pending] = useActionState(action, initialState);
  const values = initial ? formValues(initial) : {};
  const [answers, setAnswers] = useState<Record<string, string>>(values);
  const [answered, setAnswered] = useState(() => countDetails(values));

  // React resets a form after running its `action`, which would lose what was
  // typed when a save is rejected; `action` is only the pre-hydration fallback.
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    startTransition(() => formAction(form));
  }

  function recordAnswer(name: string, value: string) {
    setAnswers((current) => ({ ...current, [name]: value }));
  }

  function clearAnswer(name: string) {
    // Not a form change event, so the count is updated here.
    setAnswers((current) => ({ ...current, [name]: "" }));
    setAnswered((count) => Math.max(0, count - 1));
  }

  function countAnswers(form: HTMLFormElement) {
    const data = new FormData(form);
    setAnswered(
      OPTIONAL_ANIMAL_FIELDS.filter((name) => {
        const value = data.get(name);
        return typeof value === "string" && value.trim() !== "";
      }).length,
    );
  }

  function choice<T extends string>(
    name: string,
    legend: string,
    options: readonly Option<T>[],
  ) {
    return (
      <OptionCardGroup
        name={name}
        legend={legend}
        options={options}
        value={(answers[name] || null) as T | null}
        onChange={(value) => recordAnswer(name, value)}
        onClear={() => clearAnswer(name)}
        optional
      />
    );
  }

  return (
    <form
      action={formAction}
      onSubmit={submit}
      onChange={(event) => countAnswers(event.currentTarget)}
      className="grid gap-x-10 lg:grid-cols-[minmax(0,1fr)_20rem]"
    >
      <aside className="h-fit rounded-2xl border border-line bg-surface p-6 shadow-sm lg:sticky lg:top-8 lg:col-start-2 lg:row-start-1">
        <p className="text-xs font-bold uppercase tracking-wide text-leaf">
          Animal profile
        </p>
        <h2 className="mt-2 text-xl font-semibold text-forest">
          Help us find the right home
        </h2>
        <p className="mt-3 text-sm leading-6 text-muted">
          Add the details you know. Every compatibility and care question is
          optional, and can be left blank when it is not known.
        </p>
        <div className="mt-6 rounded-xl bg-leaf-tint p-4">
          <p className="text-sm font-semibold text-forest">
            {answered} of {OPTIONAL_ANIMAL_FIELDS.length} optional details added
          </p>
          <div
            className="mt-3 h-2 overflow-hidden rounded-full bg-white"
            role="progressbar"
            aria-label="Optional animal details completed"
            aria-valuemin={0}
            aria-valuemax={OPTIONAL_ANIMAL_FIELDS.length}
            aria-valuenow={answered}
          >
            <div
              className="h-full rounded-full bg-leaf transition-[width]"
              style={{
                width: `${(answered / OPTIONAL_ANIMAL_FIELDS.length) * 100}%`,
              }}
            />
          </div>
        </div>
      </aside>

      <div className="divide-y divide-line pt-8 lg:col-start-1 lg:row-start-1 lg:pt-0">
        <FormSection
          title="About the animal"
          why="Start with the details needed to publish a listing."
        >
          <div className="grid gap-6 sm:grid-cols-2">
            <TextField
              label="Name *"
              name="name"
              placeholder="e.g. Rex"
              defaultValue={values.name}
            />
            <label className="flex flex-col gap-2 text-sm font-medium text-forest">
              Species *
              <select
                name="species"
                defaultValue={values.species || "dog"}
                className={selectClassName}
              >
                {SPECIES_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <TextField
              label="Age in months"
              name="age_in_months"
              type="number"
              min={0}
              defaultValue={values.age_in_months}
            />
            <TextField
              label="Postal code"
              name="postal_code"
              placeholder="0000-000"
              maxLength={8}
              defaultValue={values.postal_code}
            />
            <label className="flex flex-col gap-2 text-sm font-medium text-forest">
              District
              <select
                name="district"
                defaultValue={values.district}
                className={selectClassName}
              >
                <option value="">Not specified</option>
                {DISTRICT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            {choice("sex", "Sex", ANIMAL_SEX_OPTIONS)}
            {choice("is_neutered", "Is the animal neutered?", NEUTERED_OPTIONS)}
          </div>
        </FormSection>

        <FormSection
          title="Needs and appearance"
          why="These details help people understand the animal's everyday needs."
        >
          <div className="space-y-8">
            {choice("size", "Size", SIZE_OPTIONS)}
            {choice("activity_level", "Activity level", ACTIVITY_OPTIONS)}
            {choice("space_requirement", "Space requirement", SPACE_OPTIONS)}
            {choice("shedding", "Shedding", SHEDDING_OPTIONS)}
            {choice("grooming_needs", "Grooming needs", GROOMING_OPTIONS)}
          </div>
        </FormSection>

        <FormSection
          title="Living with others"
          why="Share what is known about the animal's interactions. Unknown is always a valid answer."
        >
          <div className="space-y-8">
            {choice(
              "behaves_well_with_children",
              "Behaves well with children",
              COMPATIBILITY_OPTIONS,
            )}
            {choice(
              "behaves_well_with_dogs",
              "Behaves well with dogs",
              COMPATIBILITY_OPTIONS,
            )}
            {choice(
              "behaves_well_with_cats",
              "Behaves well with cats",
              COMPATIBILITY_OPTIONS,
            )}
            {choice(
              "behaves_well_with_other_animals",
              "Behaves well with other animals",
              COMPATIBILITY_OPTIONS,
            )}
          </div>
        </FormSection>

        <FormSection
          title="Care and temperament"
          why="Add any other information that may help a future adopter prepare."
        >
          <div className="space-y-8">
            {choice("training_needs", "Training needs", TRAINING_OPTIONS)}
            {choice(
              "tolerance_for_time_alone",
              "Tolerance for time alone",
              TIME_ALONE_OPTIONS,
            )}
            {choice("noise_level", "Noise level", NOISE_OPTIONS)}
            {choice(
              "suitable_for_first_time_owners",
              "Suitable for first-time owners",
              FIRST_TIME_OWNER_OPTIONS,
            )}
            <TextField
              label="Special-care notes"
              name="special_care_notes"
              multiline
              maxLength={2000}
              defaultValue={values.special_care_notes}
            />
            <TextField
              label="Other details"
              name="other_details"
              multiline
              maxLength={2000}
              defaultValue={values.other_details}
            />
          </div>
        </FormSection>
      </div>

      <div className="sticky bottom-0 z-10 border-t border-line bg-background pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3 lg:col-span-2">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {state.error ? (
            <p role="alert" className="text-sm font-medium text-red-700">
              {state.error}
            </p>
          ) : (
            <p className="text-sm text-muted">
              Fields marked * are required.
            </p>
          )}
          <button
            type="submit"
            disabled={pending}
            className="inline-flex min-h-11 items-center justify-center rounded-xl bg-forest px-5 text-sm font-semibold text-white transition-colors hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-60"
          >
            {pending ? pendingLabel : submitLabel}
          </button>
        </div>
      </div>
    </form>
  );
}
