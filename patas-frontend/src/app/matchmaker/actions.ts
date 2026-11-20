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
import {
  getSavedAnimals,
  getSwipeFeed,
  recordSwipe,
  removeSavedAnimal,
} from "@/lib/matchmaker-swipes-api";
import {
  isSwipeDisposition,
  SWIPE_MESSAGES,
  type SavedAnimalsOutcome,
  type SwipeFeedOutcome,
  type SwipeOutcome,
} from "@/lib/matchmaker-swipes";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

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

export async function swipeFeedAction(): Promise<SwipeFeedOutcome> {
  return getSwipeFeed();
}

export async function savedAnimalsAction(): Promise<SavedAnimalsOutcome> {
  return getSavedAnimals();
}

export async function recordSwipeAction(
  animalId: unknown,
  disposition: unknown,
): Promise<SwipeOutcome> {
  if (
    typeof animalId !== "string" ||
    !UUID_PATTERN.test(animalId) ||
    !isSwipeDisposition(disposition)
  ) {
    return {
      ok: false,
      problem: "not-found",
      message: SWIPE_MESSAGES["not-found"],
    };
  }
  return recordSwipe(animalId, disposition);
}

export async function removeSavedAnimalAction(
  animalId: unknown,
): Promise<SwipeOutcome> {
  if (typeof animalId !== "string" || !UUID_PATTERN.test(animalId)) {
    return {
      ok: false,
      problem: "not-found",
      message: SWIPE_MESSAGES["not-found"],
    };
  }
  return removeSavedAnimal(animalId);
}
