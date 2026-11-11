"use server";

import { revalidatePath } from "next/cache";

import { requestToAdopt } from "@/lib/adoption-api";
import { REQUEST_MESSAGES, type RequestOutcome } from "@/lib/adoption";
import { getFit } from "@/lib/compatibility-api";
import { isMode, type FitOutcome } from "@/lib/compatibility";

// A Server Action is a public endpoint, so the arguments are checked again here
// even though the card only sends valid ones. The backend checks them a third time.
export async function fitAction(
  animalId: unknown,
  mode: unknown,
): Promise<FitOutcome> {
  if (typeof animalId !== "string" || !isMode(mode)) {
    return {
      ok: false,
      problem: "unavailable",
      message: "The request was not valid, please try again.",
    };
  }
  return getFit(animalId, mode);
}

// Same rule as above: the arguments are checked again, and the backend is the judge.
export async function requestToAdoptAction(
  animalId: unknown,
  note: unknown,
): Promise<RequestOutcome> {
  if (typeof animalId !== "string" || typeof note !== "string") {
    return {
      ok: false,
      problem: "unavailable",
      message: REQUEST_MESSAGES.unavailable,
    };
  }
  const outcome = await requestToAdopt(animalId, note);
  if (outcome.ok) {
    // The page shows the new request instead of the form.
    revalidatePath(`/animals/${animalId}`);
  }
  return outcome;
}
