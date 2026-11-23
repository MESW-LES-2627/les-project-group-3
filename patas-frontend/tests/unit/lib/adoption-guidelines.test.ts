import { describe, expect, it } from "vitest";

import { ADOPTION_GUIDELINES, showsGuidelines } from "@/lib/adoption-guidelines";
import { APPLICATION_STATUS } from "@/lib/adoption-status";

describe("AT-26: guidelines next to an accepted request", () => {
  it("shows them only while the request is accepted", () => {
    for (const status of APPLICATION_STATUS) {
      expect(showsGuidelines(status)).toBe(status === "accepted");
    }
  });

  it("covers suggested questions, safety tips and that adoption is not a sale", () => {
    const titles = ADOPTION_GUIDELINES.map((step) => step.title);
    expect(titles).toEqual([
      "Get to know the animal",
      "Get to know the new home",
      "Meet safely",
      "Adoption is not a sale",
      "Plan the handover",
    ]);
  });
});
