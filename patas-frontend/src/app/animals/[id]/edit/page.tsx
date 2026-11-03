import type { Metadata } from "next";
import { headers } from "next/headers";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { Suspense } from "react";

import { isAnimalId, type AnimalDescription } from "@/lib/animal-form";
import { auth } from "@/lib/auth";
import { backendUrl } from "@/lib/backend";

import { AnimalForm } from "@/components/animal/animal-form";

import { editAnimalAction } from "./actions";

export const metadata: Metadata = {
  title: "Edit animal | Patas",
};

type Props = {
  params: Promise<{ id: string }>;
};

type OwnedAnimal = AnimalDescription & { adoption_status: string };

// Not GET /animals/{id}: that one hides unpublished animals.
async function getMyAnimal(
  id: string,
  token: string,
): Promise<OwnedAnimal | null> {
  const response = await fetch(
    `${backendUrl()}/me/animals/${encodeURIComponent(id)}`,
    {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    },
  );
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(
      `Unable to load the animal: backend returned ${response.status}`,
    );
  }
  return (await response.json()) as OwnedAnimal;
}

async function EditAnimal({ params }: Props) {
  const { id } = await params;
  if (!isAnimalId(id)) {
    notFound();
  }
  const requestHeaders = await headers();
  const session = await auth.api.getSession({ headers: requestHeaders });
  if (!session) {
    redirect("/login");
  }
  const { token } = await auth.api.getToken({ headers: requestHeaders });
  const animal = await getMyAnimal(id, token);
  if (!animal) {
    notFound();
  }

  return (
    <>
      <header className="mb-10 max-w-2xl">
        <h1 className="text-3xl font-semibold text-forest sm:text-4xl">
          Edit {animal.name}
        </h1>
        <p className="mt-3 text-base leading-7 text-muted">
          Name and species are required. Details left empty are removed when
          you save.
          {animal.adoption_status === "unavailable" &&
            " This animal stays unpublished."}
        </p>
      </header>
      <AnimalForm
        action={editAnimalAction.bind(null, id)}
        initial={animal}
        submitLabel="Save changes"
        pendingLabel="Saving…"
      />
    </>
  );
}

export default function EditAnimalPage({ params }: Props) {
  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6 sm:py-14">
      <Link
        href="/animals/mine"
        className="mb-8 inline-flex items-center text-sm font-medium text-muted transition hover:text-forest"
      >
        ← Back to my animals
      </Link>
      <Suspense fallback={<p>Loading…</p>}>
        <EditAnimal params={params} />
      </Suspense>
    </main>
  );
}
