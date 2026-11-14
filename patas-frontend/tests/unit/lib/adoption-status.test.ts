import { describe, expect, it } from "vitest";
import {
  animalStatusLabel,
  applicationStatusLabel,
  isApplicationStatus,
} from "@/lib/adoption-status";

describe("animalStatusLabel", () => {
  it("uses the owner's wording for an unavailable animal", () => {
    expect(animalStatusLabel("unavailable")).toBe("Unpublished");
    expect(animalStatusLabel("available")).toBe("Available");
  });

  it("shows a status it does not know as readable text, not a blank badge", () => {
    expect(animalStatusLabel("pending_review")).toBe("Pending review");
  });

  it("does not match names the object inherits", () => {
    expect(animalStatusLabel("constructor")).toBe("Constructor");
    expect(animalStatusLabel("toString")).toBe("ToString");
  });
});

describe("applicationStatusLabel", () => {
  it("labels every status the backend can send", () => {
    expect(applicationStatusLabel("open")).toBe("Open");
    expect(applicationStatusLabel("withdrawn")).toBe("Withdrawn");
  });

  it("falls back to readable text for a newer backend status", () => {
    expect(applicationStatusLabel("on_hold")).toBe("On hold");
  });
});

describe("isApplicationStatus", () => {
  it("accepts a known status and rejects everything else", () => {
    expect(isApplicationStatus("accepted")).toBe(true);
    expect(isApplicationStatus("Accepted")).toBe(false);
    expect(isApplicationStatus("constructor")).toBe(false);
    expect(isApplicationStatus(undefined)).toBe(false);
    expect(isApplicationStatus(3)).toBe(false);
  });
});
