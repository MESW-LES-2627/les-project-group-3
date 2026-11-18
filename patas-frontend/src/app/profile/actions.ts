"use server";

import { revalidatePath } from "next/cache";
import { headers } from "next/headers";

import { auth } from "@/lib/auth";
import { parseUsername } from "@/lib/username";
import { updateMe } from "@/lib/username-api";

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
  const username = parseUsername(formData.get("username"));
  if (!username.ok) {
    return { error: username.error };
  }

  const trimmedName = name.trim();
  const outcome = await updateMe({
    name: trimmedName,
    username: username.username,
  });
  if (!outcome.ok) {
    return { error: outcome.error };
  }

  try {
    await auth.api.updateUser({
      headers: await headers(),
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
