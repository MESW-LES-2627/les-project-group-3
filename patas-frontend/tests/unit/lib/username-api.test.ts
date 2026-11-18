import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// The sign-in boundary and the network are replaced; how each backend answer
// becomes a result for the person is the code under test.
vi.mock("next/headers", () => ({ headers: vi.fn(async () => new Headers()) }));
vi.mock("next/navigation", () => ({
  redirect: vi.fn((path: string) => {
    throw new Error(`REDIRECT:${path}`);
  }),
}));
vi.mock("@/lib/auth", () => ({
  auth: {
    api: {
      getSession: vi.fn(async () => ({ user: "u1" })),
      getToken: vi.fn(async () => ({ token: "test-token" })),
    },
  },
}));

import { USERNAME_RULE, USERNAME_TAKEN } from "@/lib/username";
import { isUsernameAvailable, updateMe } from "@/lib/username-api";

const fetchMock = vi.fn<typeof fetch>();

function reply(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status });
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  fetchMock.mockReset();
});

describe("isUsernameAvailable", () => {
  it("asks the public endpoint, escaping the username", async () => {
    fetchMock.mockResolvedValue(reply(200, { username: "a.b", available: true }));

    expect(await isUsernameAvailable("a.b")).toEqual({
      ok: true,
      available: true,
    });
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(/\/usernames\/a\.b$/);
    expect(new Headers(init?.headers).has("Authorization")).toBe(false);
  });

  it("reports a taken username", async () => {
    fetchMock.mockResolvedValue(reply(200, { username: "ana", available: false }));

    expect(await isUsernameAvailable("ana")).toEqual({
      ok: true,
      available: false,
    });
  });

  it("explains the rule when the backend refuses the format", async () => {
    fetchMock.mockResolvedValue(reply(422, { detail: "bad" }));

    expect(await isUsernameAvailable("a b")).toEqual({
      ok: false,
      error: USERNAME_RULE,
    });
  });

  it("reports another backend failure and an unreachable backend", async () => {
    fetchMock.mockResolvedValueOnce(reply(500, {}));
    expect(await isUsernameAvailable("ana")).toEqual({
      ok: false,
      error: "Checking the username failed (backend returned 500)",
    });

    fetchMock.mockRejectedValueOnce(new TypeError("fetch failed"));
    expect(await isUsernameAvailable("ana")).toEqual({
      ok: false,
      error: "The service is unavailable, please try again.",
    });
  });
});

describe("updateMe", () => {
  it("sends only the given fields with the user's token", async () => {
    fetchMock.mockResolvedValue(reply(200, {}));

    expect(await updateMe({ username: "ana_demo" })).toEqual({ ok: true });
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(/\/me$/);
    expect(init?.method).toBe("PATCH");
    expect(JSON.parse(String(init?.body))).toEqual({ username: "ana_demo" });
    expect(new Headers(init?.headers).get("Authorization")).toBe(
      "Bearer test-token",
    );
  });

  it("says the username is taken on a conflict", async () => {
    fetchMock.mockResolvedValue(
      reply(409, { detail: { code: "username_taken", message: "taken" } }),
    );

    expect(await updateMe({ username: "ana" })).toEqual({
      ok: false,
      error: USERNAME_TAKEN,
    });
  });

  it("shows the backend's rule message, or a general one for type errors", async () => {
    fetchMock.mockResolvedValueOnce(reply(422, { detail: "name must not be blank" }));
    expect(await updateMe({ name: " " })).toEqual({
      ok: false,
      error: "name must not be blank",
    });

    fetchMock.mockResolvedValueOnce(reply(422, { detail: [{ msg: "x" }] }));
    expect(await updateMe({})).toEqual({
      ok: false,
      error: "Please check your details.",
    });
  });

  it("reports another backend failure and an unreachable backend", async () => {
    fetchMock.mockResolvedValueOnce(reply(500, {}));
    expect(await updateMe({ name: "Ana" })).toEqual({
      ok: false,
      error: "Saving the profile failed (backend returned 500)",
    });

    fetchMock.mockRejectedValueOnce(new TypeError("fetch failed"));
    expect(await updateMe({ name: "Ana" })).toEqual({
      ok: false,
      error: "The service is unavailable, please try again.",
    });
  });
});
