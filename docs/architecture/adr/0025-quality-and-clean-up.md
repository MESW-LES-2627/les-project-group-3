# ADR 0025: Quality and clean-up

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-11-18 |
| **Scope** | #58 (quality and clean-up): the postal code, a shared confirmation dialog, catalog paging |
| **Related** | [0005-fetch-animal-data](0005-fetch-animal-data.md), [0010-animal-profile-fields](0010-animal-profile-fields.md), [0014-editing-an-animal](0014-editing-an-animal.md), [0016-catalog-filters](0016-catalog-filters.md), [0020-seeing-and-withdrawing-my-requests](0020-seeing-and-withdrawing-my-requests.md), [0023-republishing](0023-republishing.md) |

## Context

Three loose ends from earlier stories. An animal had both a postal code and a
district, which could disagree, and only the district is in the MVP. Unpublish and
Withdraw asked with the browser's `confirm()`, and Unpublish and Republish reported
errors with `alert()`. The catalog returned every published animal in one response.

## Decisions

1. **The district is the only location.** Migration 0009 drops
   `patas.animals.postal_code`; the domain, API, form, animal page and demo seed no
   longer have it. An edit that still sends `postal_code` gets a 422, like any field
   outside the description (ADR 0014). The values are lost; downgrading brings the
   column back empty.
2. **One confirmation dialog**, `ConfirmDialog`, on the browser's modal `<dialog>`:
   it gives the backdrop, Escape, an inert page and focus kept inside without a
   library. It opens on Cancel, the safe choice. A failed action keeps it open with
   the error inside; success closes it. Unpublish and Withdraw use it; their
   wording sits in `src/lib`, next to the existing withdraw text, not in the
   components. Republish still asks nothing (ADR 0023) and shows its error under the
   button. No `alert()` or `confirm()` is left. The inline
   confirmations of the Matchmaker profile and the answer panel stay as they are.
3. **The catalog is paged.** `GET /animals?page=N` returns up to 24 animals (rows of
   2 or 3 cards), newest first, and the number that match the filters in all in
   `X-Total-Count`. It is still a JSON array, so the shape ADR 0005 promises holds.
   `page` starts at 1, defaults to 1, and a page past the end is empty. The filters
   apply before paging. The page shows Previous and Next with "Page X of Y"; both
   keep the filters, and applying filters starts again at page 1.
4. **Paging is done in the service**, after the existing filters (ADR 0016): a few
   hundred animals load in one query. Past a few thousand, filtering and `LIMIT` /
   `OFFSET` should move into SQL, with an index on `(created_at, id)`.
5. **A load seed** (`scripts/seed_catalog.py`, default 300 animals among 100 users)
   fills the catalog to check the paging by hand. Each animal is written in its own
   transaction, so the order is known. Its users exist only in the backend and
   cannot sign in.

## Consequences

* (+) An animal has one location, and the form one field fewer.
* (+) Confirmations look like the rest of the site and work with the keyboard.
* (+) The catalog page stays small however many animals are published.
* (−) Offset paging can skip or repeat an animal published or unpublished between
  two page loads.
* (−) The dialog is a component, so it is checked in the browser, not by Vitest
  (TESTING.md).
* (−) The backend and frontend must be deployed together: an older form still sends
  `postal_code`.
