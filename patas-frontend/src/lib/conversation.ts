import type { ReceivedRequest, SentRequest } from "@/lib/adoption";

// The request a conversation page is about, seen from the caller's side. The page
// finds it in the two lists, which carry everything it needs (ADR 0029).
export type ConversationRequest =
  | { role: "applicant"; request: SentRequest }
  | { role: "owner"; request: ReceivedRequest };

export function findConversation(
  id: string,
  sent: readonly SentRequest[],
  received: readonly ReceivedRequest[],
): ConversationRequest | null {
  const mine = sent.find((request) => request.id === id);
  if (mine) {
    return { role: "applicant", request: mine };
  }
  const theirs = received.find((request) => request.id === id);
  if (theirs) {
    return { role: "owner", request: theirs };
  }
  return null;
}

// US-21: the messages of a conversation.

export const MESSAGE_MAX = 2000;

export type ChatMessage = {
  id: string;
  application_id: string;
  sender_id: string;
  sender_name: string;
  sender_username: string;
  body: string;
  sent_at: string;
};

const MESSAGE_FIELDS = [
  "id",
  "application_id",
  "sender_id",
  "sender_name",
  "sender_username",
  "body",
  "sent_at",
] as const;

export function isChatMessage(value: unknown): value is ChatMessage {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const message = value as Record<string, unknown>;
  return MESSAGE_FIELDS.every((field) => typeof message[field] === "string");
}

// The same rules as the backend, so the person sees the problem before sending.
export function messageProblem(body: string): "blank" | "too-long" | null {
  const trimmed = body.trim();
  if (trimmed.length === 0) {
    return "blank";
  }
  return trimmed.length > MESSAGE_MAX ? "too-long" : null;
}

// Messages arrive from three places (the page load, the answer to a send, the live
// fetch), sometimes twice: keep one of each, oldest first, in the backend's order.
export function mergeMessages(
  current: readonly ChatMessage[],
  incoming: readonly ChatMessage[],
): ChatMessage[] {
  const byId = new Map(current.map((message) => [message.id, message]));
  for (const message of incoming) {
    byId.set(message.id, message);
  }
  return [...byId.values()].sort((a, b) => {
    const byTime = Date.parse(a.sent_at) - Date.parse(b.sent_at);
    if (byTime !== 0) {
      return byTime;
    }
    return a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
  });
}

// The chat's messages and how far it has fetched from Patas. The cursor moves only
// with what a fetch returned (complete up to its last message), never with the
// answer to my own send: the other side's message saved just before mine would
// otherwise be skipped by the next "after".
export type ChatState = { messages: ChatMessage[]; cursor: string | null };

export function withFetched(
  state: ChatState,
  fetched: readonly ChatMessage[],
): ChatState {
  return {
    messages: mergeMessages(state.messages, fetched),
    cursor: fetched.at(-1)?.id ?? state.cursor,
  };
}

export function withSent(state: ChatState, sent: ChatMessage): ChatState {
  return { messages: mergeMessages(state.messages, [sent]), cursor: state.cursor };
}

// A request accepted at some point has a conversation, even after it ends.
export function hasConversation(request: {
  accepted_at: string | null;
}): boolean {
  return request.accepted_at !== null;
}

// Only while accepted: after that the conversation is read-only.
export function canSend(status: string): boolean {
  return status === "accepted";
}

export type SendProblem =
  | "blank"
  | "too-long"
  | "not-found"
  | "closed"
  | "unavailable";

export const SEND_MESSAGES: Record<SendProblem, string> = {
  blank: "Write something first.",
  "too-long": `A message can have at most ${MESSAGE_MAX} characters.`,
  "not-found": "This conversation could not be found.",
  closed: "This request has ended. Messages can no longer be sent.",
  unavailable: "We could not send that right now. Please try again.",
};

export type SendOutcome =
  | { ok: true; message: ChatMessage }
  | { ok: false; problem: SendProblem; message: string };

export type SendAction = (
  applicationId: string,
  body: string,
) => Promise<SendOutcome>;

export type MessagesResult =
  | { kind: "ok"; messages: ChatMessage[] }
  | { kind: "not-found" }
  | { kind: "unavailable" };

export type LoadMessagesAction = (
  applicationId: string,
  after: string | null,
) => Promise<MessagesResult>;
