import type { Metadata } from "next";
import { headers } from "next/headers";
import Link from "next/link";
import { Suspense } from "react";

import { auth } from "@/lib/auth";
import { backendUrl } from "@/lib/backend";

export const metadata: Metadata = {
  title: "Animals | Patas",
};

type Animal = {
  id: string;
  species: string;
  name: string;
  owner_id: string;
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
    (animal.age_in_months === null || typeof animal.age_in_months === "number") &&
    typeof animal.adoption_status === "string"
  );
}

async function getAnimals(): Promise<Animal[]> {
  const response = await fetch(`${backendUrl()}/animals`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`Unable to load animals: backend returned ${response.status}`);
  }

  const payload: unknown = await response.json();
  if (!Array.isArray(payload) || !payload.every(isAnimal)) {
    throw new Error("Unable to load animals: backend returned invalid data");
  }

  return payload;
}

async function AnimalList() {
  const animals = await getAnimals();

  if (animals.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-line bg-surface px-6 py-12 text-center">
        <p className="text-lg font-semibold text-forest">No animals listed yet</p>
        <p className="mt-2 text-sm text-muted">
          Check back soon to meet the next animals looking for a home.
        </p>
      </div>
    );
  }

  return (
    <section aria-labelledby="available-animals-heading">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-2">
        <h2
          id="available-animals-heading"
          className="text-xl font-semibold text-forest"
        >
          Animals in our community
        </h2>
        <p className="text-sm text-muted">
          {animals.length} {animals.length === 1 ? "animal" : "animals"}
        </p>
      </div>
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {animals.map((animal) => (
          <li
            key={animal.id}
            className="flex min-h-48 flex-col rounded-2xl border border-line bg-surface p-5 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-leaf/40 hover:shadow-md"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="rounded-full bg-leaf/10 px-3 py-1 text-xs font-semibold capitalize text-leaf">
                {animal.species}
              </span>
              <span className="rounded-full bg-sunlight/20 px-3 py-1 text-xs font-medium capitalize text-forest">
                {animal.adoption_status.replaceAll("_", " ")}
              </span>
            </div>
            <h3 className="mt-5 text-2xl font-semibold text-forest">
              {animal.name}
            </h3>
            <div className="mt-auto border-t border-line pt-4">
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
          </li>
        ))}
      </ul>
    </section>
  );
}

// Visitors see the catalog too (AC5); only a logged-in user gets the button.
async function PublishLink() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) {
    return (
      <p className="text-sm text-neutral-600">
        <Link href="/login" className="underline">
          Log in
        </Link>{" "}
        to publish an animal.
      </p>
    );
  }
  return (
    <Link
      href="/animals/new"
      className="inline-flex min-h-11 items-center justify-center rounded-xl bg-forest px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
    >
      Publish an animal
    </Link>
  );
}

export default function AnimalsPage() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-4 py-10 sm:px-6 sm:py-14">
      <section className="flex flex-col justify-between gap-6 border-b border-line pb-8 sm:flex-row sm:items-end">
        <div className="max-w-2xl">
          <p className="mb-3 inline-flex items-center gap-2 text-xs font-bold uppercase text-leaf">
            <span className="size-2 rounded-full bg-sunlight" />
            Adoption catalog
          </p>
          <h1 className="text-4xl font-semibold text-forest sm:text-5xl">
            A new friend is waiting.
          </h1>
          <p className="mt-3 max-w-xl text-base leading-7 text-muted">
            Meet the animals in our community and find the one who feels like
            family.
          </p>
        </div>
        <Suspense fallback={null}>
          <PublishLink />
        </Suspense>
      </section>
      <Suspense fallback={<p>Loading animals…</p>}>
        <AnimalList />
      </Suspense>
    </main>
  );
}
