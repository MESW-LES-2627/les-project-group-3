// What a confirmation dialog asks; the wording lives here so it is tested.
export type Confirmation = { title: string; message?: string };

export function unpublishConfirmation(animalName: string): Confirmation {
  return {
    title: `Unpublish ${animalName}?`,
    message: `${animalName} will no longer appear in the catalog. You can republish later.`,
  };
}
