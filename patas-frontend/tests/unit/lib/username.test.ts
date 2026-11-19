import { describe, expect, it } from "vitest";

import {
  parseUsername,
  personLabel,
  USERNAME_RULE,
} from "@/lib/username";

describe("parseUsername", () => {
  it.each(["ana", "Ana_Demo", "ana.demo", "_a_", "a".repeat(30)])(
    "accepts %s as typed",
    (username) => {
      expect(parseUsername(username)).toEqual({ ok: true, username });
    },
  );

  it("trims surrounding whitespace", () => {
    expect(parseUsername("  ana  ")).toEqual({ ok: true, username: "ana" });
  });

  it.each([
    "",
    "an",
    "a".repeat(31),
    ".ana",
    "ana.",
    "ana demo",
    "ana-demo",
    "anã",
  ])("refuses %j with the rule", (username) => {
    expect(parseUsername(username)).toEqual({ ok: false, error: USERNAME_RULE });
  });

  it("refuses a value that is not text", () => {
    expect(parseUsername(null)).toEqual({ ok: false, error: USERNAME_RULE });
  });
});

describe("personLabel", () => {
  it("shows the username next to the name", () => {
    expect(personLabel("Ana Demo", "ana_demo")).toBe("Ana Demo (@ana_demo)");
  });
});
