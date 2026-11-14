import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Only the sign-in boundary and the network are replaced: how each backend answer
// becomes a message for the person is the code under test.
vi.mock("@/lib/matchmaker-api", () => ({
  bearerToken: vi.fn(async () => "test-token"),
}));

import { getFit } from "@/lib/compatibility-api";

const ID = "3f2b8c1e-4d5a-4b6c-8d7e-9f0a1b2c3d4e";
const fit = {
  mode: "strict",
  score: 72,
  is_compatible: true,
  reasons: [{ text: "Quiet street", kind: "strength" }],
};

const fetchMock = vi.fn<typeof fetch>();

function answer(status: number, body?: unknown) {
  fetchMock.mockResolvedValueOnce(
    body === undefined
      ? new Response(null, { status })
      : Response.json(body, { status }),
  );
}

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("getFit", () => {
  it("asks for the chosen mode with the signed-in person's token and returns the fit", async () => {
    answer(200, fit);

    expect(await getFit(ID, "strict")).toEqual({ ok: true, fit });
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(
      new RegExp(`/animals/${ID}/compatibility\\?mode=strict$`),
    );
    expect(new Headers(init?.headers).get("Authorization")).toBe(
      "Bearer test-token",
    );
  });

  it("does not call the backend for something that is not an animal id", async () => {
    expect(await getFit("nope", "loose")).toMatchObject({
      ok: false,
      problem: "not-found",
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it.each([
    [409, undefined, "no-profile"],
    [404, undefined, "not-found"],
    [500, undefined, "unavailable"],
    // The domain refusal is text; FastAPI's type errors are a list.
    [422, { detail: "Cannot rate your own animal" }, "own-animal"],
    [422, { detail: [{ msg: "bad mode" }] }, "unavailable"],
  ])("maps the answer %i %j to %s", async (status, body, problem) => {
    answer(status, body);

    expect(await getFit(ID, "loose")).toMatchObject({ ok: false, problem });
  });

  it("does not trust a 200 whose body is not a fit", async () => {
    answer(200, { score: "high" });

    expect(await getFit(ID, "loose")).toMatchObject({
      ok: false,
      problem: "unavailable",
    });
  });

  it("reports the service as unavailable when the network fails, without throwing", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("fetch failed"));

    expect(await getFit(ID, "loose")).toMatchObject({
      ok: false,
      problem: "unavailable",
    });
  });
});
