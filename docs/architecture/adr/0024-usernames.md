# ADR 0024: Unique usernames

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-11-16 |
| **Scope** | US-20 (#66, choose a unique username); AT-22 (#76) |
| **Related** | [0001-authentication](0001-authentication.md), [0005-fetch-animal-data](0005-fetch-animal-data.md), [0006-application-services](0006-application-services.md), [0014-editing-an-animal](0014-editing-an-animal.md), [0015-public-animal-profile-page](0015-public-animal-profile-page.md), [0019-requesting-to-adopt](0019-requesting-to-adopt.md) |

## Context

People are shown by a free-text name, and names repeat. US-20 adds a username that
nobody else has, so people can be told apart. Better Auth owns sign-in and its own
user table; the backend keeps `patas.users` with the same id (ADR 0001), and every
"Published by" and "Requested by" comes from there.

## Decisions

1. **The backend owns the username.** `patas.users.username` is stored as typed and is
   unique ignoring case (`idx_users_username_lower`, like the email). Better Auth's
   username plugin was not used: the rule would live outside the domain, CI could not
   test it, and staging would need a Better Auth migration.
2. **The rule is in the domain.** 3 to 30 letters, digits, `_` or `.`, with no `.` at
   either end (`validate_username`, mirrored by `users_username_format_check`). It is
   the plugin's default rule, so switching later stays possible.
3. **Every user has one.** Migration 0008 backfills existing users from their name
   (`"Ana Demo"` gives `ana_demo`, then `ana_demo2`; accents dropped, padded when too
   short), so the column is `NOT NULL`. The name, not the email, so no part of a
   private address becomes public. A first backend call provisions a new user the
   same way, trying the next candidate in a savepoint when one is taken.
4. **`PATCH /me` changes the name, the username or both** through a new `UserService`,
   so `/me` follows ADR 0006 like the other routers. The row is locked (ADR 0014,
   decision 6), so a name change never writes back an old username. A malformed
   username is 422; a taken one is 409 `username_taken` (ADR 0019 style) and nothing
   changes.
5. **`GET /usernames/{username}` is public** and answers `{username, available}`. The
   register page asks it before Better Auth creates the account, so a taken username
   is refused up front, then sets it with `PATCH /me`. If someone takes it in between,
   the account keeps its derived username and the page says to choose another on the
   profile. Signing up already tells anyone whether a username is free; the endpoint
   only makes that one call.
6. **Shown next to the name:** "Ana Demo (@ana_demo)" on Published by and Requested by
   (`owner_username`, `applicant_username` from the same joins as the names). The
   header greeting and Better Auth's `name` are unchanged; the username is not copied
   into Better Auth.

## Pending team agreement

The rule and display above were chosen with the story's author; the team still has
to agree. Out of scope: reserved names (admin, patas ...), signing in with the
username, and limits on how often it changes.

## Consequences

* (+) The whole of AT-22 runs in the backend suite, including the backfill.
* (+) Sign-in is untouched: users still sign in with email and password.
* (−) Registering is two steps, so the rare race above leaves a derived username.
* (−) Usernames derived from names are predictable, so anyone can check whether, for
  example, `maria_santos` has an account, even one that never published. Choosing
  another username hides it; rate limiting is left until it is needed.
* (−) The username rule is written three times: domain, database CHECK, and the
  frontend's early check (`src/lib/username.ts`); the backend has the final word.
