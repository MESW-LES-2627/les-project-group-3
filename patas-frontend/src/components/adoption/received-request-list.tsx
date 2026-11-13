"use client";

import { TriangleAlert } from "lucide-react";
import { usePathname, useSearchParams } from "next/navigation";

import {
  filterByStatus,
  statusFilterOf,
  type ReceivedRequest,
} from "@/lib/adoption";
import {
  APPLICATION_STATUS,
  applicationStatusLabel,
  type ApplicationStatus,
} from "@/lib/adoption-status";
import {
  ENERGY_OPTIONS,
  EXPERIENCE_OPTIONS,
  HOUSING_OPTIONS,
  TIME_AWAY_OPTIONS,
} from "@/lib/matchmaker-profile";

const FILTERS: (ApplicationStatus | null)[] = [null, ...APPLICATION_STATUS];
const DATE = new Intl.DateTimeFormat("en-GB", {
  dateStyle: "medium",
  timeZone: "UTC",
});

type ReceivedRequestListProps = {
  requests: ReceivedRequest[];
};

function optionLabel<T extends string>(
  options: readonly { value: T; label: string }[],
  value: T,
): string {
  return options.find((option) => option.value === value)?.label ?? value;
}

function profileAnswers(request: ReceivedRequest): [string, string][] {
  const profile = request.applicant_profile;
  return [
    ["Home", optionLabel(HOUSING_OPTIONS, profile.housing)],
    ["Time away", optionLabel(TIME_AWAY_OPTIONS, profile.time_away)],
    ["Activity", optionLabel(ENERGY_OPTIONS, profile.activity)],
    ["Experience", optionLabel(EXPERIENCE_OPTIONS, profile.experience)],
    ["Children", profile.has_children ? "Yes" : "No"],
    ["Dogs", profile.has_dogs ? "Yes" : "No"],
    ["Cats", profile.has_cats ? "Yes" : "No"],
  ];
}

export function ReceivedRequestList({ requests }: ReceivedRequestListProps) {
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
    window.history.replaceState(
      null,
      "",
      query ? `${pathname}?${query}` : pathname,
    );
  }

  if (requests.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-line bg-surface px-6 py-12 text-center">
        <p className="text-lg font-semibold text-forest">
          No requests received yet
        </p>
        <p className="mt-2 text-sm text-muted">
          Requests for your animals will show up here.
        </p>
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
                  {request.animal_name}
                </h3>
                <span className="rounded-full bg-surface px-2.5 py-0.5 text-xs font-semibold text-forest ring-1 ring-line">
                  {applicationStatusLabel(request.status)}
                </span>
              </div>
              <p className="mt-1 text-xs text-muted">
                Received {DATE.format(new Date(request.created_at))}
              </p>

              <p className="mt-4 text-sm font-medium text-forest">
                Applicant&apos;s note
              </p>
              <p className="mt-1 whitespace-pre-wrap text-sm text-muted">
                {request.note}
              </p>

              <section
                aria-label="Applicant's Matchmaker profile"
                className="mt-5 border-t border-line pt-4"
              >
                <h4 className="text-sm font-semibold text-forest">
                  Matchmaker profile
                </h4>
                <dl className="mt-3 grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
                  {profileAnswers(request).map(([label, answer]) => (
                    <div
                      key={label}
                      className="flex items-baseline justify-between gap-3"
                    >
                      <dt className="text-muted">{label}</dt>
                      <dd className="text-right font-medium text-forest">
                        {answer}
                      </dd>
                    </div>
                  ))}
                </dl>
              </section>

              {request.compatibility_concerns.length > 0 ? (
                <section
                  aria-label="Compatibility concerns"
                  className="mt-4 rounded-xl bg-amber-50 p-4"
                >
                  <h4 className="flex items-center gap-2 text-sm font-semibold text-amber-900">
                    <TriangleAlert
                      aria-hidden="true"
                      className="size-4 shrink-0 text-amber-700"
                    />
                    Compatibility concerns
                  </h4>
                  <ul className="mt-2 grid gap-1.5 text-sm text-amber-900">
                    {request.compatibility_concerns.map((concern) => (
                      <li key={concern}>{concern}</li>
                    ))}
                  </ul>
                </section>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
