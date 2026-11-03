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

type DetailItem = {
  label: string;
  value: string | number | null;
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

function formatValue(value: string): string {
  return value.replaceAll("_", " ").replace(/^\w/, (letter) => letter.toUpperCase());
}

function DetailGroup({
  title,
  items,
}: {
  title: string;
  items: DetailItem[];
}) {
  return (
    <section className="border-t border-line pt-5" aria-label={title}>
      <h2 className="text-lg font-semibold text-forest">{title}</h2>
      <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-5 sm:grid-cols-3">
        {items.map(({ label, value }) => (
          <div key={label}>
            <dt className="text-xs font-medium text-muted">{label}</dt>
            <dd className="mt-1 text-sm font-semibold text-forest">
              {value === null
                ? "Not provided"
                : typeof value === "number"
                  ? `${value} months`
                  : formatValue(value)}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function TextDetail({ title, value }: { title: string; value: string | null }) {
  return (
    <section>
      <h2 className="text-sm font-semibold text-forest">{title}</h2>
      <p className="mt-1 whitespace-pre-wrap text-sm text-muted">
        {value ?? "Not provided"}
      </p>
    </section>
  );
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
          {formatValue(animal.species)}
        </span>
        <span className="rounded-full bg-sunlight/20 px-3 py-1 text-xs font-medium capitalize text-forest">
          {formatValue(animal.adoption_status)}
        </span>
      </div>

      <h1 className="mt-4 text-3xl font-bold text-forest sm:text-4xl">
        {animal.name}
      </h1>

      <p className="mt-2 text-sm text-muted">
        Published by {animal.owner_name}
      </p>

      <div className="mt-6 space-y-6">
        <DetailGroup
          title="About"
          items={[
            {
              label: "Age",
              value: animal.age_in_months,
            },
            { label: "Sex", value: animal.sex },
            { label: "Neutered status", value: animal.is_neutered },
            { label: "Size", value: animal.size },
            { label: "Postal code", value: animal.postal_code },
          ]}
        />
        <DetailGroup
          title="Daily care"
          items={[
            { label: "Activity level", value: animal.activity_level },
            { label: "Space requirement", value: animal.space_requirement },
            { label: "Shedding", value: animal.shedding },
            { label: "Grooming needs", value: animal.grooming_needs },
            { label: "Training needs", value: animal.training_needs },
            {
              label: "Tolerance for time alone",
              value: animal.tolerance_for_time_alone,
            },
            { label: "Noise level", value: animal.noise_level },
          ]}
        />
        <DetailGroup
          title="Compatibility"
          items={[
            {
              label: "With children",
              value: animal.behaves_well_with_children,
            },
            { label: "With dogs", value: animal.behaves_well_with_dogs },
            { label: "With cats", value: animal.behaves_well_with_cats },
            {
              label: "With other animals",
              value: animal.behaves_well_with_other_animals,
            },
            {
              label: "Suitable for first-time owners",
              value: animal.suitable_for_first_time_owners,
            },
          ]}
        />
        <section className="space-y-4 border-t border-line pt-5">
          <TextDetail title="Special care" value={animal.special_care_notes} />
          <TextDetail title="Other details" value={animal.other_details} />
        </section>
      </div>
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
