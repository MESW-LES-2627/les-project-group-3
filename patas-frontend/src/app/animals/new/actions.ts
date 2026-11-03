"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { auth } from "@/lib/auth";
import { backendUrl } from "@/lib/backend";
import {
  parseAnimalForm,
  rejectionMessage,
  type AnimalFormState,
} from "@/lib/animal-form";

export async function publishAnimalAction(
  _previous: AnimalFormState,
  form: FormData,
): Promise<AnimalFormState> {
  // Re-checked here, not only on the page: a Server Action is a public endpoint.
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
    response = await fetch(`${backendUrl()}/animals`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(parsed.description),
    });
  } catch {
    return { error: "The service is unavailable, please try again." };
  }

  if (response.status === 422) {
    return { error: await rejectionMessage(response) };
  }
  if (!response.ok) {
    return { error: `Publishing failed (backend returned ${response.status})` };
  }
  redirect("/animals");
}
