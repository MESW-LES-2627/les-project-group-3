# ADR 0011: The animal match profile and its translation to the Matchmaker scales

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-10-28 |
| **Scope** | US-07 (describe how my animal lives with others); the link between an animal and a Matchmaker profile |
| **Related** | [0008-matchmaker-profile](0008-matchmaker-profile.md), [0010-animal-profile-fields](0010-animal-profile-fields.md), [MatchingAlgorithms](../../research/MatchingAlgorithms.md) |

## Context

The Matchmaker profile (ADR 0008) holds an adopter's answers on shared scales.
The animal's profile fields (ADR 0010) were written in the owner's vocabulary:
four-state yes/no/with supervision/unknown answers, a first-time-owner question,
a tolerance for time alone, and a space requirement. The two sides ask about the
same things in different words, so scoring (iteration 2) cannot compare them
as they are. US-07 asks that an owner can say whether the animal is good with
children, dogs and cats, its energy, the space it needs and the experience it
needs. Most of that already exists as columns from US-01. What is missing is
the common vocabulary.

## Decisions

1. **No new column.** The animal keeps the owner's vocabulary as stored by
   ADR 0010, and its data is untouched. A separate `needs_yard` column was
   considered and dropped: the existing `space_requirement` is paired with the
   adopter's housing instead (decision 5).
2. **The match profile is derived, not stored.** `AnimalMatchProfile` is a frozen
   value object in `models/animal/match_profile.py`. `Animal.match_profile()`
   builds a new one on each call. Nothing is cached or persisted, so it cannot
   disagree with the animal and it follows later edits (US-03).
3. **Every adopter answer has a counterpart on the animal.** Both sides use the
   same type where one exists, so a comparison never needs a second translation.

   | Adopter (`MatchmakerProfile`) | Animal (`AnimalMatchProfile`) | Rule |
   | :-- | :-- | :-- |
   | `activity` | `activity` | The same scale, carried over. |
   | `time_away` | `max_time_alone` | Tolerance low, moderate, high becomes few hours, half a day, most of the day. Scoring reads it as a ceiling. |
   | `experience` | `experience_needed` | First-time owners yes becomes none, with support becomes some, no becomes experienced. |
   | `housing` (as `space_offered`) | `space_needed` | The animal's `space_requirement`, carried over. |
   | `has_children` | `safe_with_children` | Yes is true, no is false, anything else is not settled. |
   | `has_dogs` | `safe_with_dogs` | As above. |
   | `has_cats` | `safe_with_cats` | As above. |

4. **A blank or unsettled answer is `None`, never "no".** "Unknown" and "with
   supervision" both become `None`: a family with children is not excluded by
   them, and an unanswered question is never read as a refusal. A test fixes this
   for an animal with no answers at all.
5. **Housing is translated to space on the adopter's side.**
   `MatchmakerProfile.space_offered` is a derived property: an apartment gives
   small, a house without a yard medium, a house with a yard large. It is on the
   same small, medium, large scale as `space_needed`, so scoring compares a
   distance. It is not stored and not in the adopter's API response.
6. **Size is an animal-only modifier.** `size` is exposed as given. It has no
   adopter answer to pair with, and it is never used to fill in a blank
   `space_needed`. How much it weighs is a scoring decision (iteration 2).
7. **The translation tables are exhaustive.** Every value of each source enum is
   listed, including the ones that map to `None`, and a missing value raises a
   `KeyError`. A new enum member without a decision therefore fails the tests
   before it reaches a user. A contract test fails if an adopter question has no
   animal counterpart, or if an animal-side value other than `size` is left
   unpaired.
8. **The API carries it on the existing endpoints.** `POST /animals` and
   `GET /animals` return a read-only `match_profile` object next to the existing
   fields. It is always present, with `null` inside when nothing is known. There
   is no new endpoint, and the request model has no counterpart, so a client
   cannot send it.
9. **Two pure moves made this possible.** `TimeAway` moved from the profile
   package to `models/matching` because the animal side now uses it, which
   supersedes the part of ADR 0008 decision 3 saying it is profile-only. The
   animal enums moved from `animal.py` to `enums.py` so `match_profile.py` can
   depend on them without an import cycle. Names, values and database types are
   unchanged.

## Consequences

* **Positive:** no migration and no change to data that ADR 0010 already
  stored. Scoring will receive two comparable domain objects, which suits the
  Strategy pattern. A rule changes in one file, not in a migration.
* **Positive:** the frontend and the three stories that read animals (US-02,
  US-03, US-06) keep working: the response only gains a field.
* **Negative:** the translation loses information. "With supervision" and
  "unknown" both become `None`, so a "reasons" text that wants to say "with
  supervision" must read the animal's own field.
* **Negative:** four rules are assumptions awaiting the team's agreement:
  "with supervision" as not settled, the tolerance to time-alone buckets, the
  first-time-owner answer to experience, and housing to space. In particular,
  housing to space is coarse: a large apartment or a small house with a good
  garden does not fit it, and a hard "needs a yard" filter cannot be expressed.
  If the team wants that filter, a nullable `needs_yard` column can be added
  later without touching anything here.
* **Negative:** nothing in iteration 1 consumes the profile except the API
  response and the tests. It earns its place when scoring arrives.
* **Negative:** `behaves_well_with_other_animals`, shedding, grooming, training
  and noise have no adopter counterpart, so they stay descriptive and for
  catalog filters only.
* **Out of scope:** scoring and its weights, hard filters, the visitor quiz,
  and any screen that shows the match profile.
