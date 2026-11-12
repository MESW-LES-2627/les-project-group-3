import type { Metadata } from "next";
import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { Suspense } from "react";

import { SentRequestList } from "@/components/adoption/sent-request-list";
import { getMyRequests } from "@/lib/adoption-api";
import { auth } from "@/lib/auth";

import { withdrawRequestAction } from "./actions";

export const metadata: Metadata = {
  title: "Requests | Patas",
};

// The session and the list are request-time data, so they stay inside the Suspense
// boundary below and the heading is prerendered, like /animals/mine.
async function SentRequests() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) {
    redirect("/login");
  }

  const mine = await getMyRequests();
  if (mine.kind === "unavailable") {
    return (
      <p className="text-sm text-muted">
        Your requests are not available right now, please try again later.
      </p>
    );
  }
  return (
    <SentRequestList requests={mine.requests} withdraw={withdrawRequestAction} />
  );
}

// The requests the signed-in person sent (US-17). The list is loaded on the server
// and filtered in the browser (ADR 0020).
export default function RequestsPage() {
  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-8 px-4 py-10 sm:px-6 sm:py-14">
      <div className="border-b border-line pb-8">
        <h1 className="text-4xl font-semibold text-forest sm:text-5xl">
          Requests
        </h1>
        <p className="mt-3 max-w-xl text-base leading-7 text-muted">
          Follow the requests to adopt you sent, and see the owners&apos;
          replies.
        </p>
      </div>

      <section aria-labelledby="sent-heading">
        <h2 id="sent-heading" className="mb-5 text-xl font-semibold text-forest">
          Sent
        </h2>
        <Suspense
          fallback={<p className="text-sm text-muted">Loading your requests…</p>}
        >
          <SentRequests />
        </Suspense>
      </section>
    </main>
  );
}
