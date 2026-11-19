# ADR 0024: Matchmaker swiping, passes and saved animals

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-11-18 |
| **Scope** | US-11; AT-14 (#68), AT-15 (#69) |
| **Related** | [0005-fetch-animal-data](0005-fetch-animal-data.md), [0008-matchmaker-profile](0008-matchmaker-profile.md), [0013-compatibility-scoring](0013-compatibility-scoring.md), [0019-requesting-to-adopt](0019-requesting-to-adopt.md) |

## Context

An adopter needs a ranked, actionable Matchmaker surface rather than opening
animals individually. Their pass and save decisions must persist privately so
future browsing does not repeat those animals, while a saved animal can still lead
to the existing adoption-request flow.

The acceptance tests require compatible animals before unsuitable ones, reasons
alongside the fit, user-specific history, removable saves, and hiding unpublished
animals from saved results. A globally ranked catalog conflicts with limiting
scoring to a small random sample.

## Decisions

1. **Sample at the database, rank in the service.** Each feed request selects up
   to 100 random available animals with one SQL query, excluding the caller's own
   animals and all of their prior swipes. The service scores that sample using the
   existing loose compatibility strategy, puts compatible results before
   unsuitable ones, sorts by score descending, and returns at most 10.
2. **Ordering is batch-local.** A new request takes a fresh random sample. Scores
   are ordered within each returned batch, not globally across independently
   sampled batches. This bounds scoring work but does not promise that later
   batches contain weaker matches. The selected values of 10 and 100 are initial
   product settings and can be revisited after observing response time.
3. **A swipe is private state owned by the adopter.** `matchmaker_swipes` has a
   composite primary key of user and animal. One row records either `passed` or
   `saved`; a unique constraint makes duplicate swipes impossible, including
   concurrent requests. Both records are excluded from future feed samples.
4. **Removing a save does not undo a swipe.** It changes `saved` to `passed`.
   The animal leaves the saved list and stays out of the feed, preserving the
   invariant that a previously presented animal is never presented again.
5. **Current availability controls saved visibility.** The saved list joins saved
   decisions to the current animal catalog and includes only available,
   non-owned animals. Unpublishing or reserving an animal therefore removes it
   from this list without deleting the user's history.
6. **Keep the existing adoption flow.** A saved card links to the animal page and
   provides the existing adoption request form. The request service still owns
   eligibility and persistence rules; swipe state does not create an application.
7. **Keep the existing server-side trust boundary.** Next.js Server Actions add
   the signed-in user's token; the browser never calls the backend API directly.
   The backend requires authentication for listing and mutating private swipe
   history.

## Consequences

* (+) A bounded number of animals is scored per request, and the database does not
  transfer the full catalog to the application service for feed selection.
* (+) Database uniqueness, user scoping and server-side authentication protect
  history from duplicate writes and cross-user visibility.
* (+) Existing compatibility reasons and adoption-request rules are reused.
* (−) A strong match in a later random sample may follow a weaker one from an
  earlier batch.
* (−) Removing a saved animal passes it permanently; there is no undo in this
  story.

## Development data

[`patas-frontend/scripts/animal-generation.mjs`](../../../patas-frontend/scripts/animal-generation.mjs)
generates demo animals and publishes them through the authenticated
`POST /animals` endpoint. It randomly assigns each animal to one of the three
standard demo accounts; it does not select arbitrary registered users or write
directly to the database. Run `pnpm seed:animals` from `patas-frontend` with the
stack running to add 100 animals.