import { describe, expect, it } from "vitest";

import { expectStatus } from "../../../scripts/seed-demo.mjs";

describe("demo seeder response checks", () => {
  it("leaves a successful response body available for parsing", async () => {
    const response = new Response('{"animals":[]}', { status: 200 });

    await expectStatus(response, 200, "load catalog");

    await expect(response.json()).resolves.toEqual({ animals: [] });
  });

  it("includes the response body when a request fails", async () => {
    const response = new Response("backend unavailable", { status: 503 });

    await expect(expectStatus(response, 200, "load catalog")).rejects.toThrow(
      "load catalog failed (HTTP 503): backend unavailable",
    );
  });
});
