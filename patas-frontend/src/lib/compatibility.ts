// Types and wording for "how well does this animal fit my home". Plain TypeScript:
// no React and no server imports, so server and client components can share it.
// The values mirror the backend response of GET /animals/{id}/compatibility; the
// backend stays the source of truth for the score, the reasons and what fits.

export const MODES = ["loose", "strict"] as const;
export type Mode = (typeof MODES)[number];
export const DEFAULT_MODE: Mode = "loose";

// Placeholder names: the team still has to agree on the wording.
export const MODE_LABEL: Record<Mode, string> = {
  loose: "Flexible",
  strict: "Strict",
};

export const REASON_KINDS = ["strength", "concern", "unknown"] as const;
export type ReasonKind = (typeof REASON_KINDS)[number];

export type Reason = { text: string; kind: ReasonKind };

export type Fit = {
  mode: Mode;
  score: number;
  is_compatible: boolean;
  reasons: Reason[];
};

export type FitProblem =
  | "no-profile"
  | "own-animal"
  | "not-found"
  | "unavailable";

export type FitOutcome =
  | { ok: true; fit: Fit }
  | { ok: false; problem: FitProblem; message: string };

export function isMode(value: unknown): value is Mode {
  return (
    typeof value === "string" && (MODES as readonly string[]).includes(value)
  );
}

function isReason(value: unknown): value is Reason {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const { text, kind } = value as Record<string, unknown>;
  return (
    typeof text === "string" &&
    typeof kind === "string" &&
    (REASON_KINDS as readonly string[]).includes(kind)
  );
}

export function isFit(value: unknown): value is Fit {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const { mode, score, is_compatible, reasons } = value as Record<
    string,
    unknown
  >;
  return (
    isMode(mode) &&
    typeof score === "number" &&
    typeof is_compatible === "boolean" &&
    Array.isArray(reasons) &&
    reasons.every(isReason)
  );
}

// The order the groups are shown in, with the heading of each.
export const REASON_GROUPS: readonly { kind: ReasonKind; heading: string }[] = [
  { kind: "strength", heading: "What fits" },
  { kind: "concern", heading: "Worth checking" },
  { kind: "unknown", heading: "The owner didn't say" },
];

// Splits the reasons by kind and keeps the backend's order inside each group.
// A group without reasons is left out.
export function groupReasons(
  reasons: readonly Reason[],
): { kind: ReasonKind; heading: string; texts: string[] }[] {
  return REASON_GROUPS.map(({ kind, heading }) => ({
    kind,
    heading,
    texts: reasons.filter((r) => r.kind === kind).map((r) => r.text),
  })).filter((group) => group.texts.length > 0);
}
