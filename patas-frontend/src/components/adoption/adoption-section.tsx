import { headers } from "next/headers";
import Link from "next/link";

import { requestToAdoptAction } from "@/app/animals/[id]/actions";
import { withdrawRequestAction } from "@/app/requests/actions";
import { getMyApplication } from "@/lib/adoption-api";
import { applicationStatusLabel } from "@/lib/adoption-status";
import { auth } from "@/lib/auth";

import { RequestForm } from "./request-form";
import { WithdrawButton } from "./withdraw-button";

type AdoptionSectionProps = {
  animalId: string;
  animalName: string;
  ownerId: string;
  animalStatus: string;
};

// The band after the fit. Decides what the visitor can do about adopting: the page
// stays public, so a visitor is invited to log in, and the owner sees nothing, since
// nobody asks to adopt their own animal.
export async function AdoptionSection({
  animalId,
  animalName,
  ownerId,
  animalStatus,
}: AdoptionSectionProps) {
  const session = await auth.api.getSession({ headers: await headers() });

  if (session?.user.id === ownerId) {
    return null;
  }

  return (
    <section
      aria-labelledby="adoption-heading"
      className="mt-6 border-t border-line pt-5"
    >
      <h2 id="adoption-heading" className="text-lg font-semibold text-forest">
        Adopt {animalName}
      </h2>
      <div className="mt-4">
        {session ? (
          <SignedInAdoption
            animalId={animalId}
            animalName={animalName}
            animalStatus={animalStatus}
          />
        ) : (
          <p className="text-sm text-muted">
            <Link href="/login" className="font-semibold text-forest underline">
              Log in
            </Link>{" "}
            to ask to adopt {animalName}.
          </p>
        )}
      </div>
    </section>
  );
}

async function SignedInAdoption({
  animalId,
  animalName,
  animalStatus,
}: Omit<AdoptionSectionProps, "ownerId">) {
  const mine = await getMyApplication(animalId);

  if (mine.kind === "unavailable") {
    return (
      <p className="text-sm text-muted">
        Requests are not available right now, please try again later.
      </p>
    );
  }
  // A request that exists is shown whatever the animal's status is now.
  if (mine.kind === "active") {
    return (
      <div>
        <p className="flex items-center gap-2 text-sm font-medium text-forest">
          Your request
          <span className="rounded-full bg-surface px-2.5 py-0.5 text-xs font-semibold text-forest ring-1 ring-line">
            {applicationStatusLabel(mine.application.status)}
          </span>
        </p>
        <p className="mt-2 whitespace-pre-wrap text-sm text-muted">
          {mine.application.note}
        </p>
        <div className="mt-4 flex flex-wrap items-start gap-4">
          <WithdrawButton
            applicationId={mine.application.id}
            animalId={animalId}
            animalName={animalName}
            status={mine.application.status}
            action={withdrawRequestAction}
          />
          <Link
            href="/requests"
            className="py-1.5 text-xs font-semibold text-forest underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
          >
            See all your requests
          </Link>
        </div>
      </div>
    );
  }
  if (animalStatus !== "available") {
    return (
      <p className="text-sm text-muted">
        {animalName} is not taking requests right now.
      </p>
    );
  }
  return (
    <RequestForm
      animalId={animalId}
      animalName={animalName}
      action={requestToAdoptAction}
    />
  );
}
