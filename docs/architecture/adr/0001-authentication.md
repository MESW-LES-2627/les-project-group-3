# ADR 0001: Authentication with Better-Auth and JWT verification in FastAPI

| | |
| :-- | :-- |
| **Status** | Accepted |
| **Date** | 2026-10-16 |
| **Scope** | F1 (authentication), vertical prototype |
| **Related** | [AuthenticationResearch](../../research/AuthenticationResearch.md), [VerticalPrototypeSpec](../../iterations/0/VerticalPrototypeSpec.md) |

## Context

Users register and log in through Next.js. FastAPI must trust who is calling
without owning passwords or sessions. `patas.users` is the domain profile.

## Decisions

1. **Better-Auth owns credentials and sessions** (Next.js). FastAPI never sees a password.
2. **FastAPI verifies a Better-Auth JWT through JWKS.** EdDSA, keys fetched from
   `/api/auth/jwks` and cached. FastAPI holds no secret. The algorithm is fixed in
   our code (never read from the token header) and `exp`, `iss`, `aud`, `sub` are required.
3. **Same identity:** the Better-Auth user id (`generateId: "uuid"`) is the JWT `sub`
   and the primary key of `patas.users`.
4. **Schema isolation:** Better-Auth tables live in `patas_auth` (selected through the
   connection's `search_path`); the domain lives in `patas`. Alembic creates the
   `patas_auth` schema and never touches its tables.
5. **Just-in-time provisioning:** the first authenticated call runs
   `INSERT ... ON CONFLICT (id) DO NOTHING` in its own transaction. An email already
   owned by another id is refused with 401 and logged.
6. **Authority is never in the token.** The token carries identity only
   (`sub`, `email`, `name`). `is_platform_admin` is read from `patas.users`.
7. **Persistence convention:** domain classes stay free of SQLAlchemy; repositories use
   SQLAlchemy Core with explicit row mapping (no ORM mapping), and never commit.
   Revisit if aggregates make repositories large and repetitive.

## Consequences

* (+) No shared secret; tokens are checked without a database lookup.
* (+) Auth failures never store anything; concurrent first requests are safe.
* (-) FastAPI needs Next.js reachable to fetch keys (cached; an outage gives 503, not 401).
* (-) A name changed in Better-Auth is not synced to `patas.users` yet (out of scope until profile editing).
* (-) Hand-written repository SQL grows per aggregate.
