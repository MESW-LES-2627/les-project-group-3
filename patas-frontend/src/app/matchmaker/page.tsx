import type { Metadata } from "next";
import { Suspense } from "react";

import { FormSkeleton } from "@/components/matchmaker/form-skeleton";
import { MatchmakerProfileForm } from "@/components/matchmaker/matchmaker-profile-form";
import { getMatchmakerProfile } from "@/lib/matchmaker-api";

import { deleteProfileAction, saveProfileAction } from "./actions";

export const metadata: Metadata = {
  title: "Matchmaker profile | Patas",
};

// Reads the saved profile on the server; a signed-out visitor is sent to /login there.
async function SavedProfileForm() {
  const saved = await getMatchmakerProfile();
  return (
    <MatchmakerProfileForm
      saved={saved}
      save={saveProfileAction}
      remove={deleteProfileAction}
    />
  );
}

export default function MatchmakerPage() {
  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6 sm:py-14">
      <header className="mb-10 max-w-2xl">
        <h1 className="text-3xl font-semibold text-forest sm:text-4xl">
          Tell us about your home
        </h1>
        <p className="mt-3 text-base leading-7 text-muted">
          Answer these once and the Matchmaker can suggest animals that fit your
          life. You can change your answers whenever you like.
        </p>
      </header>
      <Suspense fallback={<FormSkeleton />}>
        <SavedProfileForm />
      </Suspense>
    </main>
  );
}
