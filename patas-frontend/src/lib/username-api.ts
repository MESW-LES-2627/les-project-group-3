// Server-side only: the register and profile pages reach the backend's user
// endpoints (ADR 0024) through here, never from the browser (ADR 0005).
import { backendUrl } from "@/lib/backend";
import { bearerToken } from "@/lib/matchmaker-api";
import { USERNAME_RULE, USERNAME_TAKEN } from "@/lib/username";

const UNAVAILABLE = "The service is unavailable, please try again.";

export type Availability =
  | { ok: true; available: boolean }
  | { ok: false; error: string };

export type ProfileChange = { name?: string; username?: string };
export type ProfileOutcome = { ok: true } | { ok: false; error: string };

// Public: asked before the account exists.
export async function isUsernameAvailable(
  username: string,
): Promise<Availability> {
  let response: Response;
  try {
    response = await fetch(
      `${backendUrl()}/usernames/${encodeURIComponent(username)}`,
      { cache: "no-store" },
    );
  } catch {
    return { ok: false, error: UNAVAILABLE };
  }
  if (response.status === 422) {
    return { ok: false, error: USERNAME_RULE };
  }
  if (!response.ok) {
    return {
      ok: false,
      error: `Checking the username failed (backend returned ${response.status})`,
    };
  }
  const { available } = (await response.json()) as { available: unknown };
  return { ok: true, available: available === true };
}

export async function updateMe(change: ProfileChange): Promise<ProfileOutcome> {
  const token = await bearerToken();
  let response: Response;
  try {
    response = await fetch(`${backendUrl()}/me`, {
      method: "PATCH",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(change),
    });
  } catch {
    return { ok: false, error: UNAVAILABLE };
  }
  if (response.ok) {
    return { ok: true };
  }
  if (response.status === 409) {
    return { ok: false, error: USERNAME_TAKEN };
  }
  if (response.status === 422) {
    // Domain rule errors are a string; FastAPI's type errors are a list.
    const { detail } = (await response.json()) as { detail: unknown };
    return {
      ok: false,
      error: typeof detail === "string" ? detail : "Please check your details.",
    };
  }
  return {
    ok: false,
    error: `Saving the profile failed (backend returned ${response.status})`,
  };
}
