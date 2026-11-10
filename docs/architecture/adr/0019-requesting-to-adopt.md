# ADR 0019: Requesting to adopt

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-11-10 |
| **Scope** | US-14 (#60); AT-16 (#70) |
| **Related** | [0017-adoption-base](0017-adoption-base.md) (decisions 1, 5, 7 and 8), [0006-application-services](0006-application-services.md), [0018-test-layout](0018-test-layout.md) |

## Context

The adoption base gave us the application record, its states and a lock order, but
no way to create a request. US-14 adds it: a signed-in person sends the owner a note,
and the request carries a copy of their Matchmaker profile. ADR 0017 left two things
to this story: where the rule on the note lives, and how a use case that creates a
request must lock the animal.

## Decisions

1. **The note is required and at most 1000 characters**, counted after trimming. The
   rule is in `AdoptionApplication.request()`, not in the constructor, because the
   constructor also loads stored rows, and a row saved before the rule existed must
   still load. The router checks only types, and a client-side check exists to save a
   round trip.
2. **An animal is open to requests only while it is available.**
   `Animal.ensure_open_to_requests()` raises `AnimalNotAvailable` for a reserved,
   adopted or unpublished animal. It is a check and not a status change, so it is not
   an `InvalidAnimalTransition`.
3. **The use case locks the animal first**, then checks everything else
   (`AdoptionService.request_to_adopt`, ADR 0017 decision 8). The lock also queues two
   requests from the same person, so the duplicate check is safe, and a request cannot
   slip in beside an unpublish. The database index on one active request per applicant
   and animal stays as the last defence, and would otherwise surface as a 500.
4. **The refusals come in a fixed order:** no such animal (404), the applicant owns it
   (403), the animal is not available (409), the applicant already has an active
   request (409), the applicant has no Matchmaker profile (409), then the note (422).
   What is wrong with the animal comes before what is missing from the applicant, so
   an owner without a profile is told she owns the animal, not to create a profile.
5. **A distinct error for the owner.** `OwnerCannotApply` is an `InvalidApplication`,
   so the router answers 403 for it and 422 for a bad note. The service checks the
   owner itself, to get the order above, and the aggregate still guards itself.
6. **The 409 carries a code.** It has three causes, so the body is
   `{"detail": {"code", "message"}}` with `animal_not_available`, `already_requested`
   or `matchmaker_profile_required`. The compatibility endpoint keeps its plain
   string: it has only one cause.
7. **A person with no Matchmaker profile cannot ask.** The profile is part of the
   request (ADR 0017 decision 4), so the request is refused and the page shows a
   notice with a link to create one, keeping the note the person had written.
8. **Only an active request blocks a new one.** Open and accepted count. A declined,
   withdrawn, closed or adopted request does not.
9. **Two endpoints.** `POST /animals/{id}/applications` creates the request (201) and
   `GET /animals/{id}/my-application` returns the caller's active request or 404, which
   the animal page needs. Neither returns the profile copy: it is for the owner.
10. **No event yet.** Nothing reacts to a new request, so none is published. The
    service already receives the dispatcher, so US-15 or the chat can add one without
    changing this use case's signature.
11. **The page.** The animal page gets a section after the fit. It shows the form, the
    request already sent, or the reason there is none (visitor, owner, animal not
    taking requests). `getMyApplication` never throws on a backend failure, because the
    page is public and this block must not take it down.

## Pending team agreement

`AGENTS.md` section 6 asks for business rules to be agreed with the team before they
are implemented. The code follows these proposals:

* **The note is required, with a limit of 1000 characters.** Decision 1.
* **A person with no Matchmaker profile cannot ask.** Decision 7. The alternative is
  to allow it and let the owner see a request without a profile.
* **A request can be sent again once the previous one ended** (declined, withdrawn,
  closed). Decision 8. The alternative is one request per person and animal for good.

## Consequences

* (+) The rules are in the domain and the database, and the endpoint only maps them to
  status codes.
* (+) The two races (a request against an unpublish, and the same person twice) are
  covered by tests that hold the animal's lock, and fail if the use case stops locking
  first.
* (−) There is no way to withdraw a request from this story. That is US-17, so a
  request sent by mistake stays open until then.
* (−) The animal page asks the backend for the caller's request on every visit, one
  extra call for a signed-in non-owner.
* (−) The owner check exists in the service and in the aggregate. It is repeated on
  purpose, to get the order of refusals, and a change to the rule must touch both.
