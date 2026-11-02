import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { backendUrl } from "@/lib/backend";

type Props = {
  params: Promise<{ id: string }>;
};



type Animal = {
  id: string;
  species: string;
  name: string;
  owner_id: string;
  owner_name: string;
  age_in_months: number | null;
  adoption_status: string;
  sex: string | null;
  is_neutered: string | null;
  postal_code: string | null;
  size: string | null;
  activity_level: string | null;
  space_requirement: string | null;
  shedding: string | null;
  grooming_needs: string | null;
  behaves_well_with_children: string | null;
  behaves_well_with_dogs: string | null;
  behaves_well_with_cats: string | null;
  behaves_well_with_other_animals: string | null;
  training_needs: string | null;
  tolerance_for_time_alone: string | null;
  noise_level: string | null;
  suitable_for_first_time_owners: string | null;
  special_care_notes: string | null;
  other_details: string | null;
};

async function getAnimal(id: string): Promise<Animal | null> {
  const response = await fetch(`${backendUrl()}/animals/${id}`, {
    cache: "no-store",
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Unable to load animal: backend returned ${response.status}`);
  }

  return (await response.json()) as Animal;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  try {
    const animal = await getAnimal(id);
    return {
      title: animal ? `${animal.name} | Patas` : "Animal Not Found | Patas",
    };
  } catch {
    return {
      title: "Animal Profile | Patas",
    };
  }
}

async function AnimalDetail({ params }: Props) {
  const { id } = await params;
  const animal = await getAnimal(id);

  if (!animal) {
    notFound();
  }

  return (
    <section className="rounded-2xl border border-line bg-surface p-6 shadow-sm sm:p-8">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="rounded-full bg-leaf/10 px-3 py-1 text-xs font-semibold capitalize text-leaf">
          {animal.species}
        </span>
        <span className="rounded-full bg-sunlight/20 px-3 py-1 text-xs font-medium capitalize text-forest">
          {animal.adoption_status.replaceAll("_", " ")}
        </span>
      </div>

      <h1 className="mt-4 text-3xl font-bold text-forest sm:text-4xl">
        {animal.name}
      </h1>

      <p className="mt-2 text-sm text-muted">
        Published by {animal.owner_name}
      </p>

      <div className="mt-6 grid grid-cols-2 gap-4 border-t border-line pt-6 sm:grid-cols-3">
        <div>
          <span className="text-xs font-medium text-muted">Age</span>
          <p className="text-sm font-semibold text-forest">
            {animal.age_in_months !== null
              ? `${animal.age_in_months} months`
              : "Not listed"}
          </p>
        </div>
        {animal.sex && (
          <div>
            <span className="text-xs font-medium text-muted">Sex</span>
            <p className="text-sm font-semibold capitalize text-forest">
              {animal.sex}
            </p>
          </div>
        )}
        {animal.size && (
          <div>
            <span className="text-xs font-medium text-muted">Size</span>
            <p className="text-sm font-semibold capitalize text-forest">
              {animal.size}
            </p>
          </div>
        )}
        {animal.postal_code && (
          <div>
            <span className="text-xs font-medium text-muted">Postal Code</span>
            <p className="text-sm font-semibold text-forest">
              {animal.postal_code}
            </p>
          </div>
        )}
      </div>

      {(animal.special_care_notes || animal.other_details) && (
        <div className="mt-6 border-t border-line pt-6 space-y-4">
          {animal.special_care_notes && (
            <div>
              <h2 className="text-sm font-semibold text-forest">Special Care</h2>
              <p className="mt-1 text-sm text-muted">
                {animal.special_care_notes}
              </p>
            </div>
          )}
          {animal.other_details && (
            <div>
              <h2 className="text-sm font-semibold text-forest">Other Details</h2>
              <p className="mt-1 text-sm text-muted">
                {animal.other_details}
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default function AnimalDetailPage({ params }: Props) {
  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-8 px-4 py-10 sm:px-6 sm:py-14">
      <Link
        href="/animals"
        className="inline-flex items-center text-sm font-medium text-muted transition hover:text-forest"
      >
        ← Back to animals
      </Link>

      <Suspense fallback={<p>Loading animal profile...</p>}>
        <AnimalDetail params={params} />
      </Suspense>
    </main>
  );
}


