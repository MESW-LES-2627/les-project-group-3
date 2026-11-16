"use server";

import { revalidatePath } from "next/cache";
import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { isAnimalId } from "@/lib/animal-form";
import { auth } from "@/lib/auth";
import { backendUrl } from "@/lib/backend";

// Unpublish and republish differ only in the endpoint and the wording.
async function changeVisibility(
  animalId: string,
  action: "unpublish" | "republish",
): Promise<{ error?: string }> {
  if (!isAnimalId(animalId)) {
    return { error: "Invalid animal id." };
  }

  const requestHeaders = await headers();
  const session = await auth.api.getSession({ headers: requestHeaders });
  if (!session) {
    redirect("/login");
  }

  const { token } = await auth.api.getToken({ headers: requestHeaders });

  try {
    const response = await fetch(`${backendUrl()}/animals/${encodeURIComponent(animalId)}/${action}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (response.status === 403) {
      return { error: `You are not authorized to ${action} this animal.` };
    }

    if (response.status === 409) {
      return { error: `This animal is reserved or adopted, so it cannot be ${action}ed.` };
    }

    if (!response.ok) {
      return { error: `Failed to ${action} animal (backend returned ${response.status}).` };
    }
  } catch {
    return { error: "The service is currently unavailable. Please try again later." };
  }

  revalidatePath("/animals");
  revalidatePath("/animals/mine");
  return {};
}

export async function unpublishAnimalAction(animalId: string): Promise<{ error?: string }> {
  return changeVisibility(animalId, "unpublish");
}

export async function republishAnimalAction(animalId: string): Promise<{ error?: string }> {
  return changeVisibility(animalId, "republish");
}
