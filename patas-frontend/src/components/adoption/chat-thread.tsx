"use client";

import { useRouter } from "next/navigation";
import {
  useEffect,
  useRef,
  useState,
  useTransition,
  type FormEvent,
  type KeyboardEvent,
} from "react";

import {
  MESSAGE_MAX,
  SEND_MESSAGES,
  mergeMessages,
  messageProblem,
  type ChatMessage,
  type LoadMessagesAction,
  type SendAction,
} from "@/lib/conversation";
import { liveBus } from "@/lib/live-bus";

// Fixed locale and time zone: the server and the browser print the same text.
const WHEN = new Intl.DateTimeFormat("en-GB", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "UTC",
});

type Props = {
  applicationId: string;
  myId: string;
  initialMessages: ChatMessage[];
  canSend: boolean;
  send: SendAction;
  loadAfter: LoadMessagesAction;
};

// US-21: the conversation of an accepted request. New messages from the other side
// arrive live through the tab's bus; when the request ends, the page is refreshed and
// shows the conversation read-only.
export function ChatThread({
  applicationId,
  myId,
  initialMessages,
  canSend,
  send,
  loadAfter,
}: Props) {
  const router = useRouter();
  const [messages, setMessages] = useState(initialMessages);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  // The newest message the page has, read by the live listener without re-subscribing.
  const lastIdRef = useRef<string | null>(initialMessages.at(-1)?.id ?? null);
  useEffect(() => {
    lastIdRef.current = messages.at(-1)?.id ?? null;
  }, [messages]);

  useEffect(
    () =>
      liveBus.subscribe((event) => {
        if (
          event.name === "request.changed" &&
          event.data.application_id === applicationId
        ) {
          router.refresh();
          return;
        }
        if (
          event.name === "reconnected" ||
          (event.name === "message.posted" &&
            event.data.application_id === applicationId)
        ) {
          void loadAfter(applicationId, lastIdRef.current).then((result) => {
            if (result.kind === "ok") {
              setMessages((current) => mergeMessages(current, result.messages));
            }
          });
        }
      }),
    [applicationId, loadAfter, router],
  );

  // Keep the newest message in view, inside the list's own scroll.
  const listRef = useRef<HTMLOListElement>(null);
  useEffect(() => {
    const list = listRef.current;
    if (list) {
      list.scrollTop = list.scrollHeight;
    }
  }, [messages]);

  function submit(event?: FormEvent) {
    event?.preventDefault();
    if (pending) {
      return;
    }
    const problem = messageProblem(draft);
    if (problem) {
      setError(SEND_MESSAGES[problem]);
      return;
    }
    setError(null);
    startTransition(async () => {
      const outcome = await send(applicationId, draft);
      if (outcome.ok) {
        setMessages((current) => mergeMessages(current, [outcome.message]));
        setDraft("");
        return;
      }
      setError(outcome.message);
      if (outcome.problem === "closed") {
        // The request ended meanwhile: show the page as it is now.
        router.refresh();
      }
    });
  }

  // Enter sends; Shift+Enter starts a new line.
  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <section
      aria-label="Conversation"
      className="flex h-[32rem] min-w-0 flex-1 flex-col rounded-2xl bg-surface ring-1 ring-line"
    >
      <ol
        ref={listRef}
        aria-live="polite"
        className="flex flex-1 flex-col gap-3 overflow-y-auto p-4"
      >
        {messages.length === 0 ? (
          <li className="m-auto text-sm text-muted">
            No messages yet. Say hello!
          </li>
        ) : (
          messages.map((message) => {
            const mine = message.sender_id === myId;
            return (
              <li
                key={message.id}
                className={`flex max-w-[85%] flex-col gap-1 ${mine ? "items-end self-end" : "items-start self-start"}`}
              >
                <p
                  className={`whitespace-pre-wrap break-words rounded-2xl px-4 py-2 text-sm ${
                    mine
                      ? "rounded-br-sm bg-forest text-white"
                      : "rounded-bl-sm bg-background text-ink ring-1 ring-line"
                  }`}
                >
                  {message.body}
                </p>
                <span className="text-xs text-muted">
                  {mine ? "You" : message.sender_name} ·{" "}
                  <time dateTime={message.sent_at}>
                    {WHEN.format(new Date(message.sent_at))}
                  </time>
                </span>
              </li>
            );
          })
        )}
      </ol>

      {canSend ? (
        <form
          onSubmit={submit}
          className="grid gap-2 border-t border-line p-3"
        >
          <label htmlFor="chat-message" className="sr-only">
            Write a message
          </label>
          <div className="flex items-end gap-2">
            <textarea
              id="chat-message"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={onKeyDown}
              rows={2}
              maxLength={MESSAGE_MAX + 200}
              placeholder="Write a message…"
              className="min-h-11 flex-1 resize-none rounded-xl bg-background px-3 py-2 text-sm text-ink ring-1 ring-line focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
            />
            <button
              type="submit"
              disabled={pending}
              className="rounded-xl bg-forest px-4 py-2 text-sm font-semibold text-white transition hover:bg-forest/90 disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
            >
              {pending ? "Sending…" : "Send"}
            </button>
          </div>
          <div className="flex items-center justify-between gap-2 text-xs">
            <span role="alert" className="font-medium text-red-700">
              {error}
            </span>
            <span
              className={
                draft.trim().length > MESSAGE_MAX ? "text-red-700" : "text-muted"
              }
            >
              {draft.trim().length} / {MESSAGE_MAX}
            </span>
          </div>
        </form>
      ) : (
        <p className="border-t border-line p-4 text-sm text-muted">
          {SEND_MESSAGES.closed}
        </p>
      )}
    </section>
  );
}
