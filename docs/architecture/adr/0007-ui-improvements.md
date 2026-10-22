# ADR 0007: Shared navigation and animal catalog UI

| | |
| :-- | :-- |
| **Status** | Accepted |
| **Date** | 2026-10-22 |
| **Scope** | Frontend shell, authentication navigation, animal catalog |
| **Related** | [0001-authentication](0001-authentication.md), [0005-fetch-animal-data](0005-fetch-animal-data.md) |

## Context

The first frontend slice exposed the animal catalog and authentication forms, but
had only minimal page styling and no navigation shared across routes. Users needed
a consistent way to reach the catalog and to see whether they were signed in,
while the catalog needed a clearer presentation without replacing its live data
flow with a static mock-up.

## Decisions

1. **The root layout owns the shared site header.** The header appears on every
   route and links back to the animal catalog. It is a server component and reads
   the Better Auth session from the incoming request headers; it does not maintain
   a separate client-side copy of authentication state.
2. **Navigation reflects the server-validated session.** Visitors see links to log
   in and register. Signed-in users see their name when available and a Log out
   button instead. The logout button calls Better Auth's client `signOut` method,
   reports failures in the interface, then navigates to the login page and refreshes
   server-rendered content.
3. **Authentication pages are for signed-out users.** The login and registration
   pages check the request session on the server and redirect an authenticated
   visitor to `/animals`. Successful login and registration replace the current
   route with `/animals` and refresh server-rendered content so the shared header
   reflects the updated session.
4. **The catalog presentation remains data-driven.** The `/animals` page keeps the
   server-side, uncached `GET /animals` flow and runtime response validation from
   [0005-fetch-animal-data](0005-fetch-animal-data.md). Its new layout improves
   hierarchy, status and species labels, age display, and empty-state messaging;
   the animal cards continue to be rendered from backend results.
5. **Shared visual tokens live in the global stylesheet.** The frontend defines a
   small palette for background, text, surfaces, borders, and accent colors. Pages
   and shared components use these tokens rather than duplicating page-level color
   definitions.

## Consequences

* **Positive:** Navigation and authentication actions are available consistently
  across routes, and the server session remains the source of truth.
* **Positive:** Login, registration, and logout update the shared header without
  relying on a separately synchronized client-side session.
* **Positive:** The catalog is more readable while continuing to display validated,
  live backend data.
* **Negative:** The shared header and auth-page guards depend on the authentication
  service and database being available when requests are rendered.