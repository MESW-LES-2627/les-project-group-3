import { headers } from "next/headers";
import Link from "next/link";

import { fitAction } from "@/app/animals/[id]/actions";
import { auth } from "@/lib/auth";

import { FitCard } from "./fit-card";

type FitSectionProps = {
  animalId: string;
  animalName: string;
  ownerId: string;
};

// Decides who gets the fit card. The page stays public: a visitor is invited to log
// in, and the owner sees nothing, since their own animal has no fit to calculate.
export async function FitSection({
  animalId,
  animalName,
  ownerId,
}: FitSectionProps) {
  const session = await auth.api.getSession({ headers: await headers() });

  if (!session) {
    return (
      <p className="rounded-2xl border border-line bg-surface p-6 text-sm text-muted shadow-sm">
        <Link href="/login" className="font-semibold text-forest underline">
          Log in
        </Link>{" "}
        to see how well {animalName} fits your home.
      </p>
    );
  }
  if (session.user.id === ownerId) {
    return null;
  }
  return (
    <FitCard animalId={animalId} animalName={animalName} action={fitAction} />
  );
}
