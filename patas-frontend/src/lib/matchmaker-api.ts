// Server-side only: every call from the frontend to the backend's Matchmaker profile
// endpoints (ADR 0008) goes through here. The browser never calls FastAPI directly
// (ADR 0005): these functions run on the Next.js server, from the page and from the
// server actions, and add the signed-in user's token to each request.
//
// This file only handles HTTP. The rules (valid values, one profile per user,
// privacy) are the backend's.
import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { auth } from "@/lib/auth";
import { backendUrl } from "@/lib/backend";
import {
  isMatchmakerAnswers,
  type DeleteOutcome,
  type MatchmakerAnswers,
  type SaveOutcome,
} from "@/lib/matchmaker-profile";

const UNAVAILABLE = "The service is unavailable, please try again.";

// Checked on every call, not only on the page: a Server Action is a public endpoint.
// redirect() throws, so this must stay outside any try/catch.
async function bearerToken(): Promise<string> {
  const requestHeaders = await headers();
  const session = await auth.api.getSession({ headers: requestHeaders });
  if (!session) {
    redirect("/login");
  }
  const { token } = await auth.api.getToken({ headers: requestHeaders });
  return token;
}

// null means the backend could not be reached.
async function callBackend(
  token: string,
  method: "GET" | "PUT" | "DELETE",
  body?: MatchmakerAnswers,
): Promise<Response | null> {
  try {
    return await fetch(`${backendUrl()}/me/matchmaker-profile`, {
      method,
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${token}`,
        ...(body && { "Content-Type": "application/json" }),
      },
      body: body && JSON.stringify(body),
    });
  } catch {
    return null;
  }
}

export async function getMatchmakerProfile(): Promise<MatchmakerAnswers | null> {
  const response = await callBackend(await bearerToken(), "GET");
  if (response === null) {
    throw new Error("Unable to load the Matchmaker profile: service unavailable");
  }
  if (response.status === 404) {
    return null; // nothing saved yet: the page shows the empty form
  }
  if (!response.ok) {
    throw new Error(
      `Unable to load the Matchmaker profile: backend returned ${response.status}`,
    );
  }
  const payload: unknown = await response.json();
  if (!isMatchmakerAnswers(payload)) {
    throw new Error("Unable to load the Matchmaker profile: invalid data");
  }
  return payload;
}

export async function saveMatchmakerProfile(
  answers: MatchmakerAnswers,
): Promise<SaveOutcome> {
  const response = await callBackend(await bearerToken(), "PUT", answers);
  if (response === null) {
    return { ok: false, error: UNAVAILABLE };
  }
  if (response.status === 422) {
    // Domain rule errors are a string; FastAPI's type errors are a list.
    const { detail } = (await response.json()) as { detail: unknown };
    return {
      ok: false,
      error:
        typeof detail === "string"
          ? detail
          : "Some answers are not valid. Please check them and try again.",
    };
  }
  if (!response.ok) {
    return {
      ok: false,
      error: `Saving failed (backend returned ${response.status})`,
    };
  }
  const payload: unknown = await response.json();
  if (!isMatchmakerAnswers(payload)) {
    return { ok: false, error: "Saving failed (the backend sent invalid data)" };
  }
  return { ok: true, answers: payload };
}

export async function deleteMatchmakerProfile(): Promise<DeleteOutcome> {
  const response = await callBackend(await bearerToken(), "DELETE");
  if (response === null) {
    return { ok: false, error: UNAVAILABLE };
  }
  if (!response.ok) {
    return {
      ok: false,
      error: `Deleting failed (backend returned ${response.status})`,
    };
  }
  return { ok: true };
}
