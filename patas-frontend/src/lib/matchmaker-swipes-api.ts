// Server-side only: browsing and swipe history use the signed-in user's token.
import { backendUrl } from "@/lib/backend";
import { bearerToken } from "@/lib/matchmaker-api";
import {
  isSwipeAnimal,
  isSwipeDisposition,
  SWIPE_MESSAGES,
  type SavedAnimalsOutcome,
  type SwipeAnimal,
  type SwipeDisposition,
  type SwipeFeedOutcome,
  type SwipeOutcome,
  type SwipeFailure,
} from "@/lib/matchmaker-swipes";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function failure(problem: SwipeFailure): SwipeOutcome {
  return { ok: false, problem, message: SWIPE_MESSAGES[problem] };
}

async function problemFor(response: Response): Promise<SwipeFailure> {
  if (response.status === 404) {
    return "not-found";
  }
  if (response.status !== 409) {
    return "unavailable";
  }
  try {
    const { detail } = (await response.json()) as {
      detail?: { code?: unknown };
    };
    if (detail?.code === "already_swiped") return "already-swiped";
    if (detail?.code === "animal_not_available") return "not-available";
    if (detail?.code === "matchmaker_profile_required") return "no-profile";
  } catch {
    return "unavailable";
  }
  return "unavailable";
}

function isAnimalList(value: unknown): value is SwipeAnimal[] {
  return Array.isArray(value) && value.every(isSwipeAnimal);
}

export async function getSwipeFeed(): Promise<SwipeFeedOutcome> {
  const token = await bearerToken();
  try {
    const response = await fetch(
      `${backendUrl()}/me/matchmaker/swipes/feed`,
      { cache: "no-store", headers: { Authorization: `Bearer ${token}` } },
    );
    if (response.status === 409) {
      return {
        ok: false,
        problem: "no-profile",
        message: SWIPE_MESSAGES["no-profile"],
      };
    }
    if (!response.ok) {
      return {
        ok: false,
        problem: "unavailable",
        message: SWIPE_MESSAGES.unavailable,
      };
    }
    const payload: unknown = await response.json();
    return isAnimalList(payload)
      ? { ok: true, animals: payload }
      : {
          ok: false,
          problem: "unavailable",
          message: SWIPE_MESSAGES.unavailable,
        };
  } catch {
    return {
      ok: false,
      problem: "unavailable",
      message: SWIPE_MESSAGES.unavailable,
    };
  }
}

export async function getSavedAnimals(): Promise<SavedAnimalsOutcome> {
  const token = await bearerToken();
  try {
    const response = await fetch(
      `${backendUrl()}/me/matchmaker/swipes/saved`,
      { cache: "no-store", headers: { Authorization: `Bearer ${token}` } },
    );
    if (!response.ok) {
      return {
        ok: false,
        problem: "unavailable",
        message: SWIPE_MESSAGES.unavailable,
      };
    }
    const payload: unknown = await response.json();
    return isAnimalList(payload)
      ? { ok: true, animals: payload }
      : {
          ok: false,
          problem: "unavailable",
          message: SWIPE_MESSAGES.unavailable,
        };
  } catch {
    return {
      ok: false,
      problem: "unavailable",
      message: SWIPE_MESSAGES.unavailable,
    };
  }
}

export async function recordSwipe(
  animalId: string,
  disposition: SwipeDisposition,
): Promise<SwipeOutcome> {
  if (!UUID_PATTERN.test(animalId) || !isSwipeDisposition(disposition)) {
    return failure("not-found");
  }
  const token = await bearerToken();
  try {
    const response = await fetch(`${backendUrl()}/me/matchmaker/swipes`, {
      method: "POST",
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ animal_id: animalId, disposition }),
    });
    if (!response.ok) {
      return failure(await problemFor(response));
    }
    return { ok: true };
  } catch {
    return failure("unavailable");
  }
}

export async function removeSavedAnimal(animalId: string): Promise<SwipeOutcome> {
  if (!UUID_PATTERN.test(animalId)) {
    return failure("not-found");
  }
  const token = await bearerToken();
  try {
    const response = await fetch(
      `${backendUrl()}/me/matchmaker/swipes/${encodeURIComponent(animalId)}`,
      {
        method: "DELETE",
        cache: "no-store",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    return response.ok ? { ok: true } : failure(await problemFor(response));
  } catch {
    return failure("unavailable");
  }
}
