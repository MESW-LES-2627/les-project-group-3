"use server";

import { revalidatePath } from "next/cache";
import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { auth } from "@/lib/auth";
import { backendUrl } from "@/lib/backend";

export async function unpublishAnimalAction(animalId: string): Promise<{ error?: string }> {
  const requestHeaders = await headers();
  const session = await auth.api.getSession({ headers: requestHeaders });
  if (!session) {
    redirect("/login");
  }

  const { token } = await auth.api.getToken({ headers: requestHeaders });

  try {
    const response = await fetch(`${backendUrl()}/animals/${animalId}/unpublish`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (response.status === 403) {
      return { error: "You are not authorized to unpublish this animal." };
    }

    if (!response.ok) {
      return { error: `Failed to unpublish animal (backend returned ${response.status}).` };
    }
  } catch {
    return { error: "The service is currently unavailable. Please try again later." };
  }

  revalidatePath("/animals");
  revalidatePath("/animals/mine");
  return {};
}
