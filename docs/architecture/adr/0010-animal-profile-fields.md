# ADR 0010: Animal profile fields for matching and care

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-10-27 |
| **Scope** | Animal registration and the optional animal profile fields in `temp.md` |
| **Related** | [0004-animal-aggregate](0004-animal-aggregate.md), [0008-matchmaker-profile](0008-matchmaker-profile.md), [0009-matchmaker-profile-page](0009-matchmaker-profile-page.md) |

## Context

The Matchmaker profile captures household answers, but animal listings need
compatible information before future matching can compare both sides. The
requested registration details describe an animal's needs, temperament,
compatibility and care. A listing must still be publishable when the publisher
does not know any of these details.

## Decisions

1. **The profile details are columns on `patas.animals`.** They describe the
   animal itself and are read and written as part of the existing `Animal`
   aggregate, not stored in a second profile or a JSON document. Migration
   `0005` adds these columns to the existing table.
2. **All newly added fields are nullable.** The animal's existing required
   `name` and `species` invariants are unchanged; `age_in_months` already exists
   and remains nullable. Missing profile answers are represented by SQL `NULL`.
   An explicit `unknown` is kept distinct where the form offers it: it means the
   publisher answered that the value is unknown.
3. **Finite choices use PostgreSQL enums.** Sex, neuter status, size,
   compatibility and first-time-owner suitability each use a native enum. The
   three-level activity scale reuses `patas.energy_level` from migration `0004`
   for activity, shedding, grooming, training, time alone and noise.
4. **Postal codes use Portuguese formatting.** A provided postal code must have
   the form `NNNN-NNN`; omitting it is valid. Optional free-text values are
   trimmed and blank values are stored as `NULL`.
5. **The existing animal endpoints carry the profile.** `POST /animals` accepts
   the new optional values, and `GET /animals` returns them alongside the
   existing listing details. Database persistence continues to use hand-written
   SQL and explicit domain mapping.
6. **Registration uses the Matchmaker form layout.** The publish form follows
   its two-column, sectioned layout and card-based choices. Name and species
   remain required; profile questions can be skipped. A completion indicator
   describes how many optional details have been entered, without suggesting
   that a complete profile is required to publish.

## Consequences

* **Positive:** listings can be published with partial or no matching details,
  while known values remain queryable and constrained to the agreed choices.
* **Positive:** animal compatibility and care data follows the same domain,
  persistence and API path as the listing rather than becoming disconnected
  profile data.
* **Negative:** adding or changing a finite choice requires a coordinated
  migration and domain/API update.
* **Negative:** the enum vocabulary is mirrored in the frontend and backend;
  the current project has no generated shared schema to prevent drift.
* **Out of scope:** matching scores, hard filters, catalog filters and editing
  an already-published animal.
