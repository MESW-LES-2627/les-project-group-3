"use client";

import {
  Award,
  Baby,
  Building2,
  Cat,
  Dog,
  Footprints,
  House,
  Mountain,
  PawPrint,
  Sofa,
  Sprout,
  TreePine,
  type LucideIcon,
} from "lucide-react";
import { useRef, useState, useTransition, type FormEvent } from "react";

import {
  ANSWER_KEYS,
  ENERGY_OPTIONS,
  EXPERIENCE_OPTIONS,
  HOUSEHOLD,
  HOUSING_OPTIONS,
  QUESTIONS,
  SECTIONS,
  TIME_AWAY_OPTIONS,
  answeredCount,
  draftFrom,
  firstUnanswered,
  isComplete,
  matchesSaved,
  type AnswerKey,
  type DeleteOutcome,
  type Draft,
  type Energy,
  type Experience,
  type HouseholdKey,
  type Housing,
  type MatchmakerAnswers,
  type SaveOutcome,
} from "@/lib/matchmaker-profile";

import { DeleteProfile } from "./delete-profile";
import { OptionCardGroup } from "./option-card-group";
import { ProfileSummary, type ChangedAnswer } from "./profile-summary";
import { SaveBar, type BarMessage } from "./save-bar";
import { YesNoField } from "./yes-no-field";

const HOUSING_ICONS: Record<Housing, LucideIcon> = {
  apartment: Building2,
  house_no_yard: House,
  house_with_yard: TreePine,
};
const ENERGY_ICONS: Record<Energy, LucideIcon> = {
  low: Sofa,
  moderate: Footprints,
  high: Mountain,
};
const EXPERIENCE_ICONS: Record<Experience, LucideIcon> = {
  none: Sprout,
  some: PawPrint,
  experienced: Award,
};
const HOUSEHOLD_ICONS: Record<HouseholdKey, LucideIcon> = {
  has_children: Baby,
  has_dogs: Dog,
  has_cats: Cat,
};

type Feedback = { tone: "success" | "error"; text: string };

type MatchmakerProfileFormProps = {
  saved: MatchmakerAnswers | null;
  save: (answers: MatchmakerAnswers) => Promise<SaveOutcome>;
  remove: () => Promise<DeleteOutcome>;
};

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

export function MatchmakerProfileForm({
  saved,
  save,
  remove,
}: MatchmakerProfileFormProps) {
  const formRef = useRef<HTMLFormElement>(null);
  const changes = useRef(0);
  const [draft, setDraft] = useState<Draft>(() => draftFrom(saved));
  const [stored, setStored] = useState<MatchmakerAnswers | null>(saved);
  const [changed, setChanged] = useState<ChangedAnswer | null>(null);
  const [showErrors, setShowErrors] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [pending, startTransition] = useTransition();

  function answer<K extends AnswerKey>(key: K, value: MatchmakerAnswers[K]) {
    setDraft((current) => ({ ...current, [key]: value }));
    setChanged({ key, id: ++changes.current });
    setFeedback(null);
  }

  // An error is shown only for a question still unanswered, after a save attempt.
  function missing(key: AnswerKey, message: string) {
    return showErrors && draft[key] === null ? message : null;
  }

  function focusQuestion(key: AnswerKey | null) {
    if (key === null) return;
    const input = formRef.current?.querySelector<HTMLInputElement>(
      `input[name="${key}"]`,
    );
    if (!input) return;
    input.focus({ preventScroll: true });
    const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    input
      .closest("fieldset")
      ?.scrollIntoView({ block: "center", behavior: calm ? "auto" : "smooth" });
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isComplete(draft)) {
      setShowErrors(true);
      focusQuestion(firstUnanswered(draft));
      return;
    }
    const answers = draft;
    startTransition(async () => {
      const result = await save(answers);
      if (result.ok) {
        setStored(result.answers);
        setDraft(draftFrom(result.answers));
        setShowErrors(false);
        setFeedback({ tone: "success", text: "Profile saved" });
      } else {
        setFeedback({ tone: "error", text: result.error });
      }
    });
  }

  function onDeleted() {
    setStored(null);
    setDraft(draftFrom(null));
    setChanged(null);
    setShowErrors(false);
    setFeedback({ tone: "success", text: "Profile deleted" });
  }

  const left = ANSWER_KEYS.length - answeredCount(draft);
  const message: BarMessage = feedback
    ? { tone: feedback.tone, text: feedback.text, announce: true }
    : left > 0
      ? {
          tone: "neutral",
          text: `${left} ${left === 1 ? "question" : "questions"} left`,
          announce: false,
        }
      : matchesSaved(draft, stored)
        ? { tone: "success", text: "All changes saved", announce: false }
        : {
            tone: "neutral",
            text: "You have unsaved changes",
            announce: false,
          };

  return (
    <form
      ref={formRef}
      onSubmit={onSubmit}
      noValidate
      className="grid gap-x-10 lg:grid-cols-[minmax(0,1fr)_20rem]"
    >
      <ProfileSummary
        draft={draft}
        changed={changed}
        className="lg:col-start-2 lg:row-start-1 lg:self-start"
      />

      <div className="divide-y divide-line pt-8 lg:col-start-1 lg:row-start-1 lg:pt-0">
        <FormSection title={SECTIONS.home.title} why={SECTIONS.home.why}>
          <div className="space-y-8">
            <OptionCardGroup
              name="housing"
              legend={QUESTIONS.housing}
              options={HOUSING_OPTIONS}
              icons={HOUSING_ICONS}
              value={draft.housing}
              onChange={(value) => answer("housing", value)}
              error={missing("housing", "Choose one.")}
            />
            <OptionCardGroup
              name="time_away"
              legend={QUESTIONS.time_away}
              options={TIME_AWAY_OPTIONS}
              value={draft.time_away}
              onChange={(value) => answer("time_away", value)}
              error={missing("time_away", "Choose one.")}
            />
          </div>
        </FormSection>

        <FormSection
          title={SECTIONS.household.title}
          why={SECTIONS.household.why}
        >
          <div className="-mt-4 divide-y divide-line">
            {HOUSEHOLD.map((item) => (
              <YesNoField
                key={item.key}
                name={item.key}
                question={item.question}
                icon={HOUSEHOLD_ICONS[item.key]}
                value={draft[item.key]}
                onChange={(value) => answer(item.key, value)}
                error={missing(item.key, "Choose yes or no.")}
              />
            ))}
          </div>
        </FormSection>

        <FormSection title={SECTIONS.routine.title} why={SECTIONS.routine.why}>
          <div className="space-y-8">
            <OptionCardGroup
              name="activity"
              legend={QUESTIONS.activity}
              options={ENERGY_OPTIONS}
              icons={ENERGY_ICONS}
              value={draft.activity}
              onChange={(value) => answer("activity", value)}
              error={missing("activity", "Choose one.")}
            />
            <OptionCardGroup
              name="experience"
              legend={QUESTIONS.experience}
              options={EXPERIENCE_OPTIONS}
              icons={EXPERIENCE_ICONS}
              value={draft.experience}
              onChange={(value) => answer("experience", value)}
              error={missing("experience", "Choose one.")}
            />
          </div>
        </FormSection>

        {stored && <DeleteProfile remove={remove} onDeleted={onDeleted} />}
      </div>

      <SaveBar message={message} pending={pending} />
    </form>
  );
}
