import { describe, expect, it } from "vitest";

import {
  isSwipeAnimal,
  isSwipeDisposition,
  reasonKindLabel,
} from "@/lib/matchmaker-swipes";

const animal = {
  id: "00000000-0000-4000-8000-000000000001",
  owner_id: "00000000-0000-4000-8000-000000000002",
  owner_name: "Ana",
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
};

describe("Matchmaker swipe responses", () => {
  it("accepts a complete animal and rejects incomplete or malformed fits", () => {
    expect(isSwipeAnimal(animal)).toBe(true);
    expect(isSwipeAnimal({ ...animal, fit: { score: 120 } })).toBe(false);
    expect(isSwipeAnimal({ ...animal, owner_id: undefined })).toBe(false);
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
