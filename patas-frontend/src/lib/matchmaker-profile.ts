// Types, answer options and wording for the Matchmaker profile. Plain TypeScript:
// no React and no server imports, so server and client components can share it.
// The values mirror the backend enums (ADR 0008); the backend stays the source of truth.

export const HOUSING = ["apartment", "house_no_yard", "house_with_yard"] as const;
export const TIME_AWAY = ["few_hours", "half_day", "most_of_day"] as const;
export const ENERGY = ["low", "moderate", "high"] as const;
export const EXPERIENCE = ["none", "some", "experienced"] as const;

export type Housing = (typeof HOUSING)[number];
export type TimeAway = (typeof TIME_AWAY)[number];
export type Energy = (typeof ENERGY)[number];
export type Experience = (typeof EXPERIENCE)[number];

export type MatchmakerAnswers = {
  housing: Housing;
  time_away: TimeAway;
  activity: Energy;
  experience: Experience;
  has_children: boolean;
  has_dogs: boolean;
  has_cats: boolean;
};

export type AnswerKey = keyof MatchmakerAnswers;

// What the form holds while it is filled in: null means "not answered yet".
export type Draft = { [K in AnswerKey]: MatchmakerAnswers[K] | null };

// The order the form asks the questions in.
export const ANSWER_KEYS: readonly AnswerKey[] = [
  "housing",
  "time_away",
  "has_children",
  "has_dogs",
  "has_cats",
  "activity",
  "experience",
];

export const EMPTY_DRAFT: Draft = {
  housing: null,
  time_away: null,
  activity: null,
  experience: null,
  has_children: null,
  has_dogs: null,
  has_cats: null,
};

function isOneOf<T extends string>(
  values: readonly T[],
  value: unknown,
): value is T {
  return (
    typeof value === "string" && (values as readonly string[]).includes(value)
  );
}

export function isMatchmakerAnswers(
  value: unknown,
): value is MatchmakerAnswers {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const answers = value as Record<string, unknown>;
  return (
    isOneOf(HOUSING, answers.housing) &&
    isOneOf(TIME_AWAY, answers.time_away) &&
    isOneOf(ENERGY, answers.activity) &&
    isOneOf(EXPERIENCE, answers.experience) &&
    typeof answers.has_children === "boolean" &&
    typeof answers.has_dogs === "boolean" &&
    typeof answers.has_cats === "boolean"
  );
}

export function draftFrom(saved: MatchmakerAnswers | null): Draft {
  return saved ? { ...saved } : { ...EMPTY_DRAFT };
}

export function answeredCount(draft: Draft): number {
  return ANSWER_KEYS.filter((key) => draft[key] !== null).length;
}

export function isComplete(draft: Draft): draft is MatchmakerAnswers {
  return answeredCount(draft) === ANSWER_KEYS.length;
}

export function firstUnanswered(draft: Draft): AnswerKey | null {
  return ANSWER_KEYS.find((key) => draft[key] === null) ?? null;
}

// True when the draft holds exactly the saved answers (or nothing, if none is saved).
export function matchesSaved(
  draft: Draft,
  saved: MatchmakerAnswers | null,
): boolean {
  return ANSWER_KEYS.every((key) => draft[key] === (saved ? saved[key] : null));
}

export type SaveOutcome =
  | { ok: true; answers: MatchmakerAnswers }
  | { ok: false; error: string };
export type DeleteOutcome = { ok: true } | { ok: false; error: string };

export type Option<T extends string> = {
  value: T;
  label: string;
  description?: string;
  // How the choice reads inside the summary sentence.
  phrase: string;
};

export const HOUSING_OPTIONS: readonly Option<Housing>[] = [
  {
    value: "apartment",
    label: "Apartment",
    description: "No garden or yard of my own",
    phrase: "an apartment",
  },
  {
    value: "house_no_yard",
    label: "House, no yard",
    description: "A house without a garden or yard",
    phrase: "a house without a yard",
  },
  {
    value: "house_with_yard",
    label: "House with a yard",
    description: "A house with a garden or yard",
    phrase: "a house with a yard",
  },
];

