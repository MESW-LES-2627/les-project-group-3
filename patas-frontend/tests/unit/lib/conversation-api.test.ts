import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Only the sign-in boundary and the network are replaced: how each backend answer
// becomes something the conversation can show is the code under test.
vi.mock("@/lib/matchmaker-api", () => ({
  bearerToken: vi.fn(async () => "test-token"),
}));

import { getMessages, postMessage } from "@/lib/conversation-api";

const ID = "3f2b8c1e-4d5a-4b6c-8d7e-9f0a1b2c3d4e";
const AFTER = "9a8b7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d";
const fetchMock = vi.fn<typeof fetch>();

const message = {
  id: AFTER,
  application_id: ID,
  sender_id: "11111111-1111-1111-1111-111111111111",
  sender_name: "Bruno",
  sender_username: "bruno",
  body: "Can I visit Rex?",
  sent_at: "2026-11-26T10:00:00Z",
};

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

describe("getMessages", () => {
  it("reads the conversation with the signed-in person's token", async () => {
    answer(200, [message]);

    const result = await getMessages(ID);

    expect(result).toEqual({ kind: "ok", messages: [message] });
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(new RegExp(`/applications/${ID}/messages$`));
    expect(new Headers(init?.headers).get("Authorization")).toBe(
      "Bearer test-token",
    );
  });

  it("asks only for the messages after the last one it has", async () => {
    answer(200, []);

    await getMessages(ID, AFTER);

    expect(String(fetchMock.mock.calls[0][0])).toMatch(
      new RegExp(`/applications/${ID}/messages\\?after=${AFTER}$`),
    );
  });

  it("ignores an after that is not a message id", async () => {
    answer(200, []);

    await getMessages(ID, "../../oops");

    expect(String(fetchMock.mock.calls[0][0])).toMatch(/\/messages$/);
  });

  it("says there is no conversation when the backend answers 404", async () => {
    answer(404);

    expect(await getMessages(ID)).toEqual({ kind: "not-found" });
  });

  it("does not call the backend for something that is not a request id", async () => {
    expect(await getMessages("not-a-uuid")).toEqual({ kind: "not-found" });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("is unavailable when the backend fails or answers something unexpected", async () => {
    fetchMock.mockRejectedValueOnce(new Error("down"));
    expect(await getMessages(ID)).toEqual({ kind: "unavailable" });

    answer(500);
    expect(await getMessages(ID)).toEqual({ kind: "unavailable" });

    answer(200, [{ ...message, body: 3 }]);
    expect(await getMessages(ID)).toEqual({ kind: "unavailable" });
  });
});

describe("postMessage", () => {
  it("posts the text and returns the saved message", async () => {
    answer(201, message);

    const outcome = await postMessage(ID, "Can I visit Rex?");

    expect(outcome).toEqual({ ok: true, message });
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(new RegExp(`/applications/${ID}/messages$`));
    expect(init?.method).toBe("POST");
    expect(init?.body).toBe(JSON.stringify({ body: "Can I visit Rex?" }));
    expect(new Headers(init?.headers).get("Authorization")).toBe(
      "Bearer test-token",
    );
  });

  it("explains each refusal from the backend", async () => {
    answer(404);
    expect(await postMessage(ID, "Hi")).toMatchObject({
      ok: false,
      problem: "not-found",
    });

    answer(409, { detail: { code: "conversation_closed" } });
    expect(await postMessage(ID, "Hi")).toMatchObject({
      ok: false,
      problem: "closed",
      message: "This request has ended. Messages can no longer be sent.",
    });

    answer(422);
    expect(await postMessage(ID, "   ")).toMatchObject({
      ok: false,
      problem: "blank",
    });

    answer(422);
    expect(await postMessage(ID, "a".repeat(2001))).toMatchObject({
      ok: false,
      problem: "too-long",
    });
  });

  it("is unavailable when the backend cannot be reached or fails", async () => {
    fetchMock.mockRejectedValueOnce(new Error("down"));
    expect(await postMessage(ID, "Hi")).toMatchObject({ problem: "unavailable" });

    answer(500);
    expect(await postMessage(ID, "Hi")).toMatchObject({ problem: "unavailable" });

    answer(201, { unexpected: true });
    expect(await postMessage(ID, "Hi")).toMatchObject({ problem: "unavailable" });
  });

  it("does not call the backend for something that is not a request id", async () => {
    expect(await postMessage("not-a-uuid", "Hi")).toMatchObject({
      problem: "not-found",
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
