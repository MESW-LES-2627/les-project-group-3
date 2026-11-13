import { describe, expect, it } from "vitest";
import {
  NOTE_MAX,
  canWithdraw,
  filterByStatus,
  isMyApplication,
  isSentRequest,
  noteProblem,
  noteProblemMessage,
  statusFilterOf,
  withdrawConfirmation,
  type SentRequest,
} from "@/lib/adoption";

function sent(status: string, id = "r1"): SentRequest {
  return {
    id,
    animal_id: "a1",
    animal_name: "Bolt",
    status,
    note: "I have a garden",
    owner_note: null,
    created_at: "2026-11-01T10:00:00Z",
  };
}

describe("noteProblem", () => {
  it("rejects an empty note and one with only spaces", () => {
    expect(noteProblem("")).toBe("blank");
    expect(noteProblem("   \n ")).toBe("blank");
  });

  it("accepts a note of exactly the maximum length", () => {
    expect(noteProblem("a".repeat(NOTE_MAX))).toBeNull();
  });

  it("rejects a note one character over the maximum", () => {
    expect(noteProblem("a".repeat(NOTE_MAX + 1))).toBe("too-long");
  });

  it("counts the length after trimming, as the backend does", () => {
    expect(noteProblem(`  ${"a".repeat(NOTE_MAX)}  `)).toBeNull();
  });
});

describe("noteProblemMessage", () => {
  it("tells the person what to do for each problem", () => {
    expect(noteProblemMessage("blank")).toBe(
      "Tell the owner a little about you and your home.",
    );
    expect(noteProblemMessage("too-long")).toContain(String(NOTE_MAX));
  });
});

describe("canWithdraw", () => {
  it.each(["open", "accepted"])("allows withdrawing a %s request", (status) => {
    expect(canWithdraw(status)).toBe(true);
  });

  it.each(["declined", "withdrawn", "closed", "adopted", "unknown"])(
    "does not allow withdrawing a %s request",
    (status) => {
      expect(canWithdraw(status)).toBe(false);
    },
  );
});

describe("withdrawConfirmation", () => {
  it("warns that an accepted request frees the animal for others", () => {
    expect(withdrawConfirmation("Bolt", "accepted")).toContain(
      "available to others again",
    );
  });

  it("asks a plain question for an open request", () => {
    expect(withdrawConfirmation("Bolt", "open")).toBe(
      "Withdraw your request for Bolt?",
    );
  });
});

describe("the ?status= filter of the requests page", () => {
  it("knows the statuses of a request", () => {
    expect(statusFilterOf("declined")).toBe("declined");
  });

  it("falls back to All for anything else", () => {
    expect(statusFilterOf(null)).toBeNull();
    expect(statusFilterOf("nonsense")).toBeNull();
    expect(statusFilterOf("")).toBeNull();
  });

  it("shows every request when there is no filter", () => {
    const requests = [sent("open", "r1"), sent("declined", "r2")];
    expect(filterByStatus(requests, null)).toEqual(requests);
  });

  it("keeps only the requests with the chosen status", () => {
    const requests = [
      sent("open", "r1"),
      sent("declined", "r2"),
      sent("open", "r3"),
    ];
    expect(filterByStatus(requests, "open").map((r) => r.id)).toEqual([
      "r1",
      "r3",
    ]);
  });
});

describe("response shape guards", () => {
  it("accepts a well-formed request I sent, with or without an owner note", () => {
    expect(isSentRequest(sent("open"))).toBe(true);
    expect(isSentRequest({ ...sent("declined"), owner_note: "Sorry" })).toBe(
      true,
    );
  });

  it("rejects a request with a missing or mistyped field", () => {
    const withoutOwnerNote: Record<string, unknown> = { ...sent("open") };
    delete withoutOwnerNote.owner_note;
    expect(isSentRequest(withoutOwnerNote)).toBe(false);
    expect(isSentRequest({ ...sent("open"), created_at: 5 })).toBe(false);
    expect(isSentRequest(null)).toBe(false);
    expect(isSentRequest("open")).toBe(false);
  });

  it("accepts a well-formed application and rejects a mistyped one", () => {
    const application = { id: "x", animal_id: "a", status: "open", note: "n" };
    expect(isMyApplication(application)).toBe(true);
    expect(isMyApplication({ ...application, note: undefined })).toBe(false);
    expect(isMyApplication(undefined)).toBe(false);
  });
});
