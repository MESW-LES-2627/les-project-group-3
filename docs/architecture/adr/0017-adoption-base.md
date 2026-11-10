# ADR 0017: Adoption base

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-11-07 |
| **Scope** | Adoption base task (#57); AT-21 (#75) for unpublishing |
| **Related** | [0004-animal-aggregate](0004-animal-aggregate.md) (this replaces the five status values of its decision 2), [0006-application-services](0006-application-services.md), [0012-owner-animals-and-unpublishing](0012-owner-animals-and-unpublishing.md), [0014-editing-an-animal](0014-editing-an-animal.md), [AdoptionPipeline](../../domain/AdoptionPipeline.md) |

## Context

Six stories (request, received list, accept or decline, my requests and withdraw,
confirm the handover, republish) are worked in parallel by different people. They need
one foundation: the application record and its states, how an application and an
animal change together, and demo data in every state.

## Decisions

1. **The application is its own aggregate** (`AdoptionApplication`, `models/adoption/`),
   separate from `Animal`. It stores the animal, the owner (copied from the animal
   when the request is made, and never changed), the applicant, the applicant's note,
   the owner's optional reply, and a time for each side's handover confirmation. It is
   created with `request(...)` and loaded through the constructor, like `Animal`.
2. **State pattern, six statuses.** From *open* an application can be accepted,
   declined, withdrawn or closed. From *accepted* it can be declined, withdrawn or
   adopted. *Declined*, *withdrawn*, *closed* and *adopted* are final. Who may act is
   checked in the aggregate before the status: only the owner accepts or declines,
   only the applicant withdraws, either side confirms, and the system closes.
   **The trial is deferred, not rejected.** Adding it later is one state class plus
   `ALTER TYPE ... ADD VALUE`. `in_trial` left the animal's status, and migration
   `0007` turns any existing `in_trial` row into `reserved`.
3. **Handover:** each side confirms once, and the second confirmation adopts. A
   confirmation stays on the row if the request is later declined or withdrawn.
4. **Matchmaker snapshot.** The applicant's seven answers are copied onto the request
   as `jsonb` (`ProfileSnapshot`), so the owner sees what was declared when asking,
   even if the applicant later edits or deletes their profile. Deleting the applicant
   deletes their requests (`CASCADE`); the animal and the owner are `RESTRICT`.
   Deleting an account is therefore its own use case: it must first withdraw the
   user's active requests, so that an accepted one releases its animal through the
   normal handler. Otherwise the animal would stay reserved with no request.
5. **The database enforces the rules too.** One active (open or accepted) request per
   applicant and animal; at most one accepted request per animal; the applicant is not
   the owner; adopted needs both confirmations. `update` writes only the status, the
   owner's note and the confirmations.
6. **Animal transitions.** `reserve` (available to reserved), `release` (reserved to
   available) and `mark_adopted` (reserved to adopted), each refused from any other
   status with `InvalidAnimalTransition`, which the router returns as 409.
   `unpublish` works only from available (twice is a no-op), so a reserved or adopted
   animal cannot be hidden, and unpublishing closes the animal's open requests.
7. **Domain events, in two phases.** Aggregates record events (`pull_events`). A use
   case **dispatches inside its transaction**: handlers keep the data consistent
   (reserve, release, adopt, close) and a failure rolls everything back. It then
   **publishes after the commit**: handlers announce what happened (chat, email,
   notifications), get no session, and a failure is logged and never raised. Handlers
   match by class hierarchy, and the dispatcher is built in `create_app`, so a new
   feature registers its handlers there without touching adoption code. A handler
   persists what it changes and returns the events of what it changed. Publishing is
   best effort: a lost announcement is acceptable because the database is the truth
   and clients refetch.
8. **Lock order: the animal first, then its applications, always.**
   `lock_animal_and_application` is the one way to lock an application, and unpublish
   locks in the same order, so the two cannot deadlock. It locks the animal but
   returns only the application: a handler loads and saves its own copy of the animal,
   so an animal kept by the use case and saved afterwards would silently revert the
   handler's change. A use case that creates a
   request (US-14) **must lock the animal before checking that it is available**, or a
   request could slip in beside an unpublish and stay open on an unpublished animal.
9. **Status labels.** Values are backend enums; labels live in one frontend module
   (`lib/adoption-status.ts`). The two lists of values are kept in step by hand: the
   `Record` type catches a missing label, not an extra value.
10. **Demo data and tests.** `scripts/seed_applications.py` adds one request per status.
    It builds rows directly in their final status and **bypasses the transitions on
    purpose**: some states cannot be reached through the application until later
    stories land. Tests start from `tests/adoption/adoption_factory.py`.

## Pending team agreement

`AGENTS.md` section 6 asks for business rules to be agreed with the team before they
are implemented. The code already follows these proposals. They are also listed as
D2 and D8 to D11 in [AdoptionPipeline](../../domain/AdoptionPipeline.md) section 10.

* **Chat opens when a request is accepted.** The owner accepts one applicant, talks to
  them, then confirms the handover or declines. The pipeline document used to open the
  chat at the request.
* **Unpublish is refused while an animal is reserved or adopted.** Today it works from
  any status.
* **The handover rule:** each side confirms once and the second confirmation adopts.
  Open question: should a confirmation block a later decline or withdrawal?
* **An accepted request cannot be closed by the system**, a consequence of the
  unpublish rule above.
* **The trial is deferred** for iteration 2.
* **Is the applicant's note required?** The aggregate does not validate it today, so it
  can be blank. US-14 owns the rule and should put it in the domain, not the router.

## Consequences

* (+) Each story starts from a seeded state and adds only its use case, endpoint and
  screen. The rules live in the domain and the database.
* (+) A new reaction (chat, notifications) is a new handler, with no change to the
  adoption code.
* (−) Events add a layer: to learn what happens when a request is accepted, read the
  handlers.
* (−) The lock order and the dispatch-then-publish pattern are conventions. A helper
  exists, but nothing stops a use case from skipping it, so reviewers check.
* (−) `publish` can lose an announcement if the process stops right after the commit.
* (−) The value lists are mirrored in the frontend by hand.
* (−) The owner's Unpublish button is still shown for a reserved or adopted animal.
  The click is refused with a message; hiding the button is left to the quality and
  clean-up task.
