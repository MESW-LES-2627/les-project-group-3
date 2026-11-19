import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// The sign-in boundary and the network are replaced; how each backend answer becomes
// a result for the person is the code under test.
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

import {
  getSavedAnimals,
  getSwipeFeed,
  recordSwipe,
  removeSavedAnimal,
} from "@/lib/matchmaker-swipes-api";
import { SWIPE_MESSAGES, type SwipeFailure } from "@/lib/matchmaker-swipes";

const ID = "00000000-0000-4000-8000-000000000001";

const animal = {
  id: ID,
  owner_id: "00000000-0000-4000-8000-000000000002",
  owner_name: "Ana",
  owner_username: "ana_owner",
  name: "Rex",
  species: "dog",
  age_in_months: 36,
  district: "porto",
  size: "medium",
  adoption_status: "available",
  fit: null,
  requested: false,
};

const fetchMock = vi.fn<typeof fetch>();

function answer(status: number, body?: unknown) {
  fetchMock.mockResolvedValueOnce(
    body === undefined
      ? new Response(null, { status })
      : Response.json(body, { status }),
  );
}

function failure(problem: SwipeFailure) {
  return { ok: false, problem, message: SWIPE_MESSAGES[problem] };
}

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe.each([
  ["getSwipeFeed", getSwipeFeed, /\/me\/matchmaker\/swipes\/feed$/],
  ["getSavedAnimals", getSavedAnimals, /\/me\/matchmaker\/swipes\/saved$/],
])("%s", (_, load, path) => {
  it("returns the animals the backend sends, with the person's token", async () => {
    answer(200, [animal]);

    expect(await load()).toEqual({ ok: true, animals: [animal] });
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(path);
    expect(new Headers(init?.headers).get("Authorization")).toBe(
      "Bearer test-token",
    );
  });

  it("treats a malformed answer as the service being unavailable", async () => {
    answer(200, [{ ...animal, requested: "yes" }]);

    expect(await load()).toEqual(failure("unavailable"));
  });

  it("treats an error answer as the service being unavailable", async () => {
    answer(500);

    expect(await load()).toEqual(failure("unavailable"));
  });

  it("treats an unreachable backend as the service being unavailable", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("fetch failed"));

    expect(await load()).toEqual(failure("unavailable"));
  });
});

describe("getSwipeFeed without a Matchmaker profile", () => {
  it("asks for the profile first", async () => {
    answer(409, { detail: { code: "matchmaker_profile_required" } });

    expect(await getSwipeFeed()).toEqual(failure("no-profile"));
  });
});

describe("recordSwipe", () => {
  it("sends the decision about the animal", async () => {
    answer(201, {});

    expect(await recordSwipe(ID, "saved")).toEqual({ ok: true });
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(/\/me\/matchmaker\/swipes$/);
    expect(init?.method).toBe("POST");
    expect(JSON.parse(String(init?.body))).toEqual({
      animal_id: ID,
      disposition: "saved",
    });
  });

  it("does not call the backend with a malformed id", async () => {
    expect(await recordSwipe("not-an-id", "saved")).toEqual(
      failure("not-found"),
    );
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it.each([
    ["already_swiped", "already-swiped"],
    ["animal_not_available", "not-available"],
    ["matchmaker_profile_required", "no-profile"],
    ["something_else", "unavailable"],
  ] as const)("maps the 409 code %s to %s", async (code, problem) => {
    answer(409, { detail: { code } });

    expect(await recordSwipe(ID, "passed")).toEqual(failure(problem));
  });

  it("treats a 409 without a readable body as unavailable", async () => {
    fetchMock.mockResolvedValueOnce(new Response("oops", { status: 409 }));

    expect(await recordSwipe(ID, "passed")).toEqual(failure("unavailable"));
  });

  it.each([
    [404, "not-found"],
    [500, "unavailable"],
  ] as const)("maps the answer %i to %s", async (status, problem) => {
    answer(status);

    expect(await recordSwipe(ID, "passed")).toEqual(failure(problem));
  });

  it("treats an unreachable backend as unavailable", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("fetch failed"));

    expect(await recordSwipe(ID, "passed")).toEqual(failure("unavailable"));
  });
});

describe("removeSavedAnimal", () => {
  it("deletes the saved animal", async () => {
    answer(204);

    expect(await removeSavedAnimal(ID)).toEqual({ ok: true });
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(new RegExp(`/me/matchmaker/swipes/${ID}$`));
    expect(init?.method).toBe("DELETE");
  });

  it("does not call the backend with a malformed id", async () => {
    expect(await removeSavedAnimal("../x")).toEqual(failure("not-found"));
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("says when the animal is not in the saved list", async () => {
    answer(404);

    expect(await removeSavedAnimal(ID)).toEqual(failure("not-found"));
  });

  it("treats an unreachable backend as unavailable", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("fetch failed"));

    expect(await removeSavedAnimal(ID)).toEqual(failure("unavailable"));
  });
});
