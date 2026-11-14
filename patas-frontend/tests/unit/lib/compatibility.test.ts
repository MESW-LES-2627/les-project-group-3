import { describe, expect, it } from "vitest";
import { groupReasons, isFit, isMode, type Reason } from "@/lib/compatibility";

describe("groupReasons", () => {
  it("groups by kind in display order and keeps the backend's order inside each group", () => {
    const reasons: Reason[] = [
      { text: "Quiet street", kind: "strength" },
      { text: "Small garden", kind: "concern" },
      { text: "Good with children", kind: "strength" },
      { text: "Other pets", kind: "unknown" },
    ];
    expect(groupReasons(reasons)).toEqual([
      {
        kind: "strength",
        heading: "What fits",
        texts: ["Quiet street", "Good with children"],
      },
      { kind: "concern", heading: "Worth checking", texts: ["Small garden"] },
      {
        kind: "unknown",
        heading: "The owner didn't say",
        texts: ["Other pets"],
      },
    ]);
  });

  it("leaves out a group without reasons", () => {
    const groups = groupReasons([{ text: "Quiet", kind: "strength" }]);
    expect(groups.map((g) => g.kind)).toEqual(["strength"]);
  });

  it("returns nothing when there are no reasons", () => {
    expect(groupReasons([])).toEqual([]);
  });
});

describe("isMode", () => {
  it("knows the two modes and nothing else", () => {
    expect(isMode("loose")).toBe(true);
    expect(isMode("strict")).toBe(true);
    expect(isMode("medium")).toBe(false);
    expect(isMode(undefined)).toBe(false);
  });
});

describe("isFit", () => {
  const fit = {
    mode: "strict",
    score: 72,
    is_compatible: true,
    reasons: [{ text: "Quiet", kind: "strength" }],
  };

  it("accepts the backend's response", () => {
    expect(isFit(fit)).toBe(true);
  });

  it("rejects an unknown mode and an unknown kind of reason", () => {
    expect(isFit({ ...fit, mode: "medium" })).toBe(false);
    expect(isFit({ ...fit, reasons: [{ text: "Quiet", kind: "maybe" }] })).toBe(
      false,
    );
  });

  it("rejects a list where a reason is not an object", () => {
    expect(isFit({ ...fit, reasons: ["Quiet"] })).toBe(false);
    expect(isFit({ ...fit, reasons: [null] })).toBe(false);
  });

  it("rejects a mistyped score or missing reasons", () => {
    expect(isFit({ ...fit, score: "72" })).toBe(false);
    expect(isFit({ ...fit, reasons: undefined })).toBe(false);
    expect(isFit(null)).toBe(false);
  });
});
