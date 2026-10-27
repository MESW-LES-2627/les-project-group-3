import type { Metadata } from "next";
import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { Suspense } from "react";

import { auth } from "@/lib/auth";

import { PublishForm } from "./publish-form";

export const metadata: Metadata = {
  title: "Publish an animal | Patas",
};

async function RequireSession({ children }: { children: React.ReactNode }) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) {
    redirect("/login");
  }
  return children;
}

export default function NewAnimalPage() {
  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6 sm:py-14">
      <header className="mb-10 max-w-2xl">
        <h1 className="text-3xl font-semibold text-forest sm:text-4xl">
          Tell us about the animal
        </h1>
        <p className="mt-3 text-base leading-7 text-muted">
          Share the animal&apos;s needs and personality to help people find a
          good fit. Name and species are required; all other profile details are
          optional.
        </p>
      </header>
      <Suspense fallback={<p>Loading…</p>}>
        <RequireSession>
          <PublishForm />
        </RequireSession>
      </Suspense>
    </main>
  );
}
