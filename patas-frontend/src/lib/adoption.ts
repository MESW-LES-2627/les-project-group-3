// What the page knows about requesting to adopt. No network here: the backend
// decides every rule, and noteProblem only saves a round trip for the obvious cases.
import {
  isApplicationStatus,
  type ApplicationStatus,
} from "@/lib/adoption-status";
import type { Confirmation } from "@/lib/confirmation";
import {
  isMatchmakerAnswers,
  type MatchmakerAnswers,
} from "@/lib/matchmaker-profile";

// The backend's limit (models/adoption/application.py, MAX_NOTE_LENGTH).
export const NOTE_MAX = 1000;

export type RequestProblem =
  | "no-profile"
  | "already-requested"
  | "not-available"
  | "invalid-note"
  | "own-animal"
  | "not-found"
  | "unavailable";

export type MyApplication = {
  id: string;
  animal_id: string;
  status: string;
  note: string;
  owner_confirmed_at: string | null;
  applicant_confirmed_at: string | null;
};

export type RequestOutcome =
  | { ok: true; application: MyApplication }
  | { ok: false; problem: RequestProblem; message: string };

export type MyApplicationResult =
  | { kind: "none" }
  | { kind: "active"; application: MyApplication }
  | { kind: "unavailable" };

export const REQUEST_MESSAGES: Record<RequestProblem, string> = {
  "no-profile": "Create your Matchmaker profile first, then come back.",
  "already-requested": "You already have a request for this animal.",
  "not-available": "This animal is not taking requests right now.",
  "invalid-note": `Write a note of up to ${NOTE_MAX} characters.`,
  "own-animal": "This is your own animal.",
  "not-found": "This animal is no longer available.",
  unavailable: "The service is unavailable, please try again.",
};

const NOTE_PROBLEM_MESSAGE = {
  blank: "Tell the owner a little about you and your home.",
  "too-long": `Keep the note under ${NOTE_MAX} characters.`,
} as const;

export type NoteProblem = keyof typeof NOTE_PROBLEM_MESSAGE;

export function noteProblem(note: string): NoteProblem | null {
  const trimmed = note.trim();
  if (trimmed.length === 0) {
    return "blank";
  }
  return trimmed.length > NOTE_MAX ? "too-long" : null;
}

export function noteProblemMessage(problem: NoteProblem): string {
  return NOTE_PROBLEM_MESSAGE[problem];
}

export function isMyApplication(value: unknown): value is MyApplication {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const { id, animal_id, status, note, owner_confirmed_at, applicant_confirmed_at } =
    value as Record<string, unknown>;
  return (
    typeof id === "string" &&
    typeof animal_id === "string" &&
    typeof status === "string" &&
    typeof note === "string" &&
    (owner_confirmed_at === null || typeof owner_confirmed_at === "string") &&
    (applicant_confirmed_at === null || typeof applicant_confirmed_at === "string")
  );
}

// US-17: the requests the signed-in person sent, and withdrawing one.

export type SentRequest = {
  id: string;
  animal_id: string;
  animal_name: string;
  status: string;
  note: string;
  owner_note: string | null;
  owner_confirmed_at: string | null;
  applicant_confirmed_at: string | null;
  created_at: string;
};

export function isSentRequest(value: unknown): value is SentRequest {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const r = value as Record<string, unknown>;
  return (
    typeof r.id === "string" &&
    typeof r.animal_id === "string" &&
    typeof r.animal_name === "string" &&
    typeof r.status === "string" &&
    typeof r.note === "string" &&
    (r.owner_note === null || typeof r.owner_note === "string") &&
    (r.owner_confirmed_at === null ||
      typeof r.owner_confirmed_at === "string") &&
    (r.applicant_confirmed_at === null ||
      typeof r.applicant_confirmed_at === "string") &&
    typeof r.created_at === "string"
  );
}

export type MyRequestsResult =
  | { kind: "ok"; requests: SentRequest[] }
  | { kind: "unavailable" };

export type ReceivedRequest = {
  id: string;
  animal_id: string;
  animal_name: string;
  applicant_name: string;
  applicant_username: string;
  status: string;
  note: string;
  owner_note: string | null;
  applicant_profile: MatchmakerAnswers;
  compatibility_concerns: string[];
  owner_confirmed_at: string | null;
  applicant_confirmed_at: string | null;
  created_at: string;
};

