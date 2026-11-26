import { describe, expect, it } from "vitest";

import {
  liveChannel,
  parseLiveEvent,
  toastFor,
  type LiveEvent,
} from "@/lib/live-events";

const ANA = "11111111-1111-1111-1111-111111111111";
const BRUNO = "22222222-2222-2222-2222-222222222222";
const REQUEST = "3f2b8c1e-4d5a-4b6c-8d7e-9f0a1b2c3d4e";

const posted = {
  application_id: REQUEST,
  message_id: "9a8b7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d",
  sender_id: BRUNO,
  sender_name: "Bruno",
  sender_username: "bruno",
  animal_name: "Rex",
};

function messageFromBruno(): LiveEvent {
  const event = parseLiveEvent("message.posted", posted);
  if (event === null) {
    throw new Error("a valid notice was refused");
  }
  return event;
}

describe("liveChannel", () => {
  it("is the same name the backend publishes to", () => {
    expect(liveChannel(ANA)).toBe(`user:${ANA}`);
  });
});

describe("parseLiveEvent", () => {
  it("reads a new message notice", () => {
    expect(parseLiveEvent("message.posted", posted)).toEqual({
      name: "message.posted",
      data: posted,
    });
  });

  it("reads a request that changed", () => {
    const data = { application_id: REQUEST, status: "declined" };

    expect(parseLiveEvent("request.changed", data)).toEqual({
      name: "request.changed",
      data,
    });
  });

  it("drops an event it does not know", () => {
    expect(parseLiveEvent("something.else", posted)).toBeNull();
  });

  it("drops a notice with a missing or mistyped field", () => {
    const withoutAnimal: Record<string, unknown> = { ...posted };
    delete withoutAnimal.animal_name;
    expect(parseLiveEvent("message.posted", withoutAnimal)).toBeNull();
    expect(parseLiveEvent("message.posted", { ...posted, sender_id: 7 })).toBeNull();
    expect(parseLiveEvent("request.changed", { application_id: REQUEST })).toBeNull();
    expect(parseLiveEvent("message.posted", null)).toBeNull();
    expect(parseLiveEvent("message.posted", "text")).toBeNull();
  });
});

describe("toastFor", () => {
  it("tells Ana about Bruno's message while she is elsewhere, with a link", () => {
    expect(toastFor(messageFromBruno(), "/animals", ANA)).toEqual({
      text: "Bruno (@bruno) sent a message about Rex",
      href: `/requests/${REQUEST}`,
    });
  });

  it("shows nothing on that conversation's page, where the chat shows it", () => {
    expect(toastFor(messageFromBruno(), `/requests/${REQUEST}`, ANA)).toBeNull();
  });

  it("still shows one on another conversation's page", () => {
    expect(toastFor(messageFromBruno(), "/requests/another-id", ANA)).not.toBeNull();
  });

  it("never toasts my own message, which my other tabs also receive", () => {
    expect(toastFor(messageFromBruno(), "/animals", BRUNO)).toBeNull();
  });

  it("shows nothing for a request that changed or a reconnection", () => {
    const changed = parseLiveEvent("request.changed", {
      application_id: REQUEST,
      status: "declined",
    });
    expect(changed).not.toBeNull();
    expect(toastFor(changed as LiveEvent, "/animals", ANA)).toBeNull();
    expect(toastFor({ name: "reconnected" }, "/animals", ANA)).toBeNull();
  });
});
