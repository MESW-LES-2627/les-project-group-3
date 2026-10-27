"use server";

import {
  deleteMatchmakerProfile,
  saveMatchmakerProfile,
} from "@/lib/matchmaker-api";
import {
  isMatchmakerAnswers,
  type DeleteOutcome,
  type SaveOutcome,
} from "@/lib/matchmaker-profile";

// A Server Action is a public endpoint, so the answers are checked again here even
// though the form only sends complete ones. The backend checks them a third time.
export async function saveProfileAction(
  answers: unknown,
): Promise<SaveOutcome> {
  if (!isMatchmakerAnswers(answers)) {
    return { ok: false, error: "Please answer every question before saving." };
  }
  return saveMatchmakerProfile(answers);
}

export async function deleteProfileAction(): Promise<DeleteOutcome> {
  return deleteMatchmakerProfile();
}
