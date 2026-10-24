# ADR 0006: Application services own use cases and transactions

| | |
| :-- | :-- |
| **Status** | Accepted |
| **Date** | 2026-10-20 |
| **Scope** | Backend layering, every router |
| **Related** | [VerticalPrototypeSpec](../../iterations/0/VerticalPrototypeSpec.md) §3.2, [0004-animal-aggregate](0004-animal-aggregate.md), [0005-fetch-animal-data](0005-fetch-animal-data.md) |

## Context

The spec layers the backend as router → application service → domain → repository.
The first animal endpoint went from the router straight to the repository, so the
router owned the database session. As use cases grow (an adoption touches the
application, the animal and a notification in one transaction), that logic would
end up in HTTP code, or the domain would need database access.

## Decisions

1. **Routers never talk to repositories or open transactions.** A router translates
   HTTP (request body, auth dependency, status codes) and calls one service method.
2. **One service groups the use cases of an area, not of a table.** `AnimalService`
   has `publish` (A1) and `list_catalog` (A2); later use cases (edit, unpublish) are
   new methods. A use case that spans several aggregates still lives in one service.
3. **A service method is the transaction boundary.** It builds or loads domain
   objects (which enforce their own rules), then persists them through repositories
   in one `session_factory.begin()` block. Repositories never commit. Reads use a
   plain session.
4. **Business rules stay in the domain.** The service orchestrates; it does not
   validate. Request models check types only, so `InvalidAnimal` from the domain is
   the single source of a 422 for rule violations.
5. **Exception:** authentication provisioning (`get_current_user`) keeps its own
   short transaction, by design in [0001-authentication](0001-authentication.md).

## Consequences

* **Positive:** HTTP, rules, coordination and SQL each have one place; tests of an
  endpoint exercise the full path; future multi-step use cases have a home.
* **Negative:** while a use case is a single step, the service is a thin pass-through.
  We accept that to keep one consistent rule for every router.
