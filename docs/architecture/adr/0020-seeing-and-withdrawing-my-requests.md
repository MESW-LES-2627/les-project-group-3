# ADR 0020: Seeing and withdrawing my requests

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-11-12 |
| **Scope** | US-15 (#61), US-17 (#63); AT-17 (#71), AT-19 (#73) |
| **Related** | [0005-fetch-animal-data](0005-fetch-animal-data.md), [0016-catalog-filters](0016-catalog-filters.md), [0017-adoption-base](0017-adoption-base.md) (decisions 3 and 8), [0019-requesting-to-adopt](0019-requesting-to-adopt.md) (decisions 6 and 9) |

## Context

US-14 lets a person send a request, and the animal page shows the one active
request they have for that animal. Nothing shows the requests that ended, or the
owner's reply, and nothing lets a person take a request back. The adoption base
already has the change itself: `AdoptionApplication.withdraw()` is allowed from
open and accepted, and the `release_animal` handler frees a reserved animal when
an accepted request is withdrawn. US-17 adds the sent list and withdrawal use
case; US-15 adds the received list to the same page.

## Decisions

1. **One page, `/requests`, with one header link, "Requests".** It has **Sent** and
   **Received** tabs, so the two lists of requests share one header link. Each
   story owns its section's component; only the page file is shared.
2. **The list is a read model.** `SentRequest` is a frozen dataclass with what the
   list shows: the request, its status, both notes, the date and the animal's name.
   `AdoptionApplicationRepository.list_sent_by` loads it with one query that joins
   the animal and leaves out the profile snapshot. The received read model includes
   the saved applicant profile; the service evaluates it against the current animal
   profile with the flexible Matchmaker strategy and includes its concern reasons.
   The aggregate stays the only way to change a request; read models have no rules.
3. **The list keeps every status**, newest first, so the person sees the answers
   (declined, with the owner's note) and the history, not only what is active.
4. **Withdrawing locks the animal first** (ADR 0017, decision 8), through
   `lock_animal_and_application`. Whether the request was accepted, and so whether
   the animal is freed, is read under that lock: a withdrawal queued behind an
   accept sees it accepted and frees the animal. A test holds the lock to make the
   two meet, and it fails if the use case stops locking the animal.
5. **Someone else's request is a 404**, the same as one that does not exist, so the
   endpoint does not reveal which ids are real. This matches
   `GET /animals/{id}/my-application`. The service checks the applicant and the
   aggregate still raises `ApplicationUnauthorized` behind it.
6. **Request endpoints.** `GET /me/applications` lists the caller's requests;
   `GET /me/received-applications` lists requests for the caller's animals and
   returns the applicant snapshot only to that owner.
   `POST /applications/{id}/withdraw` answers 200 with the request, 404 as above, or
   409 for a request that already ended. The 409 carries
   `{"code": "invalid_transition"}` although it has one cause, unlike what ADR 0019
   decision 6 says for single-cause conflicts: every 409 of the adoption router then
   has the same shape, and accepting (US-16) will have more than one cause.
7. **Rendering: data on the server, filtering in the browser.** The page loads the
   whole list on the server (ADR 0005), inside a `<Suspense>` boundary because the
   project uses Partial Prerendering. A client component filters it by status. The
   filter is one value in the URL (`?status=declined`), like the catalog (ADR 0016),
   written with `window.history.replaceState`, so changing it does not go back to
   the server. The backend has no filter parameter.
8. **Withdrawing asks with `window.confirm()`**, with a stronger message for an
   accepted request, since withdrawing it frees the animal for others. Task #58
   replaces it with the shared dialog, together with the unpublish one. The button
   also sits in the "Your request" block of the animal page.

## Alternatives considered

* **Header:** no new link, with the list reachable from Profile (hard to find); an
  account menu grouping Profile, My animals, Requests and Matchmaker (the right fix
  for a crowded header, but a task of its own, proposed below).
* **Someone else's request answering 403:** simpler to map from the domain error,
  but it confirms that the id exists.
* **Loading the aggregates and then the animals' names:** two queries, loads the
  profile snapshot for nothing, and joins by hand in the service.
* **Full client-side rendering through a Next.js Route Handler (`/api/requests`):**
  a new pattern with no need for it here. It would not serve the chat either, since
  a Route Handler cannot proxy a WebSocket. How the browser gets live data is left
  to the chat's ADR, where the real-time transport will decide it.
* **Live updates (polling with `router.refresh()`, SSE, WebSockets):** until US-16
  exists, nothing outside the applicant changes a sent request.
* **A two-step confirmation inside the row:** a second confirmation pattern for
  task #58 to merge.

## Pending team agreement

`AGENTS.md` section 6 asks for business rules to be agreed with the team before they
are implemented. The code follows these proposals:

* **The `/requests` page is shared with US-15** (decision 1).
* **Lists that join two aggregates use read models** (decision 2).
* **D10 (AdoptionPipeline): should a handover confirmation block a withdrawal?**
  Today it does not: an accepted request can be withdrawn after one side confirmed.

Proposed to the team, not done here: an account menu in the header, and links for
small screens. The navigation is `hidden sm:flex`, so below `sm` only Matchmaker and
Log out show.

## Consequences

* (+) Each list has a request read query, and the aggregate stays the only way to
  change a request.
* (+) The received list reuses Matchmaker's flexible compatibility rules and
  surfaces concerns without making an adoption decision.
* (+) Filtering is instant, and a filtered list can be shared by its URL.
* (+) The race between a withdrawal and an accept is covered by a test that fails
  without the lock order.
* (−) The adoption repository now returns two kinds of object: the aggregate and a
  read model.
* (−) The page shows what was true when it loaded; the owner's answer appears on the
  next visit or reload.
* (−) `confirm()` is the browser's dialog until task #58.
* (−) The frontend has no test runner, so the filter and the button are checked by
  lint, typecheck, build and in the browser only.
