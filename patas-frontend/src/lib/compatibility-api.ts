// Server-side only: the call from the frontend to the backend's compatibility
// endpoint. The browser never calls FastAPI directly (ADR 0005): this runs on the
// Next.js server and adds the signed-in user's token.
//
// This file only handles HTTP. The score, the reasons and what counts as not
// suitable are the backend's.
import { backendUrl } from "@/lib/backend";
import {
  isFit,
  type FitOutcome,
  type FitProblem,
  type Mode,
} from "@/lib/compatibility";
import { bearerToken } from "@/lib/matchmaker-api";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const MESSAGES: Record<FitProblem, string> = {
  "no-profile": "Create your Matchmaker profile first, then come back.",
  "own-animal": "This is your own animal, so there is no fit to calculate.",
  "not-found": "This animal is no longer available.",
  unavailable: "The service is unavailable, please try again.",
};

function problem(kind: FitProblem): FitOutcome {
  return { ok: false, problem: kind, message: MESSAGES[kind] };
}

export async function getFit(animalId: string, mode: Mode): Promise<FitOutcome> {
  if (!UUID_PATTERN.test(animalId)) {
    return problem("not-found");
  }
  // Checked on every call, not only on the page: a Server Action is a public
  // endpoint. redirect() throws, so this stays outside the try/catch below.
  const token = await bearerToken();

  let response: Response;
  try {
    response = await fetch(
      `${backendUrl()}/animals/${encodeURIComponent(animalId)}/compatibility?mode=${mode}`,
      { cache: "no-store", headers: { Authorization: `Bearer ${token}` } },
    );
  } catch {
    return problem("unavailable");
  }

  if (response.status === 409) {
    return problem("no-profile");
  }
  if (response.status === 404) {
    return problem("not-found");
  }
  if (response.status === 422) {
    // The domain refusal is a string; FastAPI's type errors are a list.
    const { detail } = (await response.json()) as { detail: unknown };
    return problem(typeof detail === "string" ? "own-animal" : "unavailable");
  }
  if (!response.ok) {
    return problem("unavailable");
  }
  const payload: unknown = await response.json();
  return isFit(payload) ? { ok: true, fit: payload } : problem("unavailable");
}
