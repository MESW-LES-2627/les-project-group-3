# ADR 0009: Matchmaker profile page (frontend)

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-10-25 |
| **Scope** | US-08 frontend: the `/matchmaker` page and its form |
| **Related** | [0005-fetch-animal-data](0005-fetch-animal-data.md), [0007-ui-improvements](0007-ui-improvements.md), [0008-matchmaker-profile](0008-matchmaker-profile.md) |

## Context

The Matchmaker profile page is the first form in the frontend that needs live
feedback (a summary that follows the answers), validation before saving, and three
backend operations (read, save, delete). The backend contract is fixed by ADR 0008,
and the browser never calls FastAPI directly (ADR 0005).

## Decisions

1. **One server-side module owns every call to the backend.** `src/lib/matchmaker-api.ts`
   runs on the Next.js server, adds the signed-in user's token to each request, turns
   status codes into plain results (saved, invalid, unavailable) and checks the shape
   of every reply at runtime. It handles HTTP only; the rules stay in the backend.
2. **Server actions are thin and are passed in as props.** `app/matchmaker/actions.ts`
   validates the answers again and delegates to the module above. The page hands
   `save` and `remove` to the form, so shared components never import from a route
   folder and the same form can be hosted by the US-09 profile page. Reading is not an
   action: a `"use server"` file exposes every function in it as a public endpoint.
3. **Code layout follows the repo's convention:** types, wording and the API module in
   `src/lib`, controls and the form in `src/components/matchmaker`, route files in
   `src/app/matchmaker`. No feature folder.
4. **The form sends typed state, not `FormData`.** It already holds the answers as
   state for the live summary, so submit passes that object to the action. This avoids
   React 19's form reset fighting controlled inputs. Saving needs JavaScript, as the
   login and registration forms already do.
5. **Validation is explicit.** No answer is ever pre-selected. An incomplete save sends
   nothing: it marks each unanswered question, scrolls to the first and focuses it.
   Inputs stay `required` so assistive technology announces them, while the browser's
   own bubble is off. The action and the backend check the answers again.
6. **Native radio inputs styled as cards, no UI library.** Keyboard use and screen
   readers come from the browser. Icons come from `lucide-react`, pinned to an exact
   version (the newest release older than two weeks, no install scripts) and added with
   pnpm 12.14.0, the version in `packageManager`: pnpm 9 rewrites the whole lockfile.
7. **Accessibility and motion are rules, not polish.** Text meets 4.5:1 (a selected card
   is a faint tint mixed with white, never laid over the page background), control
   borders about 3:1, motion is state feedback only and is off for reduced motion, and
   only the result of an action is announced to screen readers.
8. **The option wording is part of the contract.** The anchor lines for energy and
   experience define what *low*, *moderate*, *some* and *experienced* mean on the
   profile; the animal side (US-07) must describe the same scales with the same meaning.
9. **The page makes no promise about who can see the answers.** The owner will later see
   an applicant's profile with the score attached, so privacy copy would become false.

## Consequences

* **Positive:** one place for backend calls and error mapping; the form is reusable and
  testable with any save and remove functions; keyboard and screen-reader behaviour
  comes from native inputs.
* **Negative:** the value lists (housing, energy, ...) are duplicated in
  `lib/matchmaker-profile.ts`. They match the backend today (checked by a one-off
  script), but nothing in CI prevents drift. Types generated from the backend's OpenAPI
  document could close that gap and would be a separate decision.
* **Negative:** the frontend has no test runner. The automated gates are lint, typecheck
  and build; behaviour was verified by a scripted browser pass (not part of CI) and
  needs a teammate's manual check.
* **Negative:** a green build does not prove styles were generated: one edit silently
  dropped two classes while lint, typecheck and build passed. UI changes need the
  generated CSS or a browser checked.
* **Negative:** `lucide-react` adds supply-chain surface. It is pinned and should be
  re-checked on upgrade.
