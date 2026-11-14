import { describe, expect, it } from "vitest";
import { districtLabel } from "@/lib/animal-profile";

describe("districtLabel", () => {
  it("shows the district's name as written, with its accents", () => {
    expect(districtLabel("braganca")).toBe("Bragança");
  });

  it("shows a value it does not know as it came, instead of nothing", () => {
    expect(districtLabel("atlantis")).toBe("atlantis");
  });
});
