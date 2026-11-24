// The handover checklist shown to both sides of an accepted request (US-25,
// ADR 0028). The ticks are saved by the backend; the wording and the legal guidance
// are static, so they live here, like the guidelines (ADR 0027).

// The keys mirror HandoverItem (models/adoption/handover_item.py). The two lists are
// kept in step by hand: a test pins these four.
export const HANDOVER_ITEM_KEYS = [
  "vaccination_booklet",
  "microchip_transfer",
  "care_notes",
  "adoption_terms",
] as const;
export type HandoverItemKey = (typeof HANDOVER_ITEM_KEYS)[number];

// Where the advice comes from, so nobody reads a tip as if it were the law.
export type Basis = "law" | "practice" | "platform";

export type HandoverItem = {
  key: HandoverItemKey;
  title: string;
  basis: Basis;
  // What the law says. Only the items that rest on a legal rule have one.
  rule: string | null;
  steps: readonly string[];
};

export const BASIS_LABEL: Record<Basis, string> = {
  law: "The law",
  practice: "Good practice, not a legal rule",
  platform: "A Patas rule",
};

export const HANDOVER_DISCLAIMER =
  "Guidance, not legal advice. Checked on 24 November 2026.";

export const HANDOVER_CHECKLIST: readonly HandoverItem[] = [
  {
    key: "vaccination_booklet",
    title: "Hand over the vaccination record",
    basis: "law",
    rule: "Rabies vaccination is mandatory for dogs over 3 months and must be recorded in the health booklet or passport. For cats and other animals it is voluntary.",
    steps: [
      "Hand over the booklet or passport, or agree in the chat how to do it.",
      "Check the date of the last vaccines and when the next is due.",
      "The adopter books the next vaccine if it is due.",
    ],
  },
  {
    key: "microchip_transfer",
    title: "Transfer the animal in SIAC",
    basis: "law",
    rule: "Dogs, cats and ferrets must be microchipped and registered in SIAC. When the animal changes holder, the registered holder must report it within 15 days, with the consent of both people. This is the same for an adoption.",
    steps: [
      "Check that the microchip number in the documents is the animal's.",
      "Do it on the SIAC website, or with a vet, parish council or municipality. Both people need their ID and tax numbers.",
      "Do it in person or through the vet, not in the chat: Patas never shows contact details.",
      "Keep the confirmation.",
      "Not a dog, cat or ferret? This does not apply: tick it to skip.",
    ],
  },
  {
    key: "care_notes",
    title: "Share food, habits and routines",
    basis: "practice",
    rule: null,
    steps: [
      "Food and times, medication, fears, and behaviour with people and other animals.",
      "The vet who knows the animal.",
    ],
  },
  {
    key: "adoption_terms",
    title: "Confirm it is an adoption, not a sale",
    basis: "platform",
    rule: null,
    steps: [
      "Agree in the chat that nobody pays for the animal.",
      "Both confirm before the handover.",
    ],
  },
];

// AT-26: the checklist shows while the request is accepted, and after the adoption
// as it was left. A string, like canWithdraw: requests carry the status as text.
export function showsChecklist(status: string): boolean {
  return status === "accepted" || status === "adopted";
}

// Presentation only: the backend decides, and refuses a tick on anything else.
export function canTick(status: string): boolean {
  return status === "accepted";
}

// How many of the known items are ticked. A key the page does not know is ignored.
export function checkedCount(checked: readonly string[]): number {
  return HANDOVER_ITEM_KEYS.filter((key) => checked.includes(key)).length;
}
