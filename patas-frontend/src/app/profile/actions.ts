"use server";

import { revalidatePath } from "next/cache";
import { headers } from "next/headers";

import { auth } from "@/lib/auth";
import { backendUrl } from "@/lib/backend";

export type ProfileFormState = {
  success?: boolean;
  error?: string;
};

export async function updateProfile(
  _prevState: ProfileFormState,
  formData: FormData
): Promise<ProfileFormState> {
  const name = formData.get("name");

  if (typeof name !== "string" || !name.trim()) {
    return { error: "Name must not be blank" };
  }

  const trimmedName = name.trim();
  const requestHeaders = await headers();
  const session = await auth.api.getSession({ headers: requestHeaders });

  if (!session) {
    return { error: "You must be logged in to update your profile" };
  }

  const { token } = await auth.api.getToken({ headers: requestHeaders });

  const response = await fetch(`${backendUrl()}/me`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ name: trimmedName }),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const detail =
      errorBody && typeof errorBody.detail === "string"
        ? errorBody.detail
        : "Failed to update profile";
    return { error: detail };
  }

  try {
    await auth.api.updateUser({
      headers: requestHeaders,
      body: { name: trimmedName },
    });
  } catch {
    // Session sync failure is non-fatal if backend update succeeded
  }

  revalidatePath("/profile");
  revalidatePath("/animals");
  revalidatePath("/animals/mine");

  return { success: true };
}
