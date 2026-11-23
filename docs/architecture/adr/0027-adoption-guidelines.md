# ADR 0027: Guidelines next to an accepted request

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-11-23 |
| **Scope** | US-24 (#116); AT-26 (#132) |
| **Related** | [0017-adoption-base](0017-adoption-base.md), [0020-seeing-and-withdrawing-my-requests](0020-seeing-and-withdrawing-my-requests.md), [0021-quality-pipeline](0021-quality-pipeline.md) |

## Context

Once a request is accepted, the owner and the adopter have to get to know each
other and arrange the handover. US-24 asks for suggested questions, safety tips and
the reminder that adoption is not a sale, shown to both of them. The text is the
same for everyone and changes only when the team rewrites it. The chat (US-21) is
not built yet, and the handover checklist with ticks is a separate story (US-25).

## Decisions

1. **Five read-only steps, the same for owner and adopter:** get to know the animal,
   get to know the new home, meet safely, adoption is not a sale, plan the handover.
   Nothing is ticked or saved; ticking belongs to the handover checklist (US-25).
2. **The content is a frontend constant**, `ADOPTION_GUIDELINES` in
   `src/lib/adoption-guidelines.ts`. It ships with the page and is cached with it,
   so there is no endpoint and no table. The rule for when it shows,
   `showsGuidelines` (only while the request is accepted), sits next to it and is
   tested with Vitest. It adds no access rule: a person only sees requests the
   backend already returned to them (ADR 0020, decision 5).
3. **Shown on `/requests`** inside each accepted request, in both the Sent and the
   Received list, collapsed by default. It moves next to the conversation when
   US-21 adds the chat page.

## Consequences

- Changing the wording needs a frontend deploy.
- Varying the steps by role or species would turn the constant into a function of
  the request.
- The automated part of AT-26 for the guidelines is a Vitest test of
  `showsGuidelines` and the step titles; a teammate checks the page in a browser.

## Alternatives considered

- **A backend domain object served by an endpoint:** an endpoint, a schema and an
  API test for static text that has nothing to protect.
- **A configuration file loaded by the backend:** loading and validating a file is
  more than a 1-point story needs, and the team edits the text through pull
  requests anyway.
