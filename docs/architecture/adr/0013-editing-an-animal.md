# ADR 0013: Editing an animal

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-11-02 |
| **Scope** | US-03 (edit my animal): AT-02 and AT-04 for editing, the edit half of AT-03 |
| **Related** | [0004-animal-aggregate](0004-animal-aggregate.md), [0006-application-services](0006-application-services.md), [0011-animal-match-profile](0011-animal-match-profile.md), [0012-owner-animals-and-unpublishing](0012-owner-animals-and-unpublishing.md) |

## Context

An owner needs to keep their animal's listing accurate. An edit follows the same
rules as publishing (AT-02), only the owner may make one (AT-04), and the change
shows wherever the animal appears (AT-03). The edit form must also load unpublished
animals, which the public `GET /animals/{id}` hides (ADR 0012).

## Decisions

1. **`Animal.edit(by_user_id, ...)` replaces the description**: every field that
   publishing sets. The id, owner and adoption status are not part of it, so an
   edit never republishes an animal. The owner can edit in any status and change
   the species; the team has yet to confirm both.
2. **Same rules as publishing, all or nothing.** `edit` builds the new state with
   `dataclasses.replace`, which runs the constructor's checks. A broken rule raises
   `InvalidAnimal` and leaves the animal unchanged.
3. **Ownership first.** `Animal.is_owned_by` decides it for editing, unpublishing
   and the owner's read. A non-owner gets 403, even if the edit also breaks a rule.
4. **`PUT /animals/{id}` takes the same body as `POST /animals`.** A field left out
   is cleared. PUT rather than PATCH: the form always sends everything, validation
   stays identical to publishing, and it matches `PUT /me/matchmaker-profile`.
   Unknown fields are a 422, so a typo cannot clear a field and `adoption_status`
   or `owner_id` cannot be sent. Wrong types and unknown fields are refused before
   the owner check, so those are a 422 even for a non-owner.
5. **`GET /me/animals/{id}` loads the edit form.** Owner only, unpublished
   included; 404 if the animal is missing or not the caller's.
6. **Edit and unpublish lock the row** (`AnimalRepository.get_for_update`,
   `SELECT ... FOR UPDATE OF a`). The repository writes the whole animal, so
   without the lock an edit could write back the old status and republish an
   animal, or an unpublish could undo an edit. Any other use case that updates an
   animal must load it with `get_for_update` too.

## Consequences

* **Positive:** one set of rules for publishing and editing; the match profile
  follows an edit (ADR 0011); no migration.
* **Negative:** two edits of the same animal (two tabs) are last write wins. A
  conditional request (`ETag`/`If-Match`) would fix it if needed.
* **Negative:** a client must send every field, or the ones left out are cleared.
* **Negative:** the description fields are listed in the domain, service and
  router, as for publishing.
