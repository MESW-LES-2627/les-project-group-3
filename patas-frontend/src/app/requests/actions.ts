"use server";

import { revalidatePath } from "next/cache";

import {
  answerRequest,
  confirmHandover,
  setHandoverItem,
  withdrawRequest,
} from "@/lib/adoption-api";
import {
  ANSWER_MESSAGES,
  CONFIRM_HANDOVER_MESSAGES,
  TICK_MESSAGES,
  WITHDRAW_MESSAGES,
  type AnswerOutcome,
  type ConfirmHandoverOutcome,
  type TickOutcome,
  type WithdrawOutcome,
} from "@/lib/adoption";
import { HANDOVER_ITEM_KEYS } from "@/lib/handover-checklist";

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

// The owner's answer to a request. Like the one above, it is a public endpoint: the
// arguments are checked again here, and the backend is the judge.
export async function answerRequestAction(
  applicationId: unknown,
  animalId: unknown,
  answer: unknown,
  note: unknown,
): Promise<AnswerOutcome> {
  if (
    typeof applicationId !== "string" ||
    typeof animalId !== "string" ||
    (answer !== "accept" && answer !== "decline") ||
    typeof note !== "string"
  ) {
    return {
      ok: false,
      problem: "unavailable",
      message: ANSWER_MESSAGES.unavailable,
    };
  }
  const outcome = await answerRequest(applicationId, answer, note);
  // Refresh unless the backend could not be reached: after a 404 or a 409 the page
  // was showing something stale, so it should show what is true now.
  if (outcome.ok || outcome.problem !== "unavailable") {
    revalidatePath("/requests");
    revalidatePath(`/animals/${animalId}`);
  }
  return outcome;
}

// US-18: the owner or applicant confirms the handover. The second confirmation
// adopts the animal, so the catalog is refreshed as well as the animal page.
export async function confirmHandoverAction(
  applicationId: unknown,
  animalId: unknown,
): Promise<ConfirmHandoverOutcome> {
  if (typeof applicationId !== "string" || typeof animalId !== "string") {
    return {
      ok: false,
      problem: "unavailable",
      message: CONFIRM_HANDOVER_MESSAGES.unavailable,
    };
  }
  const outcome = await confirmHandover(applicationId);
  // Refresh unless the backend could not be reached: after a 404 or a 409 the page
  // was showing something stale, so it should show what is true now.
  if (outcome.ok || outcome.problem !== "unavailable") {
    revalidatePath("/requests");
    revalidatePath(`/animals/${animalId}`);
    revalidatePath("/animals");
  }
  return outcome;
}

// US-25: either side ticks or unticks a handover checklist item. A public endpoint
// like the others: the item is checked against the known keys, and the backend is
// the judge of who may tick and when.
export async function setHandoverItemAction(
  applicationId: unknown,
  item: unknown,
  checked: unknown,
): Promise<TickOutcome> {
  if (
    typeof applicationId !== "string" ||
    typeof item !== "string" ||
    !(HANDOVER_ITEM_KEYS as readonly string[]).includes(item) ||
    typeof checked !== "boolean"
  ) {
    return {
      ok: false,
      problem: "unavailable",
      message: TICK_MESSAGES.unavailable,
    };
  }
  const outcome = await setHandoverItem(applicationId, item, checked);
  // Refresh unless the backend could not be reached: after a 404 or a 409 the page
  // was showing something stale, so it should show what is true now.
  if (outcome.ok || outcome.problem !== "unavailable") {
    revalidatePath(`/requests/${applicationId}`);
  }
  return outcome;
}
