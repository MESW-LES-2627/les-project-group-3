"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { auth } from "@/lib/auth";
import { backendUrl } from "@/lib/backend";
import { OPTIONAL_ANIMAL_FIELDS } from "@/lib/animal-profile";

export type PublishState = { error: string | null };

export async function publishAnimalAction(
  _previous: PublishState,
  form: FormData,
): Promise<PublishState> {
  // Re-checked here, not only on the page: a Server Action is a public endpoint.
  const requestHeaders = await headers();
  const session = await auth.api.getSession({ headers: requestHeaders });
  if (!session) {
    redirect("/login");
  }
  const { token } = await auth.api.getToken({ headers: requestHeaders });

  const age = String(form.get("age_in_months") ?? "").trim();
  const ageInMonths = age === "" ? null : Number(age);
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
  );
  let response: Response;
  try {
    response = await fetch(`${backendUrl()}/animals`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: String(form.get("name") ?? ""),
        species: String(form.get("species") ?? ""),
        age_in_months: ageInMonths,
        ...optionalFields,
      }),
    });
  } catch {
    return { error: "The service is unavailable, please try again." };
  }

  if (response.status === 422) {
    // The domain's rule errors are a string; FastAPI's type errors are a list.
    const { detail } = (await response.json()) as { detail: unknown };
    return { error: typeof detail === "string" ? detail : "Invalid animal data" };
  }
  if (!response.ok) {
    return { error: `Publishing failed (backend returned ${response.status})` };
  }
  redirect("/animals");
}
