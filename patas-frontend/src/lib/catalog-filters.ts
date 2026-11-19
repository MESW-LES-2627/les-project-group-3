import {
  AGE_GROUP_OPTIONS,
  ANIMAL_SIZE,
  DISTRICT_OPTIONS,
  SPECIES_OPTIONS,
} from "@/lib/animal-profile";

const ALLOWED: Record<string, readonly string[]> = {
  species: SPECIES_OPTIONS.map((option) => option.value),
  size: ANIMAL_SIZE,
  district: DISTRICT_OPTIONS.map((option) => option.value),
  age_group: AGE_GROUP_OPTIONS.map((option) => option.value),
};

export type CatalogFilters = {
  species?: string;
  size?: string;
  district?: string;
  age_group?: string;
};

// A value GET /animals would reject is dropped, so an edited URL still shows
// the catalog instead of an error.
export function catalogFilters(
  params: Record<string, string | string[] | undefined>,
): CatalogFilters {
  return Object.fromEntries(
    Object.entries(ALLOWED).flatMap(([name, allowed]) => {
      const value = params[name];
      return typeof value === "string" && allowed.includes(value)
        ? [[name, value]]
        : [];
    }),
  );
}

// The page is left out on the first page, so filter links stay short.
export function catalogQuery(filters: CatalogFilters, page = 1): string {
  const query = new URLSearchParams(
    Object.entries(filters).filter(([, value]) => value !== undefined),
  );
  if (page > 1) {
    query.set("page", String(page));
  }
  const text = query.toString();
  return text === "" ? "" : `?${text}`;
}
