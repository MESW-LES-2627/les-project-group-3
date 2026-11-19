"use server";

import { parseUsername, USERNAME_TAKEN } from "@/lib/username";
import { isUsernameAvailable, updateMe } from "@/lib/username-api";

export type UsernameResult = { ok: true } | { ok: false; error: string };

// Asked before the account is created, so a taken username is refused up front.
export async function checkUsername(raw: string): Promise<UsernameResult> {
  const parsed = parseUsername(raw);
  if (!parsed.ok) {
    return parsed;
  }
  const availability = await isUsernameAvailable(parsed.username);
  if (!availability.ok) {
    return availability;
  }
  return availability.available
    ? { ok: true }
    : { ok: false, error: USERNAME_TAKEN };
}

// After sign-up: the new account claims the username it asked for.
export async function claimUsername(raw: string): Promise<UsernameResult> {
  const parsed = parseUsername(raw);
  if (!parsed.ok) {
    return parsed;
  }
  return updateMe({ username: parsed.username });
}
