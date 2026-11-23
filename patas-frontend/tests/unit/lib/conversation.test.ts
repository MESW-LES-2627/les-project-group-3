import { describe, expect, it } from "vitest";

import type { ReceivedRequest, SentRequest } from "@/lib/adoption";
import { findConversation } from "@/lib/conversation";

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
