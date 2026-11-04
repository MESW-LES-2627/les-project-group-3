import Form from "next/form";
import Link from "next/link";
import { Fragment } from "react";

import {
  AGE_GROUP_OPTIONS,
  DISTRICT_OPTIONS,
  SIZE_OPTIONS,
  SPECIES_OPTIONS,
} from "@/lib/animal-profile";
import { catalogQuery, type CatalogFilters } from "@/lib/catalog-filters";

function FilterSelect({
  label,
  name,
  value,
  options,
}: {
  label: string;
  name: string;
  value: string | undefined;
  options: readonly { value: string; label: string }[];
}) {
  return (
    <label className="flex flex-col gap-1.5 text-sm font-medium text-forest">
      {label}
      <select
        name={name}
        defaultValue={value ?? ""}
        className="w-full rounded-xl border border-muted/75 bg-surface px-3 py-2.5 text-sm text-forest outline-none focus-visible:border-leaf focus-visible:ring-2 focus-visible:ring-leaf/30"
      >
        <option value="">Any</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function CatalogFilterForm({ filters }: { filters: CatalogFilters }) {
  return (
    <Form
      action="/animals"
      scroll={false}
      aria-label="Filter animals"
      className="grid gap-4 rounded-2xl border border-line bg-surface p-5 shadow-sm sm:grid-cols-2 lg:grid-cols-[repeat(4,minmax(0,1fr))_auto] lg:items-end"
    >
      {/* A new key when the URL changes, so the selects show the applied
          filters after Clear or the back button too. */}
      <Fragment key={catalogQuery(filters)}>
        <FilterSelect
          label="Species"
          name="species"
          value={filters.species}
          options={SPECIES_OPTIONS}
        />
        <FilterSelect
          label="Size"
          name="size"
          value={filters.size}
          options={SIZE_OPTIONS}
        />
        <FilterSelect
          label="Age group"
          name="age_group"
          value={filters.age_group}
          options={AGE_GROUP_OPTIONS}
        />
        <FilterSelect
          label="District"
          name="district"
          value={filters.district}
          options={DISTRICT_OPTIONS}
        />
      </Fragment>
      <div className="flex items-center gap-4 sm:col-span-2 lg:col-span-1">
        <button
          type="submit"
          className="inline-flex min-h-11 items-center justify-center rounded-xl bg-forest px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
        >
          Apply filters
        </button>
        {Object.keys(filters).length > 0 && (
          <Link
            href="/animals"
            className="text-sm font-medium text-muted underline hover:text-forest"
          >
            Clear filters
          </Link>
        )}
      </div>
    </Form>
  );
}
