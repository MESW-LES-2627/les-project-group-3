// The username rule, checked here only to answer before a round trip; the backend
// decides (ADR 0024). Uniqueness ignores case, so only the backend can check it.
const USERNAME = /^[A-Za-z0-9_][A-Za-z0-9_.]{1,28}[A-Za-z0-9_]$/;

export const USERNAME_RULE =
  "Use 3 to 30 letters, digits, _ or ., not starting or ending with a dot.";
export const USERNAME_TAKEN = "That username is already taken.";

export type ParsedUsername =
  | { ok: true; username: string }
  | { ok: false; error: string };

export function parseUsername(raw: unknown): ParsedUsername {
  const username = typeof raw === "string" ? raw.trim() : "";
  return USERNAME.test(username)
    ? { ok: true, username }
    : { ok: false, error: USERNAME_RULE };
}

// "Ana Demo (@ana_demo)": names can repeat, the username tells people apart.
export function personLabel(name: string, username: string): string {
  return `${name} (@${username})`;
}
