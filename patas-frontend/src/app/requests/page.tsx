import type { Metadata } from "next";
import { headers } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Suspense } from "react";

import { ReceivedRequestList } from "@/components/adoption/received-request-list";
import { SentRequestList } from "@/components/adoption/sent-request-list";
import { getMyRequests, getReceivedRequests } from "@/lib/adoption-api";
import { auth } from "@/lib/auth";

import { withdrawRequestAction } from "./actions";

export const metadata: Metadata = {
  title: "Requests | Patas",
};

type Props = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

async function RequestsContent({ searchParams }: Props) {
  const params = await searchParams;
  const received = params.view === "received";

  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) {
    redirect("/login");
  }

  if (received) {
    const mine = await getReceivedRequests();
    if (mine.kind === "unavailable") {
      return (
        <>
          <RequestTabs received />
          <p className="mt-5 text-sm text-muted">
            Your requests are not available right now, please try again later.
          </p>
        </>
      );
    }

    return (
      <>
        <RequestTabs received />
        <section aria-labelledby="received-heading" className="mt-6">
          <h2 id="received-heading" className="sr-only">
            Received
          </h2>
          <ReceivedRequestList requests={mine.requests} />
        </section>
      </>
    );
  }

  const mine = await getMyRequests();
  if (mine.kind === "unavailable") {
    return (
      <>
        <RequestTabs received={false} />
        <p className="mt-5 text-sm text-muted">
          Your requests are not available right now, please try again later.
        </p>
      </>
    );
  }

  return (
    <>
      <RequestTabs received={false} />
      <section aria-labelledby="sent-heading" className="mt-6">
        <h2 id="sent-heading" className="sr-only">
          Sent
        </h2>
        <SentRequestList
          requests={mine.requests}
          withdraw={withdrawRequestAction}
        />
      </section>
    </>
  );
}

function RequestTabs({ received }: { received: boolean }) {
  const linkClass =
    "inline-flex min-h-11 items-center border-b-2 px-4 text-sm font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest";

  return (
    <nav aria-label="Request type" className="flex border-b border-line">
      <Link
        href="/requests"
        aria-current={received ? undefined : "page"}
        className={`${linkClass} ${
          received
            ? "border-transparent text-muted hover:text-forest"
            : "border-forest text-forest"
        }`}
      >
        Sent
      </Link>
      <Link
        href="/requests?view=received"
        aria-current={received ? "page" : undefined}
        className={`${linkClass} ${
          received
            ? "border-forest text-forest"
            : "border-transparent text-muted hover:text-forest"
        }`}
      >
        Received
      </Link>
    </nav>
  );
}

// Each list is request-time data and is rendered on the server inside Suspense.
export default function RequestsPage({ searchParams }: Props) {
  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-8 px-4 py-10 sm:px-6 sm:py-14">
      <div className="border-b border-line pb-8">
        <h1 className="text-4xl font-semibold text-forest sm:text-5xl">
          Requests
        </h1>
        <p className="mt-3 max-w-xl text-base leading-7 text-muted">
          Follow the requests you sent and see who wants to adopt your animals.
        </p>
      </div>

      <Suspense
        fallback={<p className="text-sm text-muted">Loading your requests…</p>}
      >
        <RequestsContent searchParams={searchParams} />
      </Suspense>
    </main>
  );
}
