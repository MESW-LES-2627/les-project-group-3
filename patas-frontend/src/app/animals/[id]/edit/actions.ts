"use server";

import { revalidatePath } from "next/cache";
import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { auth } from "@/lib/auth";
import { backendUrl } from "@/lib/backend";
import {
  isAnimalId,
  parseAnimalForm,
  rejectionMessage,
  type AnimalFormState,
} from "@/lib/animal-form";

export async function editAnimalAction(
  animalId: string,
  _previous: AnimalFormState,
  form: FormData,
): Promise<AnimalFormState> {
  // Re-checked here, not only on the page: a Server Action is a public endpoint.
  if (!isAnimalId(animalId)) {
    return { error: "Invalid animal id." };
  }
  const requestHeaders = await headers();
  const session = await auth.api.getSession({ headers: requestHeaders });
  if (!session) {
    redirect("/login");
  }
  const { token } = await auth.api.getToken({ headers: requestHeaders });

  const parsed = parseAnimalForm(form);
  if (!("description" in parsed)) {
    return parsed;
  }
  let response: Response;
  try {
    response = await fetch(
      `${backendUrl()}/animals/${encodeURIComponent(animalId)}`,
      {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(parsed.description),
      },
    );
  } catch {
    return { error: "The service is unavailable, please try again." };
  }

  if (response.status === 422) {
    return { error: await rejectionMessage(response) };
  }
  if (response.status === 403) {
    return { error: "You can only edit your own animals." };
  }
  if (response.status === 404) {
    return { error: "This animal no longer exists." };
  }
  if (!response.ok) {
    return { error: `Saving failed (backend returned ${response.status})` };
  }
  revalidatePath("/animals");
  revalidatePath("/animals/mine");
  revalidatePath(`/animals/${animalId}`);
  redirect("/animals/mine");
}
