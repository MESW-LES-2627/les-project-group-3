// US-21: the live notices each person receives on their own Ably channel, and when
// one becomes a toast. The backend publishes them (services/live.py); they carry ids
// and names only, never the text of a message.
import { personLabel } from "@/lib/username";

// The one channel a person listens to. The backend publishes to the same name, and
// the token route lets a person listen to nothing else.
export function liveChannel(userId: string): string {
  return `user:${userId}`;
}

export type MessagePostedData = {
  application_id: string;
  message_id: string;
  sender_id: string;
  sender_name: string;
  sender_username: string;
  animal_name: string;
};

export type RequestChangedData = {
  application_id: string;
  status: string;
};

export type LiveEvent =
  | { name: "message.posted"; data: MessagePostedData }
  | { name: "request.changed"; data: RequestChangedData }
  // Not from the backend: the connection came back, so the page should catch up on
  // whatever it missed while it was away.
  | { name: "reconnected" };

const MESSAGE_POSTED_FIELDS = [
  "application_id",
  "message_id",
  "sender_id",
  "sender_name",
  "sender_username",
  "animal_name",
] as const;

const REQUEST_CHANGED_FIELDS = ["application_id", "status"] as const;

function hasStrings<K extends string>(
  value: unknown,
  fields: readonly K[],
): value is Record<K, string> {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const record = value as Record<string, unknown>;
  return fields.every((field) => typeof record[field] === "string");
}

// What arrives from Ably is checked like a backend answer: unknown names and payloads
// with missing fields are dropped.
export function parseLiveEvent(name: string, data: unknown): LiveEvent | null {
  if (name === "message.posted" && hasStrings(data, MESSAGE_POSTED_FIELDS)) {
    return { name, data };
  }
  if (name === "request.changed" && hasStrings(data, REQUEST_CHANGED_FIELDS)) {
    return { name, data };
  }
  return null;
}

export type Toast = { text: string; href: string };

// A toast only for someone else's message, and not on that conversation's own page,
// where the chat shows the message instead.
export function toastFor(
  event: LiveEvent,
  pathname: string,
  myId: string,
): Toast | null {
  if (event.name !== "message.posted") {
    return null;
  }
  const { application_id, sender_id, sender_name, sender_username, animal_name } =
    event.data;
  const href = `/requests/${application_id}`;
  if (sender_id === myId || pathname === href) {
    return null;
  }
  return {
    text: `${personLabel(sender_name, sender_username)} sent a message about ${animal_name}`,
    href,
  };
}
