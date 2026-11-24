import { describe, expect, it } from "vitest";

import { APPLICATION_STATUS } from "@/lib/adoption-status";
import {
  HANDOVER_CHECKLIST,
  HANDOVER_ITEM_KEYS,
  canTick,
  checkedCount,
  showsChecklist,
} from "@/lib/handover-checklist";

describe("AT-26: the handover checklist next to an accepted request", () => {
  it("shows while the request is accepted and after the adoption, not otherwise", () => {
    for (const status of APPLICATION_STATUS) {
      expect(showsChecklist(status)).toBe(
        status === "accepted" || status === "adopted",
      );
    }
  });

  it("can be changed only while the request is accepted", () => {
    for (const status of APPLICATION_STATUS) {
      expect(canTick(status)).toBe(status === "accepted");
    }
  });
});

describe("the checklist items", () => {
  it("are the four the backend knows, in this order", () => {
    expect(HANDOVER_ITEM_KEYS).toEqual([
      "vaccination_booklet",
      "microchip_transfer",
      "care_notes",
      "adoption_terms",
    ]);
    expect(HANDOVER_CHECKLIST.map((item) => item.key)).toEqual([
      ...HANDOVER_ITEM_KEYS,
    ]);
  });

  it("each say how to do it", () => {
    for (const item of HANDOVER_CHECKLIST) {
      expect(item.title).not.toBe("");
      expect(item.steps.length).toBeGreaterThan(0);
    }
  });

  it("quote a legal rule only where one exists", () => {
    for (const item of HANDOVER_CHECKLIST) {
      expect(item.rule !== null).toBe(item.basis === "law");
    }
  });

  it("tell the two sides to do the SIAC transfer outside the chat", () => {
    const transfer = HANDOVER_CHECKLIST.find(
      (item) => item.key === "microchip_transfer",
    );
    expect(transfer?.rule).toContain("15 days");
    expect(transfer?.steps.join(" ")).toContain("not in the chat");
  });
});

describe("checkedCount", () => {
  it("counts the ticked items", () => {
    expect(checkedCount([])).toBe(0);
    expect(checkedCount(["care_notes", "adoption_terms"])).toBe(2);
  });

  it("ignores a key the page does not know", () => {
    expect(checkedCount(["care_notes", "something_new"])).toBe(1);
  });
});
