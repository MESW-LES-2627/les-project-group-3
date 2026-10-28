# ADR 0012: Owner's animal list and unpublishing

| | |
| :-- | :-- |
| **Status** | Accepted |
| **Date** | 2026-10-28 |
| **Scope** | US-04 (owner page with all animals, unpublished included), US-05 (unpublish) |
| **Related** | [0004-animal-aggregate](0004-animal-aggregate.md), [0006-application-services](0006-application-services.md), [AdoptionPipeline](../../domain/AdoptionPipeline.md) |

## Context

An animal owner needs a dashboard to view all the animals they have published,
including unpublished listings, and the ability to unpublish animals so they are
removed from the public adoption catalog while retaining their records and history.
Unpublishing must be strictly authorized: only the animal's owner can unpublish it.
When unpublished, an animal must not be visible in the public catalog or accessible
to visitors on its public detail page, but must remain visible to its owner under "My animals"
marked as unpublished.

## Decisions

1. **Unpublishing maps directly to `AdoptionStatus.UNAVAILABLE`.**
   The existing `patas.adoption_status` database enum and domain enum already have
   `unavailable` (defined in migration `0003` and ADR 0004, matching the adoption pipeline).
   Using `unavailable` represents the unpublished state without requiring a separate
   boolean column or duplicate status tracking. An animal is published if and only if
   `adoption_status != AdoptionStatus.UNAVAILABLE`.
2. **Domain method encapsulates authorization and invariant.**
   `Animal.unpublish(by_user_id: UUID)` verifies `self.owner_id == by_user_id`.
   If the caller is not the owner, `AnimalUnauthorized` is raised (mapped to HTTP 403
   in the router).
3. **Repository updates and queries:**
   - `AnimalRepository.list_all()` filters out unpublished listings (`WHERE adoption_status != 'unavailable'`),
     ensuring the public catalog never displays unpublished animals.
   - `AnimalRepository.list_by_owner(owner_id: UUID)` selects all animals for the given owner
     (`WHERE owner_id = :owner_id`), including unpublished ones, ordered newest first.
   - `AnimalRepository.get_by_id(id: UUID)` fetches by id, and `update(animal: Animal)` persists
     state changes.
4. **Endpoint contracts:**
   - `GET /me/animals`: requires user authentication, returns all animals owned by the current user.
   - `POST /animals/{id}/unpublish`: requires user authentication, checks ownership (403 if not owner),
     and transitions status to `unavailable`.
   - `GET /animals/{id}`: public endpoint returning 404 if the animal does not exist or is unpublished.
5. **Frontend route and controls:**
   - `/animals/mine` displays the authenticated user's animal list with published and unpublished badges.
   - Unpublish button triggers a Next.js Server Action (`unpublishAnimalAction`) that calls
     `POST /animals/{id}/unpublish` and revalidates cache paths.
   - Navigation in `SiteHeader` adds a link to "My animals" for authenticated users.

## Consequences

* **Positive:** Zero database migration required; fully backward-compatible with existing schema.
* **Positive:** Strict encapsulation: business rules and ownership checks reside within the domain aggregate.
* **Positive:** Public catalog and detail pages automatically hide unpublished animals.
* **Negative:** If a future requirement distinguishes between "temporarily paused / unpublished" and other
  unavailable states (e.g. administrative suspension), a dedicated column or sub-state may be needed.
