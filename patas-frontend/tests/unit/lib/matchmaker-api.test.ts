import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// The sign-in boundary and the network are replaced; how each backend answer becomes
// a result for the person (and when it throws) is the code under test.
const session = vi.hoisted(() => ({ current: { user: "u1" } as unknown }));
vi.mock("next/headers", () => ({ headers: vi.fn(async () => new Headers()) }));
vi.mock("next/navigation", () => ({
  redirect: vi.fn((path: string) => {
    throw new Error(`REDIRECT:${path}`);
  }),
}));
vi.mock("@/lib/auth", () => ({
  auth: {
    api: {
      getSession: vi.fn(async () => session.current),
      getToken: vi.fn(async () => ({ token: "test-token" })),
    },
  },
}));

import {
  bearerToken,
  deleteMatchmakerProfile,
  getMatchmakerProfile,
  saveMatchmakerProfile,
} from "@/lib/matchmaker-api";
import type { MatchmakerAnswers } from "@/lib/matchmaker-profile";

const answers: MatchmakerAnswers = {
  housing: "apartment",
  time_away: "half_day",
  activity: "moderate",
  experience: "some",
  has_children: false,
  has_dogs: true,
  has_cats: false,
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
  session.current = { user: "u1" };
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("bearerToken", () => {
  it("returns the token of a signed-in person", async () => {
    expect(await bearerToken()).toBe("test-token");
  });

  it("sends a person without a session to the login page", async () => {
    session.current = null;

    await expect(bearerToken()).rejects.toThrow("REDIRECT:/login");
  });
});

describe("getMatchmakerProfile", () => {
  it("returns the saved answers", async () => {
    answer(200, answers);

    expect(await getMatchmakerProfile()).toEqual(answers);
    const [, init] = fetchMock.mock.calls[0];
    expect(init?.method).toBe("GET");
    expect(init?.body).toBeUndefined();
    expect(new Headers(init?.headers).get("Authorization")).toBe(
      "Bearer test-token",
    );
  });

  it("returns null when nothing is saved yet, so the page shows the empty form", async () => {
    answer(404);

    expect(await getMatchmakerProfile()).toBeNull();
  });

  it("throws when the backend errors, so the error page shows instead of an empty form", async () => {
    answer(500);

    await expect(getMatchmakerProfile()).rejects.toThrow(
      "backend returned 500",
    );
  });

  it("throws when the saved data is not a profile", async () => {
    answer(200, { housing: "castle" });

    await expect(getMatchmakerProfile()).rejects.toThrow("invalid data");
  });

  it("throws when the network fails", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("fetch failed"));

    await expect(getMatchmakerProfile()).rejects.toThrow(
      "service unavailable",
    );
  });
});

describe("saveMatchmakerProfile", () => {
  it("sends the answers as JSON and returns what was saved", async () => {
    answer(200, answers);

    expect(await saveMatchmakerProfile(answers)).toEqual({
      ok: true,
      answers,
    });
    const [, init] = fetchMock.mock.calls[0];
    expect(init?.method).toBe("PUT");
    expect(init?.body).toBe(JSON.stringify(answers));
    expect(new Headers(init?.headers).get("Content-Type")).toBe(
      "application/json",
    );
  });

  it("shows the rule the domain refused in its own words", async () => {
    answer(422, { detail: "A profile needs a housing answer" });

    expect(await saveMatchmakerProfile(answers)).toEqual({
      ok: false,
      error: "A profile needs a housing answer",
    });
  });

  it("shows a general message for FastAPI's list of type errors", async () => {
    answer(422, { detail: [{ msg: "bad" }] });

    expect(await saveMatchmakerProfile(answers)).toEqual({
      ok: false,
      error: "Some answers are not valid. Please check them and try again.",
    });
  });

  it("names the status of any other failure", async () => {
    answer(503);

    expect(await saveMatchmakerProfile(answers)).toEqual({
      ok: false,
      error: "Saving failed (backend returned 503)",
    });
  });

  it("does not trust a 200 that is not a profile", async () => {
    answer(200, { nope: true });

    expect(await saveMatchmakerProfile(answers)).toMatchObject({ ok: false });
  });

  it("reports the service as unavailable when the network fails", async () => {
    fetchMock.mockRejectedValueOnce(new Error("down"));

    expect(await saveMatchmakerProfile(answers)).toEqual({
      ok: false,
      error: "The service is unavailable, please try again.",
    });
  });
});

describe("deleteMatchmakerProfile", () => {
  it("deletes without a body", async () => {
    answer(204);

    expect(await deleteMatchmakerProfile()).toEqual({ ok: true });
    const [, init] = fetchMock.mock.calls[0];
    expect(init?.method).toBe("DELETE");
    expect(init?.body).toBeUndefined();
  });

  it("names the status of a failure", async () => {
    answer(500);

    expect(await deleteMatchmakerProfile()).toEqual({
      ok: false,
      error: "Deleting failed (backend returned 500)",
    });
  });

  it("reports the service as unavailable when the network fails", async () => {
    fetchMock.mockRejectedValueOnce(new Error("down"));

    expect(await deleteMatchmakerProfile()).toMatchObject({ ok: false });
  });
});
