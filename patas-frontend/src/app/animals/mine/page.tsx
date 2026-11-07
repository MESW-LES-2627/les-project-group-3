import type { Metadata } from "next";
import { headers } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Suspense } from "react";

import { animalStatusLabel } from "@/lib/adoption-status";
import { auth } from "@/lib/auth";
import { backendUrl } from "@/lib/backend";
import { UnpublishButton } from "./unpublish-button";

export const metadata: Metadata = {
  title: "My Animals | Patas",
};

type Animal = {
  id: string;
  species: string;
  name: string;
  owner_id: string;
  owner_name: string;
  age_in_months: number | null;
  adoption_status: string;
};

function isAnimal(value: unknown): value is Animal {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const animal = value as Record<string, unknown>;
  return (
    typeof animal.id === "string" &&
    typeof animal.species === "string" &&
    typeof animal.name === "string" &&
    typeof animal.owner_id === "string" &&
    typeof animal.owner_name === "string" &&
    (animal.age_in_months === null || typeof animal.age_in_months === "number") &&
    typeof animal.adoption_status === "string"
  );
}


async function getMyAnimals(token: string): Promise<Animal[]> {
  const response = await fetch(`${backendUrl()}/me/animals`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Unable to load my animals: backend returned ${response.status}`);
  }

  const payload: unknown = await response.json();
  if (!Array.isArray(payload) || !payload.every(isAnimal)) {
    throw new Error("Unable to load my animals: backend returned invalid data");
  }

  return payload;
}

async function MyAnimalList({ token }: { token: string }) {
  const animals = await getMyAnimals(token);

  if (animals.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-line bg-surface px-6 py-12 text-center">
        <p className="text-lg font-semibold text-forest">No animals listed yet</p>
        <p className="mt-2 text-sm text-muted">
          You haven&apos;t published any animals yet.
        </p>
        <div className="mt-6">
          <Link
            href="/animals/new"
            className="inline-flex min-h-11 items-center justify-center rounded-xl bg-forest px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
          >
            Publish an animal
          </Link>
        </div>
      </div>
    );
  }

  return (
    <section aria-labelledby="my-animals-heading">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-2">
        <h2 id="my-animals-heading" className="text-xl font-semibold text-forest">
          Your animal listings
        </h2>
        <p className="text-sm text-muted">
          {animals.length} {animals.length === 1 ? "animal" : "animals"}
        </p>
      </div>
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {animals.map((animal) => {
          const isUnpublished = animal.adoption_status === "unavailable";
          return (
            <li
              key={animal.id}
              className="flex min-h-48 flex-col rounded-2xl border border-line bg-surface p-5 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-leaf/40 hover:shadow-md"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="rounded-full bg-leaf/10 px-3 py-1 text-xs font-semibold capitalize text-leaf">
                  {animal.species}
                </span>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-medium ${
                    isUnpublished
                      ? "bg-muted/15 text-muted"
                      : "bg-sunlight/20 text-forest"
                  }`}
                >
                  {animalStatusLabel(animal.adoption_status)}
                </span>
              </div>
              <h3 className="mt-5 text-2xl font-semibold text-forest">
                {animal.name}
              </h3>
              <p className="mt-1 text-xs text-muted">
                Published by {animal.owner_name}
              </p>
              <div className="mt-2">

                {animal.age_in_months !== null ? (
                  <p className="text-sm text-muted">
                    <span className="font-medium text-forest">Age</span>
                    <span aria-hidden="true"> · </span>
                    {animal.age_in_months} months
                  </p>
                ) : (
                  <p className="text-sm text-muted">Age not listed</p>
                )}
              </div>
              <div className="mt-auto flex items-center justify-between border-t border-line pt-4">
                <span className="text-xs text-muted">
                  {isUnpublished ? "Not visible in catalog" : "Visible in catalog"}
                </span>
                <div className="flex items-center gap-3">
                  <Link
                    href={`/animals/${animal.id}/edit`}
                    aria-label={`Edit ${animal.name}`}
                    className="text-sm font-semibold text-forest underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
                  >
                    Edit
                  </Link>
                  {!isUnpublished && (
                    <UnpublishButton animalId={animal.id} animalName={animal.name} />
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

async function AuthenticatedMyAnimalList() {
  const requestHeaders = await headers();
  const session = await auth.api.getSession({ headers: requestHeaders });
  if (!session) {
    redirect("/login");
  }

  const { token } = await auth.api.getToken({ headers: requestHeaders });
  return <MyAnimalList token={token} />;
}

export default async function MyAnimalsPage() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-4 py-10 sm:px-6 sm:py-14">
      <section className="flex flex-col justify-between gap-6 border-b border-line pb-8 sm:flex-row sm:items-end">
        <div className="max-w-2xl">
          <p className="mb-3 inline-flex items-center gap-2 text-xs font-bold uppercase text-leaf">
            <span className="size-2 rounded-full bg-sunlight" />
            Owner dashboard
          </p>
          <h1 className="text-4xl font-semibold text-forest sm:text-5xl">
            My animals
          </h1>
          <p className="mt-3 max-w-xl text-base leading-7 text-muted">
            Manage all the animals you have registered, including active listings and
            unpublished animals.
          </p>
        </div>
        <div>
          <Link
            href="/animals/new"
            className="inline-flex min-h-11 items-center justify-center rounded-xl bg-forest px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
          >
            Publish an animal
          </Link>
        </div>
      </section>
      <Suspense fallback={<p>Loading your animals…</p>}>
        <AuthenticatedMyAnimalList />
      </Suspense>
    </main>
  );
}
