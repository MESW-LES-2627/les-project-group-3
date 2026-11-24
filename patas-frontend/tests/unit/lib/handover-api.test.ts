import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Only the sign-in boundary and the network are replaced: how each backend answer
// becomes a message for the person is the code under test.
vi.mock("@/lib/matchmaker-api", () => ({
  bearerToken: vi.fn(async () => "test-token"),
}));

import { setHandoverItem } from "@/lib/adoption-api";

const ID = "3f2b8c1e-4d5a-4b6c-8d7e-9f0a1b2c3d4e";
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

describe("setHandoverItem", () => {
  it("puts the tick with the signed-in person's token and returns what is ticked", async () => {
    answer(200, { checked: ["care_notes"] });

    const outcome = await setHandoverItem(ID, "care_notes", true);

    expect(outcome).toEqual({ ok: true, checked: ["care_notes"] });
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(
      new RegExp(`/applications/${ID}/handover/care_notes$`),
    );
    expect(init?.method).toBe("PUT");
    expect(init?.body).toBe(JSON.stringify({ checked: true }));
    expect(new Headers(init?.headers).get("Authorization")).toBe(
      "Bearer test-token",
    );
  });

  it("sends an untick as checked false", async () => {
    answer(200, { checked: [] });

    await setHandoverItem(ID, "care_notes", false);

    expect(fetchMock.mock.calls[0][1]?.body).toBe(
      JSON.stringify({ checked: false }),
    );
  });

  it("does not call the backend for something that is not a request id", async () => {
    const outcome = await setHandoverItem("not-a-uuid", "care_notes", true);

    expect(outcome).toMatchObject({ ok: false, problem: "not-found" });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it.each([
    [404, "not-found"],
    [409, "not-tickable"],
    [422, "unavailable"],
    [500, "unavailable"],
  ])("maps the answer %i to %s", async (status, problem) => {
    answer(status);

    expect(await setHandoverItem(ID, "care_notes", true)).toMatchObject({
      ok: false,
      problem,
    });
  });

  it("is unavailable when the backend cannot be reached", async () => {
    fetchMock.mockRejectedValueOnce(new Error("down"));

    expect(await setHandoverItem(ID, "care_notes", true)).toMatchObject({
      ok: false,
      problem: "unavailable",
    });
  });

  it("does not trust a 200 whose body is not a list of ticked items", async () => {
    answer(200, { checked: "care_notes" });

    expect(await setHandoverItem(ID, "care_notes", true)).toMatchObject({
      ok: false,
      problem: "unavailable",
    });
  });
});
