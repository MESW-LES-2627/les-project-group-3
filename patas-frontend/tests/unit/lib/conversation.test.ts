import { describe, expect, it } from "vitest";

import type { ReceivedRequest, SentRequest } from "@/lib/adoption";
import {
  MESSAGE_MAX,
  canSend,
  findConversation,
  hasConversation,
  isChatMessage,
  mergeMessages,
  messageProblem,
  type ChatMessage,
} from "@/lib/conversation";

function sent(id: string): SentRequest {
  return {
    id,
    animal_id: "a1",
    animal_name: "Rex",
    status: "accepted",
    note: "I have a garden",
    owner_note: null,
    owner_confirmed_at: null,
    applicant_confirmed_at: null,
    handover_checked: [],
    accepted_at: null,
    created_at: "2026-11-01T10:00:00Z",
  };
}

function received(id: string): ReceivedRequest {
  return {
    id,
    animal_id: "a2",
    animal_name: "Bolt",
    applicant_name: "Bruno",
    applicant_username: "bruno",
    status: "accepted",
    note: "I have a garden",
    owner_note: null,
    applicant_profile: {
      housing: "apartment",
      time_away: "half_day",
      activity: "moderate",
      experience: "some",
      has_children: false,
      has_dogs: true,
      has_cats: false,
    },
    compatibility_concerns: [],
    owner_confirmed_at: null,
    applicant_confirmed_at: null,
    handover_checked: [],
    accepted_at: null,
    created_at: "2026-11-01T10:00:00Z",
  };
}

describe("findConversation", () => {
  it("finds a request I sent and marks me as the applicant", () => {
    const mine = sent("r1");
    expect(findConversation("r1", [mine], [received("r2")])).toEqual({
      role: "applicant",
      request: mine,
    });
  });

  it("finds a request I received and marks me as the owner", () => {
    const theirs = received("r2");
    expect(findConversation("r2", [sent("r1")], [theirs])).toEqual({
      role: "owner",
      request: theirs,
    });
  });

  it("finds nothing for someone else's request", () => {
    expect(findConversation("r9", [sent("r1")], [received("r2")])).toBeNull();
  });
});

function message(id: string, sent_at: string, body = "Hi"): ChatMessage {
  return {
    id,
    application_id: "r1",
    sender_id: "u1",
    sender_name: "Bruno",
    sender_username: "bruno",
    body,
    sent_at,
  };
}

describe("messageProblem", () => {
  it("refuses an empty message and one with only spaces", () => {
    expect(messageProblem("")).toBe("blank");
    expect(messageProblem("  \n\t ")).toBe("blank");
  });

  it("accepts exactly 2000 characters and refuses 2001", () => {
    expect(MESSAGE_MAX).toBe(2000);
    expect(messageProblem("a".repeat(2000))).toBeNull();
    expect(messageProblem("a".repeat(2001))).toBe("too-long");
  });

  it("counts the message without the spaces around it, like the backend", () => {
    expect(messageProblem(`  ${"a".repeat(2000)}  `)).toBeNull();
  });
});

describe("mergeMessages", () => {
  it("keeps one copy of a message that arrives twice (the sender's own echo)", () => {
    const mine = message("m1", "2026-11-26T10:00:00Z");

    expect(mergeMessages([mine], [mine])).toEqual([mine]);
  });

  it("puts messages that arrive out of order back in the order they were sent", () => {
    const first = message("m1", "2026-11-26T10:00:00Z");
    const second = message("m2", "2026-11-26T10:01:00Z");
    const third = message("m3", "2026-11-26T10:02:00Z");

    expect(mergeMessages([third], [second, first])).toEqual([first, second, third]);
  });

  it("orders two messages sent at the same instant by id, like the backend", () => {
    const b = message("b", "2026-11-26T10:00:00Z");
    const a = message("a", "2026-11-26T10:00:00Z");

    expect(mergeMessages([b], [a]).map((m) => m.id)).toEqual(["a", "b"]);
  });

  it("does not change the list it was given", () => {
    const current = [message("m2", "2026-11-26T10:01:00Z")];

    mergeMessages(current, [message("m1", "2026-11-26T10:00:00Z")]);

    expect(current.map((m) => m.id)).toEqual(["m2"]);
  });
});

describe("isChatMessage", () => {
  it("accepts a message as the backend sends it", () => {
    expect(isChatMessage(message("m1", "2026-11-26T10:00:00Z"))).toBe(true);
  });

  it("refuses one with a missing or mistyped field", () => {
    const without: Record<string, unknown> = {
      ...message("m1", "2026-11-26T10:00:00Z"),
    };
    delete without.body;
    expect(isChatMessage(without)).toBe(false);
    expect(
      isChatMessage({ ...message("m1", "2026-11-26T10:00:00Z"), sent_at: 1 }),
    ).toBe(false);
    expect(isChatMessage(null)).toBe(false);
  });
});

describe("hasConversation and canSend", () => {
  it("a request accepted at some point has a conversation, even after it ended", () => {
    expect(hasConversation({ accepted_at: "2026-11-02T10:00:00Z" })).toBe(true);
    expect(hasConversation({ accepted_at: null })).toBe(false);
  });

  it("only an accepted request can be written to", () => {
    expect(canSend("accepted")).toBe(true);
    for (const status of ["open", "declined", "withdrawn", "closed", "adopted"]) {
      expect(canSend(status)).toBe(false);
    }
  });
});
