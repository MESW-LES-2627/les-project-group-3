# ADR 0016: Catalog filters and the animal's district

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-11-03 |
| **Scope** | US-06 (filter the catalog): AT-06, the filters half of AT-03, AT-05's "dog" results; the district US-01 asks for |
| **Related** | [0004-animal-aggregate](0004-animal-aggregate.md), [0010-animal-profile-fields](0010-animal-profile-fields.md), [0011-animal-match-profile](0011-animal-match-profile.md), [0012-owner-animals-and-unpublishing](0012-owner-animals-and-unpublishing.md), [0014-editing-an-animal](0014-editing-an-animal.md) |

## Context

A visitor filters the public catalog by species, size, age group and district.
An animal had no district, only an optional postal code (ADR 0010), and the
service already narrowed the catalog by species.

## Decisions

1. **The district is optional and picked from a list**: Portugal's 18 districts,
   Açores and Madeira, as the `patas.district` enum (migration `0006`). The postal
   code stays and is not checked against it. The team has yet to confirm the list.
2. **`CatalogFilter` decides what matches.** It is a domain value object with one
   optional criterion per filter. All criteria must hold, and an animal without
   the asked-for value never matches: an unknown size is not "large".
3. **One value per filter**, as the `species`, `size`, `district` and `age_group`
   query parameters of `GET /animals`. An unknown value is a 422.
4. **The service filters the published animals in memory**, not in SQL. The
   catalog is small and the rule stays in one tested place. If it grows,
   `list_all` can take the filter and turn it into a `WHERE`.
5. **The age group is the match profile's life stage** (PR #51): baby under 12
   months, senior from 96, for every species.
6. **The catalog page keeps the filters in its URL** through a GET form, so a
   filtered list can be shared and the back button restores it. A value the
   backend would reject is dropped from the URL's filters.

## Consequences

* (+) A new filter is one criterion in `CatalogFilter`, one query parameter, and
  a select with its allowed values on the catalog page.
* (−) Each catalog request loads every published animal.
* (−) The district list is mirrored in the frontend, like the other enums (ADR 0010).
* (−) Animals published before this change have no district until edited.
