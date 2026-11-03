# ADR 0015: Public animal profile page

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-11-03 |
| **Scope** | Visitor animal profile and publisher display name; AT-01, AT-03, AT-05 and AT-09 |
| **Related** | [0004-animal-aggregate](0004-animal-aggregate.md), [0010-animal-profile-fields](0010-animal-profile-fields.md), [0012-owner-animals-and-unpublishing](0012-owner-animals-and-unpublishing.md), [0014-editing-an-animal](0014-editing-an-animal.md) |

## Context

A visitor needs to open an animal from the public catalog and see enough
information to decide whether it may be a good fit. This includes the complete
description supplied by its owner and the owner's current display name. Changes
to an animal or its owner's name must be reflected on the public profile, and
unpublished animals must not remain accessible there.

## Decisions

1. **The existing public detail endpoint is the source of truth.**
   `/animals/{id}` returns the existing `AnimalResponse`, including every
   description field and `owner_name`. The frontend does not maintain a second
   profile store or introduce a new endpoint or database schema.
2. **The profile page fetches current data without caching.**
   The server-rendered `/animals/[id]` page uses `cache: "no-store"` so edits
   and owner-name changes are visible on the next request. If the endpoint
   returns 404 for a missing or unpublished animal, the page renders the
   framework's not-found route.
3. **The owner name is resolved from the current user record.**
   The animal repository joins `patas.users` when it loads a public detail, so
   the response reflects changes to the owner's display name instead of a
   snapshot copied onto the animal.
4. **The page presents the full description in groups.**
   It shows identity and publisher information, then the profile fields under
   About, Daily care and Compatibility, followed by Special care and Other
   details. Null optional values are explicitly shown as “Not provided”;
   enum values replace underscores with spaces and are capitalized for
   display. Free-text notes preserve their line breaks.
5. **Existing write and catalog behavior remains unchanged.**
   Publishing and editing continue to use the animal description contract
   (AT-01 and AT-03); public catalog filtering continues to use the existing
   catalog endpoint; unpublishing continues to make public detail unavailable
   (AT-05). The public profile displays the `owner_name` supplied by that API
   (AT-09).

## Consequences

* **Positive:** one API response drives the catalog and public detail, so
  edits and current owner names are consistent without duplicated state.
* **Positive:** visitors can distinguish unanswered optional fields from
  missing page content.
* **Negative:** adding a description field requires coordinated updates to the
  API response type and the profile page.
* **Negative:** the display labels and enum formatting are maintained in the
  frontend rather than generated from the backend schema.
* **Out of scope:** matching scores, new filters, contact workflows and
  changes to the owner's animal-management page.
