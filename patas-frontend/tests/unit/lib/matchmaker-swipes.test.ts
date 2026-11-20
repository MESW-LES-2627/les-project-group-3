import { describe, expect, it } from "vitest";

import {
  isSwipeAnimal,
  isSwipeDisposition,
  movesOn,
  reasonKindLabel,
  SWIPE_MESSAGES,
  type SwipeFailure,
} from "@/lib/matchmaker-swipes";

const animal = {
  id: "00000000-0000-4000-8000-000000000001",
  owner_id: "00000000-0000-4000-8000-000000000002",
  owner_name: "Ana",
  owner_username: "ana_owner",
  name: "Rex",
  species: "dog",
  age_in_months: 36,
  district: "porto",
  size: "medium",
  adoption_status: "available",
  fit: {
    score: 82,
    is_compatible: true,
    reasons: [{ text: "Fits your routine.", kind: "strength" }],
  },
  requested: false,
};

describe("Matchmaker swipe responses", () => {
  it("accepts a complete animal and rejects incomplete or malformed fits", () => {
    expect(isSwipeAnimal(animal)).toBe(true);
    expect(isSwipeAnimal({ ...animal, fit: { score: 120 } })).toBe(false);
    expect(isSwipeAnimal({ ...animal, owner_id: undefined })).toBe(false);
    expect(isSwipeAnimal({ ...animal, requested: undefined })).toBe(false);
  });

  it("accepts only passed and saved swipe decisions", () => {
    expect(isSwipeDisposition("passed")).toBe(true);
    expect(isSwipeDisposition("saved")).toBe(true);
    expect(isSwipeDisposition("liked")).toBe(false);
  });

  it("labels each compatibility reason kind", () => {
    expect(reasonKindLabel("strength")).toBe("Fits");
    expect(reasonKindLabel("concern")).toBe("Worth checking");
    expect(reasonKindLabel("unknown")).toBe("Not provided");
  });
});

describe("movesOn", () => {
  function failed(problem: SwipeFailure) {
    return { ok: false as const, problem, message: SWIPE_MESSAGES[problem] };
  }

  it("moves on after a recorded swipe", () => {
    expect(movesOn({ ok: true })).toBe(true);
  });

  it("moves on from an animal that can never be swiped again", () => {
    expect(movesOn(failed("not-available"))).toBe(true);
    expect(movesOn(failed("already-swiped"))).toBe(true);
  });

  it("stays on the card when trying again could work", () => {
    expect(movesOn(failed("unavailable"))).toBe(false);
    expect(movesOn(failed("no-profile"))).toBe(false);
  });
});
