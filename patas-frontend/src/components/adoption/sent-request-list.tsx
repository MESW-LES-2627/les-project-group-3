"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

import {
  canWithdraw,
  filterByStatus,
  statusFilterOf,
  type SentRequest,
  type WithdrawAction,
} from "@/lib/adoption";
import {
  APPLICATION_STATUS,
  applicationStatusLabel,
  type ApplicationStatus,
} from "@/lib/adoption-status";

import { WithdrawButton } from "./withdraw-button";

const FILTERS: (ApplicationStatus | null)[] = [null, ...APPLICATION_STATUS];
// Fixed locale and time zone: the server and the browser print the same text.
const DATE = new Intl.DateTimeFormat("en-GB", {
  dateStyle: "medium",
  timeZone: "UTC",
});

type SentRequestListProps = {
  requests: SentRequest[];
  withdraw: WithdrawAction;
};

export function SentRequestList({ requests, withdraw }: SentRequestListProps) {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const active = statusFilterOf(searchParams.get("status"));
  const shown = filterByStatus(requests, active);

  function choose(status: ApplicationStatus | null) {
    const params = new URLSearchParams(searchParams);
    if (status === null) {
      params.delete("status");
    } else {
      params.set("status", status);
    }
    const query = params.toString();
    // The browser's own history: Next.js keeps useSearchParams in step with it, and
    // nothing goes to the server, since every request is already here.
    window.history.replaceState(
      null,
      "",
      query ? `${pathname}?${query}` : pathname,
    );
  }

  if (requests.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-line bg-surface px-6 py-12 text-center">
        <p className="text-lg font-semibold text-forest">No requests yet</p>
        <p className="mt-2 text-sm text-muted">
          You have not asked to adopt any animal yet.
        </p>
        <div className="mt-6">
          <Link
            href="/animals"
            className="inline-flex min-h-11 items-center justify-center rounded-xl bg-forest px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
          >
            Browse animals
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div
        role="group"
        aria-label="Filter by status"
        className="mb-5 flex flex-wrap gap-2"
      >
        {FILTERS.map((status) => {
          const pressed = status === active;
          return (
            <button
              key={status ?? "all"}
              type="button"
              aria-pressed={pressed}
              onClick={() => choose(status)}
              className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
                pressed
                  ? "bg-forest text-white ring-forest"
                  : "bg-surface text-muted ring-line hover:text-forest hover:ring-forest"
              }`}
            >
              {status === null ? "All" : applicationStatusLabel(status)}
            </button>
          );
        })}
      </div>

      {shown.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-line bg-surface px-6 py-10 text-center">
          <p className="text-sm text-muted">
            No {applicationStatusLabel(active ?? "").toLowerCase()} requests.
          </p>
          <button
            type="button"
            onClick={() => choose(null)}
            className="mt-3 text-sm font-semibold text-forest underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
          >
            Show all
          </button>
        </div>
      ) : (
        <ul className="grid gap-4">
          {shown.map((request) => (
            <li
              key={request.id}
              className="rounded-2xl border border-line bg-surface p-5 shadow-sm"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-xl font-semibold text-forest">
                  <Link
                    href={`/animals/${request.animal_id}`}
                    className="underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
                  >
                    {request.animal_name}
                  </Link>
                </h3>
                <span className="rounded-full bg-surface px-2.5 py-0.5 text-xs font-semibold text-forest ring-1 ring-line">
                  {applicationStatusLabel(request.status)}
                </span>
              </div>
              <p className="mt-1 text-xs text-muted">
                Sent {DATE.format(new Date(request.created_at))}
              </p>

              <p className="mt-4 text-sm font-medium text-forest">Your note</p>
              <p className="mt-1 whitespace-pre-wrap text-sm text-muted">
                {request.note}
              </p>
              {request.owner_note ? (
                <>
                  <p className="mt-4 text-sm font-medium text-forest">
                    Owner&apos;s reply
                  </p>
                  <p className="mt-1 whitespace-pre-wrap text-sm text-muted">
                    {request.owner_note}
                  </p>
                </>
              ) : null}

              {canWithdraw(request.status) ? (
                <div className="mt-4 border-t border-line pt-4">
                  <WithdrawButton
                    applicationId={request.id}
                    animalId={request.animal_id}
                    animalName={request.animal_name}
                    status={request.status}
                    action={withdraw}
                  />
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
