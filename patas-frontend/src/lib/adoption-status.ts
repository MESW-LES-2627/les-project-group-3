// Values mirror the backend: AdoptionStatus (models/animal/enums.py) and
// ApplicationStatus (models/adoption/status.py). Labels are defined here, once.

export const ANIMAL_STATUS = [
  "available",
  "reserved",
  "adopted",
  "unavailable",
] as const;
export type AnimalStatus = (typeof ANIMAL_STATUS)[number];

export const ANIMAL_STATUS_LABEL: Record<AnimalStatus, string> = {
  available: "Available",
  reserved: "Reserved",
  adopted: "Adopted",
  // The owner's view: the animal left the catalog.
  unavailable: "Unpublished",
};

export const APPLICATION_STATUS = [
  "open",
  "accepted",
  "declined",
  "withdrawn",
  "closed",
  "adopted",
] as const;
export type ApplicationStatus = (typeof APPLICATION_STATUS)[number];

export const APPLICATION_STATUS_LABEL: Record<ApplicationStatus, string> = {
  open: "Open",
  accepted: "Accepted",
  declined: "Declined",
  withdrawn: "Withdrawn",
  closed: "Closed",
  adopted: "Adopted",
};

// A status the frontend does not know yet (a stale or newer backend) still shows
// as readable text instead of a blank badge.
function labelOf(labels: Record<string, string>, status: string): string {
  // hasOwn, not `in`: "constructor" must not match something inherited.
  if (Object.hasOwn(labels, status)) {
    return labels[status];
  }
  const words = status.replaceAll("_", " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

export function animalStatusLabel(status: string): string {
  return labelOf(ANIMAL_STATUS_LABEL, status);
}

export function applicationStatusLabel(status: string): string {
  return labelOf(APPLICATION_STATUS_LABEL, status);
}
