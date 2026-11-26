import type { Metadata } from "next";
import { headers } from "next/headers";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { Suspense } from "react";

import {
  loadMessagesAction,
  sendMessageAction,
  setHandoverItemAction,
} from "@/app/requests/actions";
import { AdoptionGuidelines } from "@/components/adoption/adoption-guidelines";
import { ChatThread } from "@/components/adoption/chat-thread";
import { HandoverChecklist } from "@/components/adoption/handover-checklist";
import { SidePanel } from "@/components/adoption/side-panel";
import { getMyRequests, getReceivedRequests } from "@/lib/adoption-api";
import { showsGuidelines } from "@/lib/adoption-guidelines";
import { canTick, showsChecklist } from "@/lib/handover-checklist";
import { applicationStatusLabel } from "@/lib/adoption-status";
import { auth } from "@/lib/auth";
import {
  canSend,
  findConversation,
  hasConversation,
} from "@/lib/conversation";
import { getMessages } from "@/lib/conversation-api";
import { personLabel } from "@/lib/username";

export const metadata: Metadata = {
  title: "Conversation | Patas",
};

type Props = {
  params: Promise<{ id: string }>;
};

// The page of one request: a compact header with the guidelines (US-24, ADR 0027),
// then the conversation (US-21, ADR 0029) beside the handover checklist (US-25).
async function ConversationContent({ params }: Props) {
  const { id } = await params;
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) {
    redirect("/login");
  }

  const [sent, received] = await Promise.all([
    getMyRequests(),
    getReceivedRequests(),
  ]);
  if (sent.kind === "unavailable" || received.kind === "unavailable") {
    return (
      <p className="text-sm text-muted">
        This conversation is not available right now, please try again later.
      </p>
    );
  }

  // Someone else's request looks like one that does not exist (ADR 0020, decision 5).
  const conversation = findConversation(id, sent.requests, received.requests);
  if (!conversation) {
    notFound();
  }

  const { request } = conversation;
  const who =
    conversation.role === "owner"
      ? `Request from ${personLabel(
          conversation.request.applicant_name,
          conversation.request.applicant_username,
        )}`
      : "Your request";

  // A request accepted at some point has a conversation, even after it ended.
  const messages = hasConversation(request)
    ? await getMessages(request.id)
    : null;
  const checklist = showsChecklist(request.status) ? (
    <HandoverChecklist
      applicationId={request.id}
      checked={request.handover_checked}
      editable={canTick(request.status)}
      action={setHandoverItemAction}
      collapsible={false}
    />
  ) : null;

  return (
    <>
      <div className="grid gap-3 border-b border-line pb-5">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <h1 className="text-2xl font-semibold text-forest sm:text-3xl">
            {request.animal_name}
          </h1>
          <span className="rounded-full bg-surface px-2.5 py-0.5 text-xs font-semibold text-forest ring-1 ring-line">
            {applicationStatusLabel(request.status)}
          </span>
          <p className="text-sm text-muted sm:ml-auto">{who}</p>
        </div>
        {showsGuidelines(request.status) ? <AdoptionGuidelines /> : null}
      </div>

      {messages === null ? null : messages.kind === "ok" ? (
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:gap-0">
          <ChatThread
            applicationId={request.id}
            myId={session.user.id}
            initialMessages={messages.messages}
            canSend={canSend(request.status)}
            send={sendMessageAction}
            loadAfter={loadMessagesAction}
          />
          {checklist ? (
            <SidePanel title="Handover checklist">{checklist}</SidePanel>
          ) : null}
        </div>
      ) : (
        <p className="text-sm text-muted">
          The conversation is not available right now, please try again later.
        </p>
      )}
    </>
  );
}

export default function ConversationPage({ params }: Props) {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-4 py-10 sm:px-6 sm:py-14">
      <Link
        href="/requests"
        className="self-start text-sm font-semibold text-leaf underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
      >
        ← Requests
      </Link>

      <Suspense
        fallback={<p className="text-sm text-muted">Loading the conversation…</p>}
      >
        <ConversationContent params={params} />
      </Suspense>
    </main>
  );
}
