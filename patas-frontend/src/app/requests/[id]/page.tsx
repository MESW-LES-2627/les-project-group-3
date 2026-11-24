import type { Metadata } from "next";
import { headers } from "next/headers";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { Suspense } from "react";

import { setHandoverItemAction } from "@/app/requests/actions";
import { AdoptionGuidelines } from "@/components/adoption/adoption-guidelines";
import { HandoverChecklist } from "@/components/adoption/handover-checklist";
import { getMyRequests, getReceivedRequests } from "@/lib/adoption-api";
import { showsGuidelines } from "@/lib/adoption-guidelines";
import { canTick, showsChecklist } from "@/lib/handover-checklist";
import { applicationStatusLabel } from "@/lib/adoption-status";
import { auth } from "@/lib/auth";
import { findConversation } from "@/lib/conversation";
import { personLabel } from "@/lib/username";

export const metadata: Metadata = {
  title: "Conversation | Patas",
};

type Props = {
  params: Promise<{ id: string }>;
};

// The page of one request, where its conversation will live (US-21). For now it
// holds the guidelines (US-24, ADR 0027).
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

  return (
    <>
      <div className="border-b border-line pb-8">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h1 className="text-4xl font-semibold text-forest sm:text-5xl">
            {request.animal_name}
          </h1>
          <span className="rounded-full bg-surface px-2.5 py-0.5 text-xs font-semibold text-forest ring-1 ring-line">
            {applicationStatusLabel(request.status)}
          </span>
        </div>
        <p className="mt-3 text-base leading-7 text-muted">{who}</p>
      </div>

      {showsGuidelines(request.status) ? <AdoptionGuidelines open /> : null}

      {showsChecklist(request.status) ? (
        <HandoverChecklist
          applicationId={request.id}
          checked={request.handover_checked}
          editable={canTick(request.status)}
          action={setHandoverItemAction}
        />
      ) : null}
    </>
  );
}

export default function ConversationPage({ params }: Props) {
  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-8 px-4 py-10 sm:px-6 sm:py-14">
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
