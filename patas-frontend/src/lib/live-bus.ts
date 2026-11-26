// US-21: hands the live events of this tab to whoever is listening (Observer). The
// connection in the layout emits; the chat, when its page is open, listens.
import type { LiveEvent } from "@/lib/live-events";

export type LiveListener = (event: LiveEvent) => void;

export type LiveBus = {
  subscribe(listener: LiveListener): () => void;
  emit(event: LiveEvent): void;
};

export function createLiveBus(): LiveBus {
  const listeners = new Set<LiveListener>();
  return {
    subscribe(listener) {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    emit(event) {
      for (const listener of listeners) {
        listener(event);
      }
    },
  };
}

// One bus for the tab.
export const liveBus = createLiveBus();
