import { describe, expect, it } from "vitest";

import { expectStatus } from "../../../scripts/animal-generation.mjs";

describe("animal generator response checks", () => {
  it("leaves a successful response body available for parsing", async () => {
    const response = new Response('{"token":"demo-token"}', { status: 200 });

    await expectStatus(response, 200, "obtain token");

    await expect(response.json()).resolves.toEqual({ token: "demo-token" });
  });

  it("includes the response body when a request fails", async () => {
    const response = new Response("authentication failed", { status: 401 });

    await expect(expectStatus(response, 200, "obtain token")).rejects.toThrow(
      "obtain token failed (HTTP 401): authentication failed",
    );
  });
});
