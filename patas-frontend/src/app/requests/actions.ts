"use server";

import { revalidatePath } from "next/cache";

import { withdrawRequest } from "@/lib/adoption-api";
import { WITHDRAW_MESSAGES, type WithdrawOutcome } from "@/lib/adoption";

// A Server Action is a public endpoint: the arguments are checked again here, and the
// backend is the judge.
export async function withdrawRequestAction(
  applicationId: unknown,
  animalId: unknown,
): Promise<WithdrawOutcome> {
  if (typeof applicationId !== "string" || typeof animalId !== "string") {
    return {
      ok: false,
      problem: "unavailable",
      message: WITHDRAW_MESSAGES.unavailable,
    };
  }
  const outcome = await withdrawRequest(applicationId);
  // Refresh unless the backend could not be reached: after a 404 or a 409 the page
  // was showing something stale, so it should show what is true now.
  if (outcome.ok || outcome.problem !== "unavailable") {
    revalidatePath("/requests");
    revalidatePath(`/animals/${animalId}`);
  }
  return outcome;
}
