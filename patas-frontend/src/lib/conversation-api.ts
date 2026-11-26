// Server-side only: the calls from the frontend to the backend's conversation
// endpoints (US-21). The browser never calls FastAPI directly (ADR 0005): this runs
// on the Next.js server and adds the signed-in user's token.
//
// This file only handles HTTP. Who may read or write, and when, is the backend's.
import { UUID_PATTERN } from "@/lib/adoption-api";
import { backendUrl } from "@/lib/backend";
import {
  SEND_MESSAGES,
  isChatMessage,
  messageProblem,
  type MessagesResult,
  type SendOutcome,
  type SendProblem,
} from "@/lib/conversation";
import { bearerToken } from "@/lib/matchmaker-api";

function messagesUrl(applicationId: string): string {
  return `${backendUrl()}/applications/${encodeURIComponent(applicationId)}/messages`;
}

function sendProblem(kind: SendProblem): SendOutcome {
  return { ok: false, problem: kind, message: SEND_MESSAGES[kind] };
}

// The whole conversation, or only the messages after `after`. Never throws on a
// backend failure: the page shows the rest of the request anyway.
export async function getMessages(
  applicationId: string,
  after?: string,
): Promise<MessagesResult> {
  if (!UUID_PATTERN.test(applicationId)) {
    return { kind: "not-found" };
  }
  // redirect() throws, so this stays outside the try/catch below.
  const token = await bearerToken();
  const query =
    after && UUID_PATTERN.test(after)
      ? `?after=${encodeURIComponent(after)}`
      : "";

  try {
    const response = await fetch(`${messagesUrl(applicationId)}${query}`, {
      cache: "no-store",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (response.status === 404) {
      return { kind: "not-found" };
    }
    if (!response.ok) {
      return { kind: "unavailable" };
    }
    const payload: unknown = await response.json();
    return Array.isArray(payload) && payload.every(isChatMessage)
      ? { kind: "ok", messages: payload }
      : { kind: "unavailable" };
  } catch {
    return { kind: "unavailable" };
  }
}

export async function postMessage(
  applicationId: string,
  body: string,
): Promise<SendOutcome> {
  if (!UUID_PATTERN.test(applicationId)) {
    return sendProblem("not-found");
  }
  const token = await bearerToken();

  let response: Response;
  try {
    response = await fetch(messagesUrl(applicationId), {
      method: "POST",
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ body }),
    });
  } catch {
    return sendProblem("unavailable");
  }

  if (response.status === 201) {
    const payload: unknown = await response.json();
    return isChatMessage(payload)
      ? { ok: true, message: payload }
      : sendProblem("unavailable");
  }
  if (response.status === 404) {
    return sendProblem("not-found");
  }
  if (response.status === 409) {
    return sendProblem("closed");
  }
  if (response.status === 422) {
    // The backend has the same rules as messageProblem, so this names the problem.
    return sendProblem(messageProblem(body) ?? "unavailable");
  }
  return sendProblem("unavailable");
}
