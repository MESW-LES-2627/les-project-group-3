// Server-side only: the calls from the frontend to the backend's adoption endpoints.
// The browser never calls FastAPI directly (ADR 0005): this runs on the Next.js
// server and adds the signed-in user's token.
//
// This file only handles HTTP. Who may ask, and when, is the backend's.
import { backendUrl } from "@/lib/backend";
import {
  ANSWER_MESSAGES,
  CONFIRM_HANDOVER_MESSAGES,
  REQUEST_MESSAGES,
  TICK_MESSAGES,
  WITHDRAW_MESSAGES,
  isChecklist,
  isMyApplication,
  isReceivedRequest,
  isSentRequest,
  type AnswerOutcome,
  type AnswerProblem,
  type ConfirmHandoverOutcome,
  type ConfirmHandoverProblem,
  type MyApplicationResult,
  type OwnerAnswer,
  type MyRequestsResult,
  type ReceivedRequestsResult,
  type RequestOutcome,
  type RequestProblem,
  type TickOutcome,
  type TickProblem,
  type WithdrawOutcome,
  type WithdrawProblem,
} from "@/lib/adoption";
import { bearerToken } from "@/lib/matchmaker-api";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

// The backend's 409 carries a code, because it has more than one cause.
const CONFLICT_CODES: Record<string, RequestProblem> = {
  matchmaker_profile_required: "no-profile",
  already_requested: "already-requested",
  animal_not_available: "not-available",
};

function problem(kind: RequestProblem): RequestOutcome {
  return { ok: false, problem: kind, message: REQUEST_MESSAGES[kind] };
}

async function conflictProblem(response: Response): Promise<RequestProblem> {
  try {
    const { detail } = (await response.json()) as {
      detail?: { code?: unknown };
    };
    const code = detail?.code;
    return typeof code === "string" && Object.hasOwn(CONFLICT_CODES, code)
      ? CONFLICT_CODES[code]
      : "unavailable";
  } catch {
    return "unavailable";
  }
}

export async function requestToAdopt(
  animalId: string,
  note: string,
): Promise<RequestOutcome> {
  if (!UUID_PATTERN.test(animalId)) {
    return problem("not-found");
  }
  // Checked on every call, not only on the page: a Server Action is a public
  // endpoint. redirect() throws, so this stays outside the try/catch below.
  const token = await bearerToken();

  let response: Response;
  try {
    response = await fetch(
      `${backendUrl()}/animals/${encodeURIComponent(animalId)}/applications`,
      {
        method: "POST",
        cache: "no-store",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ note }),
      },
    );
  } catch {
    return problem("unavailable");
  }

  if (response.status === 201) {
    const payload: unknown = await response.json();
    return isMyApplication(payload)
      ? { ok: true, application: payload }
      : problem("unavailable");
  }
  if (response.status === 403) {
    return problem("own-animal");
  }
  if (response.status === 404) {
    return problem("not-found");
  }
  if (response.status === 409) {
    return problem(await conflictProblem(response));
  }
  if (response.status === 422) {
    return problem("invalid-note");
  }
  return problem("unavailable");
}

// Never throws on a backend failure: the animal page is public, and a problem here
// must not take the whole page down.
export async function getMyApplication(
  animalId: string,
): Promise<MyApplicationResult> {
  if (!UUID_PATTERN.test(animalId)) {
    return { kind: "none" };
  }
  const token = await bearerToken();

  try {
    const response = await fetch(
      `${backendUrl()}/animals/${encodeURIComponent(animalId)}/my-application`,
      { cache: "no-store", headers: { Authorization: `Bearer ${token}` } },
    );
    if (response.status === 404) {
      return { kind: "none" };
    }
    if (!response.ok) {
      return { kind: "unavailable" };
    }
    const payload: unknown = await response.json();
    return isMyApplication(payload)
      ? { kind: "active", application: payload }
      : { kind: "unavailable" };
  } catch {
    return { kind: "unavailable" };
  }
}

