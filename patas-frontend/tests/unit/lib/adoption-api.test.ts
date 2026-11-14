import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Only the sign-in boundary and the network are replaced: how each backend answer
// becomes a message for the person is the code under test.
vi.mock("@/lib/matchmaker-api", () => ({
  bearerToken: vi.fn(async () => "test-token"),
}));

import {
  getMyApplication,
  getMyRequests,
  getReceivedRequests,
  requestToAdopt,
  withdrawRequest,
} from "@/lib/adoption-api";

const ID = "3f2b8c1e-4d5a-4b6c-8d7e-9f0a1b2c3d4e";
const application = { id: ID, animal_id: ID, status: "open", note: "Hi" };
const sentRequest = {
  ...application,
  animal_name: "Bolt",
  owner_note: null,
  created_at: "2026-11-01T10:00:00Z",
};

const receivedRequest = {
  id: ID,
  animal_id: ID,
  animal_name: "Bolt",
  status: "open",
  note: "Hi",
  applicant_profile: {
    housing: "apartment",
    time_away: "half_day",
    activity: "moderate",
    experience: "some",
    has_children: false,
    has_dogs: true,
    has_cats: false,
  },
  compatibility_concerns: ["Its energy is a bit different from yours"],
  created_at: "2026-11-01T10:00:00Z",
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

describe("requestToAdopt", () => {
  it("sends the note with the signed-in person's token and returns the application", async () => {
    answer(201, application);

    const outcome = await requestToAdopt(ID, "Hi");

    expect(outcome).toEqual({ ok: true, application });
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(new RegExp(`/animals/${ID}/applications$`));
    expect(init?.method).toBe("POST");
    expect(init?.body).toBe(JSON.stringify({ note: "Hi" }));
    expect(new Headers(init?.headers).get("Authorization")).toBe(
      "Bearer test-token",
    );
  });

  it("does not call the backend for something that is not an animal id", async () => {
    const outcome = await requestToAdopt("not-a-uuid", "Hi");

    expect(outcome).toMatchObject({ ok: false, problem: "not-found" });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it.each([
    [403, undefined, "own-animal"],
    [404, undefined, "not-found"],
    [422, undefined, "invalid-note"],
    [500, undefined, "unavailable"],
    [409, { detail: { code: "matchmaker_profile_required" } }, "no-profile"],
    [409, { detail: { code: "already_requested" } }, "already-requested"],
    [409, { detail: { code: "animal_not_available" } }, "not-available"],
  ])("maps the answer %i %j to %s", async (status, body, problem) => {
    answer(status, body);

    expect(await requestToAdopt(ID, "Hi")).toMatchObject({
      ok: false,
      problem,
    });
  });

  it("treats a 409 with a code it does not know as unavailable", async () => {
    answer(409, { detail: { code: "constructor" } });

    expect(await requestToAdopt(ID, "Hi")).toMatchObject({
      problem: "unavailable",
    });
  });

  it("treats a 409 without a readable body as unavailable", async () => {
    answer(409);

    expect(await requestToAdopt(ID, "Hi")).toMatchObject({
      problem: "unavailable",
    });
  });

  it("does not trust a 201 whose body is not an application", async () => {
    answer(201, { id: ID });

    expect(await requestToAdopt(ID, "Hi")).toMatchObject({
      ok: false,
      problem: "unavailable",
    });
  });

  it("reports the service as unavailable when the network fails, without throwing", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("fetch failed"));

    expect(await requestToAdopt(ID, "Hi")).toMatchObject({
      ok: false,
      problem: "unavailable",
    });
  });
});

describe("getMyApplication", () => {
  it("returns the active application", async () => {
    answer(200, application);

    expect(await getMyApplication(ID)).toEqual({
      kind: "active",
      application,
    });
  });

  it("returns none when there is no request, and for an invalid id without a call", async () => {
    answer(404);
    expect(await getMyApplication(ID)).toEqual({ kind: "none" });

    fetchMock.mockClear();
    expect(await getMyApplication("nope")).toEqual({ kind: "none" });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("never throws: an error status, a bad body or a network failure is unavailable", async () => {
    answer(500);
    expect(await getMyApplication(ID)).toEqual({ kind: "unavailable" });

    answer(200, { nope: true });
    expect(await getMyApplication(ID)).toEqual({ kind: "unavailable" });

    fetchMock.mockRejectedValueOnce(new Error("down"));
    expect(await getMyApplication(ID)).toEqual({ kind: "unavailable" });
  });
});

describe("getMyRequests", () => {
  it("returns the requests I sent", async () => {
    answer(200, [sentRequest]);

    expect(await getMyRequests()).toEqual({
      kind: "ok",
      requests: [sentRequest],
    });
  });

  it("is unavailable when even one item is malformed", async () => {
    answer(200, [sentRequest, { id: "x" }]);

    expect(await getMyRequests()).toEqual({ kind: "unavailable" });
  });

  it("is unavailable on an error status, a non-list body or a network failure", async () => {
    answer(500);
    expect(await getMyRequests()).toEqual({ kind: "unavailable" });

    answer(200, { requests: [] });
    expect(await getMyRequests()).toEqual({ kind: "unavailable" });

    fetchMock.mockRejectedValueOnce(new Error("down"));
    expect(await getMyRequests()).toEqual({ kind: "unavailable" });
  });
});

describe("getReceivedRequests", () => {
  it("returns the requests for my animals, asking with my token", async () => {
    answer(200, [receivedRequest]);

    expect(await getReceivedRequests()).toEqual({
      kind: "ok",
      requests: [receivedRequest],
    });
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(/\/me\/received-applications$/);
    expect(init?.headers).toEqual({ Authorization: "Bearer test-token" });
  });

  it("is unavailable when even one item is malformed", async () => {
    answer(200, [receivedRequest, { id: "x" }]);

    expect(await getReceivedRequests()).toEqual({ kind: "unavailable" });
  });

  it("is unavailable on an error status, a non-list body or a network failure", async () => {
    answer(500);
    expect(await getReceivedRequests()).toEqual({ kind: "unavailable" });

    answer(200, { requests: [] });
    expect(await getReceivedRequests()).toEqual({ kind: "unavailable" });

    fetchMock.mockRejectedValueOnce(new Error("down"));
    expect(await getReceivedRequests()).toEqual({ kind: "unavailable" });
  });
});

describe("withdrawRequest", () => {
  it("withdraws and reports success", async () => {
    answer(200);

    expect(await withdrawRequest(ID)).toEqual({ ok: true });
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(new RegExp(`/applications/${ID}/withdraw$`));
    expect(init?.method).toBe("POST");
  });

  it.each([
    [404, "not-found"],
    [409, "not-active"],
    [500, "unavailable"],
  ])("maps the answer %i to %s", async (status, problem) => {
    answer(status);

    expect(await withdrawRequest(ID)).toMatchObject({ ok: false, problem });
  });

  it("does not call the backend for an invalid id", async () => {
    expect(await withdrawRequest("nope")).toMatchObject({
      problem: "not-found",
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("reports the service as unavailable when the network fails", async () => {
    fetchMock.mockRejectedValueOnce(new Error("down"));

    expect(await withdrawRequest(ID)).toMatchObject({
      problem: "unavailable",
    });
  });
});
