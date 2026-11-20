# AI Critique — Iteration 2

This is a short reflection on how AI was used, not a chronological prompt log.

## How we used AI

Describe one or more completed tasks. For each, distinguish what AI proposed or
produced from what a team member checked, changed, tested, or decided.

| Completed task | AI assistance | Team contribution and verification |
| :-- | :-- | :-- |
| Adoption base (ADR 0017) — application aggregate, state machine, domain events | AI sketched the `AdoptionApplication` aggregate with the State pattern, the event dispatcher, and the lock-order helper. AI wrote the initial repository and the seed script. | The team defined the six statuses, the handover rule (two confirmations adopt), the lock order (animal first, then application), and the dispatch-then-publish pattern. The domain rules were reviewed against the AdoptionPipeline document, and the seed script was adjusted to bypass transitions on purpose so that states unreachable through the application could still be seeded. |
| Unique usernames (ADR 0024) — validation, backfill, public check endpoint | AI drafted the username validation regex, the migration backfill logic, and the `PATCH /me` endpoint. | The team decided to store the username in the backend (not in Better Auth), chose the name-based derivation rule (not email-based), and designed the public `GET /usernames/{username}` endpoint for the register page. The team reviewed the backfill collision strategy (sequential suffix). |
| Quality and clean-up (ADR 0025) — shared dialog, catalog paging, drop postal code | AI proposed the `<dialog>`-based `ConfirmDialog` component and the paging logic for the catalog. | The team decided on one shared confirmation dialog (not per-component), chose 24 animals per page (rows of 2 or 3 cards), and agreed to drop the postal code column entirely (not deprecate it). The team verified that the dialog keeps open on error and closes on success. |

## Decisions and human judgement

Choose an important decision where the team exercised judgement rather than
accepting an AI suggestion by default. Explain the context, alternatives or AI
input, what the team chose, and the reason for that choice.

| Decision and context | AI input or alternatives | Team's decision and reason |
| :-- | :-- | :-- |
| Adoption state machine — six statuses with two-confirm handover | AI initially proposed a simpler four-state model (open, accepted, declined, adopted) without separate confirmation tracking. | The team chose six statuses (open, accepted, declined, withdrawn, closed, adopted) with explicit handover confirmations because the MVP requires both parties to confirm before the adoption is final. This matches the real-world process where neither side can unilaterally complete the adoption. |
| Username ownership — backend vs Better Auth plugin | AI suggested using Better Auth's built-in username plugin to avoid duplicating validation logic. | The team decided to own the username in the backend (`patas.users.username`) so that the rule is testable in CI, visible in the domain model, and does not require a Better Auth migration on staging. |
| Matchmaker feed — batch-local vs global ranking | AI proposed ranking all available animals globally and returning the top 10. | The team chose batch-local ordering: sample 100 random animals, score them, and return the top 10. Global ranking would score the entire catalog on every request, which is unnecessary for a discovery feed and would degrade as the catalog grows. |

## Errors, mistakes, and corrections

Record at least one specific, verified AI error or unsuitable suggestion:
what it got wrong, how the team noticed, what was corrected, and what was
learned. Link to evidence where possible. If review finds no verified example,
say so explicitly rather than manufacturing one.

| What AI got wrong | How it was caught | Correction and lesson |
| :-- | :-- | :-- |
| AI generated the adoption event dispatcher without locking the animal first, so a handler could save the animal after the use case had already released its lock — a silent revert. | The lock-order test (`lock_animal_and_application`) failed when the use case stopped locking the animal before dispatching. The team noticed the pattern during code review of the adoption base. | The helper `lock_animal_and_application` was created to enforce the order: animal first, then application. The use case now passes the lock to the dispatcher, and the handler loads and saves its own copy of the animal. Documented in ADR 0017, decision 8. |
| AI proposed keeping the `postal_code` column and marking it as deprecated instead of dropping it, which would have left two location fields that could disagree. | The team reviewed the animal model and noticed that the district is the only location field in the MVP (ADR 0010). | Migration 0009 drops `postal_code` entirely. The form, API, and domain no longer reference it. An edit that still sends `postal_code` gets a 422. Documented in ADR 0025, decision 1. |
| AI initially configured the quality gate to count line coverage in async services without handling `await`, so the coverage report showed artificially low numbers for services with database calls. | The CI gate failed on a merge that clearly had tests — the coverage numbers did not match the expected range. | The coverage configuration was fixed to count lines after an `await` in async services (commit `05a4161`). The gate now correctly measures the branch coverage of the code with logic. |

## Linked change

Link one completed change that illustrates the account above (for example, a
pull request or commit). Briefly identify the AI contribution and the human
review, decision, or correction visible in that change.

- Change link: [PR #78 — Adoption base](https://github.com/MESW-LES-2627/les-project-group-3/pull/78)
- What it demonstrates: AI sketched the `AdoptionApplication` aggregate and the event dispatcher. The team defined the six statuses, the handover rule, and the lock order (animal first, then application). The lock-order helper (`lock_animal_and_application`) was added during review to prevent a silent revert when a handler saves the animal after the use case releases its lock.

## What worked well and what we will change

Summarize what was useful, what required human expertise or checking, and one
specific adjustment the team will make when using AI next time.

AI was most useful for scaffolding repetitive structures: the adoption aggregate
state classes, the swipe repository, the quality scripts, and the test layout
migration. It handled the mechanical work of generating boilerplate code,
migrations, and CI configurations quickly.

Human expertise was essential for domain rules: the adoption state machine
(transitions, handover confirmations, lock ordering), the business decision to
drop `postal_code` entirely, the choice of batch-local over global ranking in
the Matchmaker feed, and the decision to own usernames in the backend rather
than delegating to Better Auth. Every ADR from this iteration records a business
rule that the team defined, not the AI.

One adjustment for next time: before asking AI to generate code for a new feature,
we will write the business rule in the ADR or ticket first, so that the AI fills in
implementation details around a fixed contract rather than inventing the rule
itself. This prevents the AI from proposing domain logic that the team must later
correct, as happened with the adoption state machine and the postal code column.
