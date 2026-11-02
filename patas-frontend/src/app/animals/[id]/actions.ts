"use server";

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
