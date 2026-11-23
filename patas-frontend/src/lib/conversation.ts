import type { ReceivedRequest, SentRequest } from "@/lib/adoption";

// The request a conversation page is about, seen from the caller's side.
// Until US-21 adds GET /applications/{id}, the page finds it in the two lists.
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
