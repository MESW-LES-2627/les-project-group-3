// The suggested steps shown to both sides of an accepted request (US-24).
// Static and the same for owner and adopter, so they live here, not in the
// backend (ADR 0027).
export type GuidelineStep = { title: string; points: readonly string[] };

export const ADOPTION_GUIDELINES: readonly GuidelineStep[] = [
  {
    title: "Get to know the animal",
    points: [
      "Ask about health: vaccines, deworming, known conditions and the last vet visit.",
      "Ask about temperament and routine: food, walks or litter, where it sleeps.",
      "Ask why the animal is being rehomed.",
    ],
  },
  {
    title: "Get to know the new home",
    points: [
      "Ask for photos of the house and garden.",
      "Ask who lives there and whether everyone agrees with the adoption.",
      "Ask about landlord or condominium rules and who looks after the animal during holidays.",
    ],
  },
  {
    title: "Meet safely",
    points: [
      "Meet first in a public place and bring someone with you.",
      "See the animal in person before agreeing to anything.",
    ],
  },
  {
    title: "Adoption is not a sale",
    points: [
      "No one pays for the animal: never pay a deposit, reservation or transport fee.",
      "Keep the conversation in Patas and be wary of anyone who asks for money.",
    ],
  },
  {
    title: "Plan the handover",
    points: [
      "Agree on where and when the animal changes home.",
      "Once the animal is in its new home, both of you confirm the handover here.",
    ],
  },
];

// AT-26: the guidelines show while the request is accepted, not before or after.
// A string, like canWithdraw: requests from the API carry the status as text.
export function showsGuidelines(status: string): boolean {
  return status === "accepted";
}