export function isReceivedRequest(value: unknown): value is ReceivedRequest {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const request = value as Record<string, unknown>;
  return (
    typeof request.id === "string" &&
    typeof request.animal_id === "string" &&
    typeof request.animal_name === "string" &&
    typeof request.applicant_name === "string" &&
    typeof request.applicant_username === "string" &&
    typeof request.status === "string" &&
    typeof request.note === "string" &&
    (request.owner_note === null || typeof request.owner_note === "string") &&
    isMatchmakerAnswers(request.applicant_profile) &&
    Array.isArray(request.compatibility_concerns) &&
    request.compatibility_concerns.every(
      (concern) => typeof concern === "string",
    ) &&
    (request.owner_confirmed_at === null ||
      typeof request.owner_confirmed_at === "string") &&
    (request.applicant_confirmed_at === null ||
      typeof request.applicant_confirmed_at === "string") &&
    typeof request.created_at === "string"
  );
}

export type ReceivedRequestsResult =
  | { kind: "ok"; requests: ReceivedRequest[] }
  | { kind: "unavailable" };

export type WithdrawProblem = "not-found" | "not-active" | "unavailable";

export type WithdrawOutcome =
  | { ok: true }
  | { ok: false; problem: WithdrawProblem; message: string };

export type WithdrawAction = (
  applicationId: string,
  animalId: string,
) => Promise<WithdrawOutcome>;

export const WITHDRAW_MESSAGES: Record<WithdrawProblem, string> = {
  "not-found": "This request no longer exists.",
  "not-active": "This request has already ended, so it cannot be withdrawn.",
  unavailable: "The service is unavailable, please try again.",
};

// Presentation only: the backend decides what can be withdrawn.
export function canWithdraw(status: string): boolean {
  return status === "open" || status === "accepted";
}

export function withdrawConfirmation(
  animalName: string,
  status: string,
): Confirmation {
  return status === "accepted"
    ? {
        title: `Withdraw your accepted request for ${animalName}?`,
        message: `${animalName} will be available to others again.`,
      }
    : { title: `Withdraw your request for ${animalName}?` };
}

// US-18: the owner or applicant confirms the animal was handed over.

export function handoverConfirmation(
  animalName: string,
  otherSideConfirmed: boolean,
): Confirmation {
  return otherSideConfirmed
    ? {
        title: `Complete the adoption of ${animalName}?`,
        message: `The other side has already confirmed. ${animalName} will be marked adopted and any other open requests will be closed. This cannot be undone.`,
      }
    : {
        title: `Confirm the handover of ${animalName}?`,
        message: "The adoption is completed when the other side confirms too.",
      };
}

export type ConfirmHandoverProblem =
  | "not-found"
  | "not-confirmable"
  | "unavailable";

export const CONFIRM_HANDOVER_MESSAGES: Record<
  ConfirmHandoverProblem,
  string
> = {
  "not-found": "This request could not be found.",
  "not-confirmable":
    "This handover can no longer be confirmed, or you have already confirmed it.",
  unavailable:
    "We could not confirm the handover right now. Please try again.",
};

export type ConfirmHandoverOutcome =
  | { ok: true }
  | { ok: false; problem: ConfirmHandoverProblem; message: string };

export type ConfirmHandoverAction = (
  applicationId: string,
  animalId: string,
) => Promise<ConfirmHandoverOutcome>;

// US-16: the owner accepts or declines a request, with an optional note.

export type OwnerAnswer = "accept" | "decline";

export type AnswerProblem =
  | "not-found"
  | "not-active"
  | "animal-reserved"
  | "invalid-note"
  | "unavailable";

export type AnswerOutcome =
  | { ok: true }
  | { ok: false; problem: AnswerProblem; message: string };

export type AnswerAction = (
  applicationId: string,
  animalId: string,
  answer: OwnerAnswer,
  note: string,
) => Promise<AnswerOutcome>;

export const ANSWER_MESSAGES: Record<AnswerProblem, string> = {
  "not-found": "This request no longer exists.",
  "not-active": "This request has already changed, so it cannot be answered.",
  "animal-reserved": "This animal is already reserved for another request.",
  "invalid-note": `Write a note of up to ${NOTE_MAX} characters.`,
  unavailable: "The service is unavailable, please try again.",
};

// Presentation only: the backend decides what can be answered. An open request can
// be accepted or declined; an accepted one can still be declined.
export function answersAvailable(status: string): OwnerAnswer[] {
  if (status === "open") {
    return ["accept", "decline"];
  }
  return status === "accepted" ? ["decline"] : [];
}

// The owner's note is optional, so it can only be too long. It counts the trimmed
// text, like the backend.
export function answerNoteProblem(note: string): "too-long" | null {
  return note.trim().length > NOTE_MAX ? "too-long" : null;
}

// The ?status= of the requests page. Anything that is not a known status means All.
export function statusFilterOf(value: string | null): ApplicationStatus | null {
  return isApplicationStatus(value) ? value : null;
}

export function filterByStatus<T extends { status: string }>(
  requests: T[],
  status: ApplicationStatus | null,
): T[] {
  return status === null
    ? requests
    : requests.filter((request) => request.status === status);
}