export const TIME_AWAY_OPTIONS: readonly Option<TimeAway>[] = [
  { value: "few_hours", label: "A few hours", phrase: "a few hours" },
  { value: "half_day", label: "Half the day", phrase: "half the day" },
  { value: "most_of_day", label: "Most of the day", phrase: "most of the day" },
];

export const ENERGY_OPTIONS: readonly Option<Energy>[] = [
  {
    value: "low",
    label: "Low",
    description: "Calm days: short walks, mostly indoors",
    phrase: "calm",
  },
  {
    value: "moderate",
    label: "Moderate",
    description: "Daily walks and some play",
    phrase: "moderately active",
  },
  {
    value: "high",
    label: "High",
    description: "Long daily activity: runs, hikes, lots of play",
    phrase: "very active",
  },
];

export const EXPERIENCE_OPTIONS: readonly Option<Experience>[] = [
  {
    value: "none",
    label: "None",
    description: "This would be my first pet",
    phrase: "no",
  },
  {
    value: "some",
    label: "Some",
    description: "I've had pets before",
    phrase: "some",
  },
  {
    value: "experienced",
    label: "Experienced",
    description: "Confident with strong-willed or special-needs animals",
    phrase: "a lot of",
  },
];

export type HouseholdKey = "has_children" | "has_dogs" | "has_cats";

export const HOUSEHOLD: readonly {
  key: HouseholdKey;
  label: string;
  question: string;
  yes: string;
  no: string;
}[] = [
  {
    key: "has_children",
    label: "Children",
    question: "Are there children at home?",
    yes: "children",
    no: "no children",
  },
  {
    key: "has_dogs",
    label: "Dogs",
    question: "Do you have dogs at home?",
    yes: "dogs",
    no: "no dogs",
  },
  {
    key: "has_cats",
    label: "Cats",
    question: "Do you have cats at home?",
    yes: "cats",
    no: "no cats",
  },
];

export const QUESTIONS = {
  housing: "Where do you live?",
  time_away: "How long are you usually away from home each day?",
  activity: "How active is your household?",
  experience: "How much experience do you have with animals?",
} as const;

export const SECTIONS = {
  home: {
    title: "Your home",
    why: "So we can tell which animals would be comfortable where you live.",
  },
  household: {
    title: "Your household",
    why: "Not every animal gets along with children, dogs or cats, so we need to know who is at home.",
  },
  routine: {
    title: "Your routine",
    why: "Energy and experience help match you with an animal you can look after well.",
  },
} as const;

// The summary sentence. Each answer is its own segment so the panel can highlight
// the one that just changed; a null text is a question not answered yet.
export type Segment =
  | { kind: "text"; text: string }
  | { kind: "answer"; key: AnswerKey; text: string | null };

function phraseOf<T extends string>(
  options: readonly Option<T>[],
  value: T | null,
): string | null {
  return options.find((option) => option.value === value)?.phrase ?? null;
}

export function sentence(draft: Draft): Segment[] {
  const text = (value: string): Segment => ({ kind: "text", text: value });
  const answer = (key: AnswerKey, phrase: string | null): Segment => ({
    kind: "answer",
    key,
    text: phrase,
  });
  const [children, dogs, cats] = HOUSEHOLD.map((item) => {
    const has = draft[item.key];
    return answer(item.key, has === null ? null : has ? item.yes : item.no);
  });

  return [
    text("I live in "),
    answer("housing", phraseOf(HOUSING_OPTIONS, draft.housing)),
    text(". On a normal day I'm away "),
    answer("time_away", phraseOf(TIME_AWAY_OPTIONS, draft.time_away)),
    text(". At home there are "),
    children,
    text(", "),
    dogs,
    text(" and "),
    cats,
    text(". My household is "),
    answer("activity", phraseOf(ENERGY_OPTIONS, draft.activity)),
    text(" and I have "),
    answer("experience", phraseOf(EXPERIENCE_OPTIONS, draft.experience)),
    text(" experience with animals."),
  ];
}
