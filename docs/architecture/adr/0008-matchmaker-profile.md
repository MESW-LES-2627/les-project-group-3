# ADR 0008: Matchmaker profile and the shared matching scales

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-10-25 |
| **Scope** | US-08 (save my Matchmaker profile); the scales shared with US-07 |
| **Related** | [0001-authentication](0001-authentication.md) §7, [0004-animal-aggregate](0004-animal-aggregate.md), [0006-application-services](0006-application-services.md), [MatchingAlgorithms](../../research/MatchingAlgorithms.md), [Glossary](../../domain/Glossary.md) |

## Context

A registered user saves their home and lifestyle once, so the platform can later
suggest animals without asking again ([MVP](../../product/MVP.md)). Scoring is a
later iteration, but it will compare this profile with the animal's own description
(US-07) on the same dimensions, so the two must share their vocabulary now. The
archived `matchmaker_profiles` sketch has no household answers, and the research
document says the safety filters need them.

## Decisions

1. **The profile is its own aggregate, one per user.** It is identified by the
   user id and refers to `User` by id only. It is not columns on `users` (that would
   couple it to identity and to US-09) and not a JSON blob (the database could not
   reject an invalid value).
2. **Every answer is required.** There is no partial profile and no default for the
   household answers: a missing "has cats" must never be read as "no cats".
3. **Energy and experience are shared three-level scales.** `EnergyLevel` (low,
   moderate, high) and `ExperienceLevel` (none, some, experienced) live in
   `models/matching` and are used by the profile and, in US-07, by the animal. Each
   is declared from lowest to highest, so scoring can use the distance later. Their
   database types are named after the scale (`patas.energy_level`,
   `patas.experience_level`), not after the profile, and are created by migration
   `0004`; US-07 reuses them. `HousingType` and `TimeAway` belong to the profile only.
4. **Integrity lives in the table.** `user_id` is the primary key, so a second
   profile cannot exist. It references `users` with `ON DELETE CASCADE`: the profile
   is personal data and leaves with the account (animals use `RESTRICT` because
   others depend on a listing). Columns are `NOT NULL` with no default, enums are
   native, and `updated_at` is kept by the existing trigger. There is no `created_at`.
5. **Saving is one atomic upsert** (`INSERT ... ON CONFLICT (user_id) DO UPDATE`),
   so two saves at once cannot create two rows. It follows ADR 0001 §7: hand-written
   SQL, explicit row mapping, the caller owns the transaction.
6. **Validation has three layers.** The request model checks types (`StrictBool`,
   so `"yes"` is not a yes). The domain constructor checks the enums and real
   booleans, however the object is built. The database enforces enums and `NOT NULL`.
   No domain error is mapped to HTTP yet: the request types equal the domain values,
   so the branch is unreachable. The mapping is added with the first rule that only
   the domain knows.
7. **`MatchmakerProfileService` has `get`, `save` and `delete`** (ADR 0006). `save`
   builds the profile before the transaction opens; `get` returns nothing when there
   is no profile.
8. **The API is `/me/matchmaker-profile`, with no user id in the URL.** The profile
   is always the caller's own, so privacy comes from the shape of the URL.
   `GET` returns 200, or 404 when nothing is saved; `PUT` replaces all answers and
   returns 200; `DELETE` returns 204 and is idempotent; no token is 401; an invalid
   body is 422. The response is the seven answers only.
9. **A user can delete their own profile.** This goes beyond the story text. It lets
   a user remove their own data and start over. It is one separate commit and can be
   reverted alone.

Out of scope: scoring, hard filters and the visitor quiz (iteration 2), the
animal-side fields (US-07), and where the form lives in the interface (US-09).

## Consequences

* **Positive:** one profile per user is a database guarantee, and a user cannot
  reach another user's profile by changing a URL.
* **Positive:** animal and profile energy and experience can be compared directly.
  A test compares each Postgres enum with its Python enum, so the two cannot drift.
* **Negative:** native enums need a `CAST` and `ALTER TYPE ... ADD VALUE` to grow.
  Moving from three levels to five is a data migration.
* **Negative:** the domain object has little behaviour until scoring arrives.
* **Negative:** `time_away` has no counterpart on the animal. Scoring derives it
  from the animal's energy (research §3B). A field for tolerance of being alone
  would need a new decision.
* **Negative:** US-07 and US-08 are coupled through the shared enum types, so the
  migration order matters (US-08 creates them, US-07 reuses them).
* **Negative:** a client must treat a 404 on `GET` as "no profile yet". There is no
  soft delete or history of past answers.
