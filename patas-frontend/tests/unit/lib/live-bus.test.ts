import { describe, expect, it } from "vitest";

import { createLiveBus } from "@/lib/live-bus";
import type { LiveEvent } from "@/lib/live-events";

const reconnected: LiveEvent = { name: "reconnected" };

describe("createLiveBus", () => {
  it("gives every event to everyone listening", () => {
    const bus = createLiveBus();
    const first: LiveEvent[] = [];
    const second: LiveEvent[] = [];
    bus.subscribe((event) => first.push(event));
    bus.subscribe((event) => second.push(event));

    bus.emit(reconnected);

    expect(first).toEqual([reconnected]);
    expect(second).toEqual([reconnected]);
  });

  it("stops giving events to a listener that left (a closed chat)", () => {
    const bus = createLiveBus();
    const received: LiveEvent[] = [];
    const leave = bus.subscribe((event) => received.push(event));

    leave();
    bus.emit(reconnected);

    expect(received).toEqual([]);
  });

  it("keeps separate buses apart", () => {
    const one = createLiveBus();
    const other = createLiveBus();
    const received: LiveEvent[] = [];
    other.subscribe((event) => received.push(event));

    one.emit(reconnected);

    expect(received).toEqual([]);
  });
});
