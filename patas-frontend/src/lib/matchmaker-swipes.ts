import { REASON_KINDS, type Reason, type ReasonKind } from "@/lib/compatibility";

export const SWIPE_DISPOSITIONS = ["passed", "saved"] as const;
export type SwipeDisposition = (typeof SWIPE_DISPOSITIONS)[number];

export type SwipeFit = {
  score: number;
  is_compatible: boolean;
  reasons: Reason[];
};

export type SwipeAnimal = {
  id: string;
  owner_id: string;
  owner_name: string;
  name: string;
  species: string;
  age_in_months: number | null;
  district: string | null;
  size: string | null;
  adoption_status: string;
  fit: SwipeFit | null;
};

export type SwipeFailure =
  | "already-swiped"
  | "not-available"
  | "no-profile"
  | "not-found"
  | "unavailable";

export type SwipeOutcome =
  | { ok: true }
  | { ok: false; problem: SwipeFailure; message: string };

export type SwipeFeedOutcome =
  | { ok: true; animals: SwipeAnimal[] }
  | { ok: false; problem: "no-profile" | "unavailable"; message: string };

export type SavedAnimalsOutcome =
  | { ok: true; animals: SwipeAnimal[] }
  | { ok: false; problem: "unavailable"; message: string };

export const SWIPE_MESSAGES: Record<SwipeFailure, string> = {
  "already-swiped": "You have already made a choice about this animal.",
  "not-available": "This animal is no longer available.",
  "no-profile": "Save your Matchmaker profile before swiping.",
  "not-found": "This animal is no longer in your saved list.",
  unavailable: "The service is unavailable, please try again.",
};

export function isSwipeDisposition(value: unknown): value is SwipeDisposition {
  return (
    typeof value === "string" &&
    (SWIPE_DISPOSITIONS as readonly string[]).includes(value)
  );
}

function isReason(value: unknown): value is Reason {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const reason = value as Record<string, unknown>;
  return (
    typeof reason.text === "string" &&
    typeof reason.kind === "string" &&
    (REASON_KINDS as readonly string[]).includes(reason.kind)
  );
}

function isSwipeFit(value: unknown): value is SwipeFit {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const fit = value as Record<string, unknown>;
  return (
    typeof fit.score === "number" &&
    fit.score >= 0 &&
    fit.score <= 100 &&
    typeof fit.is_compatible === "boolean" &&
    Array.isArray(fit.reasons) &&
    fit.reasons.every(isReason)
  );
}

export function isSwipeAnimal(value: unknown): value is SwipeAnimal {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const animal = value as Record<string, unknown>;
  return (
    typeof animal.id === "string" &&
    typeof animal.owner_id === "string" &&
    typeof animal.owner_name === "string" &&
    typeof animal.name === "string" &&
    typeof animal.species === "string" &&
    (animal.age_in_months === null ||
      typeof animal.age_in_months === "number") &&
    (animal.district === null || typeof animal.district === "string") &&
    (animal.size === null || typeof animal.size === "string") &&
    typeof animal.adoption_status === "string" &&
    (animal.fit === null || isSwipeFit(animal.fit))
  );
}

export function reasonKindLabel(kind: ReasonKind): string {
  if (kind === "strength") return "Fits";
  if (kind === "concern") return "Worth checking";
  return "Not provided";
}