// Never throws on a backend failure, like getMyApplication.
export async function getMyRequests(): Promise<MyRequestsResult> {
  const token = await bearerToken();

  try {
    const response = await fetch(`${backendUrl()}/me/applications`, {
      cache: "no-store",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      return { kind: "unavailable" };
    }
    const payload: unknown = await response.json();
    return Array.isArray(payload) && payload.every(isSentRequest)
      ? { kind: "ok", requests: payload }
      : { kind: "unavailable" };
  } catch {
    return { kind: "unavailable" };
  }
}

export async function getReceivedRequests(): Promise<ReceivedRequestsResult> {
  const token = await bearerToken();

  try {
    const response = await fetch(
      `${backendUrl()}/me/received-applications`,
      {
        cache: "no-store",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!response.ok) {
      return { kind: "unavailable" };
    }
    const payload: unknown = await response.json();
    return Array.isArray(payload) && payload.every(isReceivedRequest)
      ? { kind: "ok", requests: payload }
      : { kind: "unavailable" };
  } catch {
    return { kind: "unavailable" };
  }
}

function withdrawProblem(kind: WithdrawProblem): WithdrawOutcome {
  return { ok: false, problem: kind, message: WITHDRAW_MESSAGES[kind] };
}

export async function withdrawRequest(
  applicationId: string,
): Promise<WithdrawOutcome> {
  if (!UUID_PATTERN.test(applicationId)) {
    return withdrawProblem("not-found");
  }
  // redirect() throws, so this stays outside the try/catch below.
  const token = await bearerToken();

  let response: Response;
  try {
    response = await fetch(
      `${backendUrl()}/applications/${encodeURIComponent(applicationId)}/withdraw`,
      {
        method: "POST",
        cache: "no-store",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
  } catch {
    return withdrawProblem("unavailable");
  }

  if (response.ok) {
    return { ok: true };
  }
  if (response.status === 404) {
    return withdrawProblem("not-found");
  }
  if (response.status === 409) {
    return withdrawProblem("not-active");
  }
  return withdrawProblem("unavailable");
}

function confirmHandoverProblem(
  kind: ConfirmHandoverProblem,
): ConfirmHandoverOutcome {
  return { ok: false, problem: kind, message: CONFIRM_HANDOVER_MESSAGES[kind] };
}

export async function confirmHandover(
  applicationId: string,
): Promise<ConfirmHandoverOutcome> {
  if (!UUID_PATTERN.test(applicationId)) {
    return confirmHandoverProblem("not-found");
  }
  // redirect() throws, so this stays outside the try/catch below.
  const token = await bearerToken();

  let response: Response;
  try {
    response = await fetch(
      `${backendUrl()}/applications/${encodeURIComponent(applicationId)}/confirm-handover`,
      {
        method: "POST",
        cache: "no-store",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
  } catch {
    return confirmHandoverProblem("unavailable");
  }

  if (response.ok) {
    return { ok: true };
  }
  if (response.status === 404) {
    return confirmHandoverProblem("not-found");
  }
  if (response.status === 409) {
    return confirmHandoverProblem("not-confirmable");
  }
  return confirmHandoverProblem("unavailable");
}

function tickProblem(kind: TickProblem): TickOutcome {
  return { ok: false, problem: kind, message: TICK_MESSAGES[kind] };
}

export async function setHandoverItem(
  applicationId: string,
  item: string,
  checked: boolean,
): Promise<TickOutcome> {
  if (!UUID_PATTERN.test(applicationId)) {
    return tickProblem("not-found");
  }
  // redirect() throws, so this stays outside the try/catch below.
  const token = await bearerToken();

  let response: Response;
  try {
    response = await fetch(
      `${backendUrl()}/applications/${encodeURIComponent(applicationId)}/handover/${encodeURIComponent(item)}`,
      {
        method: "PUT",
        cache: "no-store",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ checked }),
      },
    );
  } catch {
    return tickProblem("unavailable");
  }

  if (response.ok) {
    const payload: unknown = await response.json();
    return isChecklist(payload)
      ? { ok: true, checked: payload.checked }
      : tickProblem("unavailable");
  }
  if (response.status === 404) {
    return tickProblem("not-found");
  }
  if (response.status === 409) {
    return tickProblem("not-tickable");
  }
  // A 422 is an item or body this page never sends, so it is not the person's to fix.
  return tickProblem("unavailable");
}

// The backend's 409 on an answer has two causes: the request is no longer open, or
// the animal is already reserved for another request.
const ANSWER_CONFLICT_CODES: Record<string, AnswerProblem> = {
  invalid_transition: "not-active",
  animal_not_available: "animal-reserved",
};

function answerProblem(kind: AnswerProblem): AnswerOutcome {
  return { ok: false, problem: kind, message: ANSWER_MESSAGES[kind] };
}

async function answerConflict(response: Response): Promise<AnswerProblem> {
  try {
    const { detail } = (await response.json()) as {
      detail?: { code?: unknown };
    };
    const code = detail?.code;
    return typeof code === "string" && Object.hasOwn(ANSWER_CONFLICT_CODES, code)
      ? ANSWER_CONFLICT_CODES[code]
      : "unavailable";
  } catch {
    return "unavailable";
  }
}

export async function answerRequest(
  applicationId: string,
  answer: OwnerAnswer,
  note: string,
): Promise<AnswerOutcome> {
  if (!UUID_PATTERN.test(applicationId)) {
    return answerProblem("not-found");
  }
  // redirect() throws, so this stays outside the try/catch below.
  const token = await bearerToken();

  let response: Response;
  try {
    response = await fetch(
      `${backendUrl()}/applications/${encodeURIComponent(applicationId)}/${answer}`,
      {
        method: "POST",
        cache: "no-store",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ note: note.trim() === "" ? null : note }),
      },
    );
  } catch {
    return answerProblem("unavailable");
  }

  if (response.ok) {
    return { ok: true };
  }
  if (response.status === 404) {
    return answerProblem("not-found");
  }
  if (response.status === 409) {
    return answerProblem(await answerConflict(response));
  }
  if (response.status === 422) {
    return answerProblem("invalid-note");
  }
  return answerProblem("unavailable");
}
