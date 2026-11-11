// What the page knows about requesting to adopt. No network here: the backend
// decides every rule, and noteProblem only saves a round trip for the obvious cases.

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
