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

// The last band of the animal card. Decides who gets the fit: the page stays public,
// so a visitor is invited to log in, and the owner sees nothing (not even the
// divider), since their own animal has no fit to calculate.
export async function FitSection({
  animalId,
  animalName,
  ownerId,
}: FitSectionProps) {
  const session = await auth.api.getSession({ headers: await headers() });

  if (session?.user.id === ownerId) {
    return null;
  }
  return (
    <div className="mt-6 border-t border-line pt-6">
      {session ? (
        <FitCard
          animalId={animalId}
          animalName={animalName}
          action={fitAction}
        />
      ) : (
        <p className="text-sm text-muted">
          <Link href="/login" className="font-semibold text-forest underline">
            Log in
          </Link>{" "}
          to see how well {animalName} fits your home.
        </p>
      )}
    </div>
  );
}
