import { describe, expect, it } from "vitest";

import { unpublishConfirmation } from "@/lib/confirmation";

describe("unpublishConfirmation", () => {
  it("names the animal and says it can be republished", () => {
    expect(unpublishConfirmation("Rex")).toEqual({
      title: "Unpublish Rex?",
      message: "Rex will no longer appear in the catalog. You can republish later.",
    });
  });
});
