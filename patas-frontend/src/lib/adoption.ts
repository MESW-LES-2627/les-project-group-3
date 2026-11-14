// What the page knows about requesting to adopt. No network here: the backend
// decides every rule, and noteProblem only saves a round trip for the obvious cases.
import {
  isApplicationStatus,
  type ApplicationStatus,
} from "@/lib/adoption-status";
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
  const { id, animal_id, status, note } = value as Record<string, unknown>;
  return (
    typeof id === "string" &&
    typeof animal_id === "string" &&
    typeof status === "string" &&
    typeof note === "string"
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
  status: string;
  note: string;
  applicant_profile: MatchmakerAnswers;
  compatibility_concerns: string[];
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
    typeof request.status === "string" &&
    typeof request.note === "string" &&
    isMatchmakerAnswers(request.applicant_profile) &&
    Array.isArray(request.compatibility_concerns) &&
    request.compatibility_concerns.every(
      (concern) => typeof concern === "string",
    ) &&
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

export function withdrawConfirmation(animalName: string, status: string): string {
  return status === "accepted"
    ? `Withdraw your accepted request for ${animalName}? ${animalName} will be available to others again.`
    : `Withdraw your request for ${animalName}?`;
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
