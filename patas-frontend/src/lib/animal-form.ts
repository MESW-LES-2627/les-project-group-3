import { OPTIONAL_ANIMAL_FIELDS } from "@/lib/animal-profile";

type OptionalAnimalField = (typeof OPTIONAL_ANIMAL_FIELDS)[number];

const UUID_V4_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function isAnimalId(id: string): boolean {
  return UUID_V4_PATTERN.test(id);
}

// What the publish and edit forms send; on an edit, null clears the field.
export type AnimalDescription = {
  name: string;
  species: string;
  age_in_months: number | null;
} & Record<OptionalAnimalField, string | null>;

export type AnimalFormState = { error: string | null };

const DESCRIPTION_FIELDS = [
  "name",
  "species",
  "age_in_months",
  ...OPTIONAL_ANIMAL_FIELDS,
] as const;

export function formValues(
  description: AnimalDescription,
): Record<string, string> {
  return Object.fromEntries(
    DESCRIPTION_FIELDS.map((name) => {
      const value = description[name];
      return [name, value === null ? "" : String(value)];
    }),
  );
}

export function parseAnimalForm(
  form: FormData,
): { description: AnimalDescription } | AnimalFormState {
  const age = String(form.get("age_in_months") ?? "").trim();
  if (
    age !== "" &&
    (!/^\d+$/.test(age) ||
      !Number.isSafeInteger(Number(age)) ||
      Number(age) < 0)
  ) {
    return { error: "Age must be a whole number of months, zero or greater." };
  }
  const fields = ["name", "species", ...OPTIONAL_ANIMAL_FIELDS];
  if (
    fields.some(
      (name) => form.get(name) !== null && typeof form.get(name) !== "string",
    )
  ) {
    return { error: "Please submit text values for the animal details." };
  }
  const optionalFields = Object.fromEntries(
    OPTIONAL_ANIMAL_FIELDS.map((name) => {
      const value = form.get(name);
      return [
        name,
        typeof value === "string" && value.trim() !== "" ? value.trim() : null,
      ];
    }),
  ) as Record<OptionalAnimalField, string | null>;
  return {
    description: {
      name: String(form.get("name") ?? ""),
      species: String(form.get("species") ?? ""),
      age_in_months: age === "" ? null : Number(age),
      ...optionalFields,
    },
  };
}

// The domain's rule errors are a string; FastAPI's type errors are a list.
export async function rejectionMessage(response: Response): Promise<string> {
  const { detail } = (await response.json()) as { detail: unknown };
  return typeof detail === "string" ? detail : "Invalid animal data";
}
