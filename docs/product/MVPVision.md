# MVP Vision: Patas as a Peer-to-Peer Adoption Marketplace

| Metadata | Detail |
| :--- | :--- |
| **Project** | Patas: Collaborative Animal Welfare Platform |
| **Context** | MESW, Software Engineering Laboratory (2026/27), 4 sprints (about 8 weeks) |
| **Status** | APPROVED: confirmed by the team and the teacher |
| **Relation to [Vision](Vision.md)** | Scope reduction and product pivot for the MVP only. [Vision](Vision.md) remains the long-term vision; this document overrides it wherever they conflict, for the MVP. |

> **Approval note:** per `AGENTS.md` §6, business-logic decisions must be aligned by the whole team before implementation. Section 1 records what was decided; everything marked *Derived* follows from those decisions; everything in Section 11 is still open.

---

## 1. Decisions Taken

| # | Decision | Status |
| :-- | :-- | :-- |
| MD1 | **For the MVP there are no associations.** Any registered user can publish animals for adoption and manages their own catalog, like a marketplace. | **Decided** (team) |
| MD2 | **Option 1, "pure marketplace":** `Animal.ownerId` references a `User`. No `Association` or `Publisher` entity in the MVP. Associations return as a post-MVP increment (see §9). | **Decided** (team) |
| MD3 | Formal association registration and verification is not needed. It disappears together with the association concept. | **Decided** (team) |
| MD4 | **The animal location state machine is dropped for the MVP.** `Animal` keeps a single state machine (adoption status). Whether the animal is with its owner or with the adopter is derived from the adoption status. The location dimension returns together with fostering. | **Decided** (team) |

### 1.1 Alternatives considered (for the ADR)

| Option | Description | Cohesion | Coupling | Cost now | Cost later |
| :-- | :-- | :-- | :-- | :-- | :-- |
| **1. Pure marketplace (chosen)** | `Animal.ownerId = User` | High: one concept of "owner" | Low: no extra aggregate | Lowest | Mechanical migration: create one publisher per user, repoint `ownerId` |
| 2. `Publisher` with individuals only | One publisher row per user, for future associations | Medium | Extra indirection in every query | Medium | Lower than option 1 |
| 3. Associations and individuals together | `Publisher.kind = ASSOCIATION or INDIVIDUAL` | Medium | Rules depend on `kind` | Highest | None |

**Rationale:** `AGENTS.md` §2 forbids overengineering. Abstractions for associations solve a problem the MVP no longer has, and the later migration is cheap. **An ADR must be written for this decision** (`AGENTS.md` §6).

---

## 2. Product Vision Statement (MVP)

> **For** people who want to rehome an animal and people who want to adopt one,
> **Patas** is a collaborative web platform where anyone can publish animals for adoption and anyone can find the one that fits their home.
> **Unlike** social media groups and classifieds, where applicants never know the status of their request and adoption is driven by looks,
> **our product** combines an open catalog with a lifestyle compatibility *Matchmaker*, full process transparency through a real-time *Adoption Tracker*, and an optional *Foster-to-Adopt* trial period. By doing so, we increase the fit between animal and family and reduce the risk of returns.

**Core options in the MVP:**
* **Adopt:** find an animal, apply, follow the process, optionally try it first (trial).
* **Rehome:** publish and manage your own animals, review applications and decide.

*Care* (volunteering) and *Contribute* (wishlist) and association-style *Foster* are **out of the MVP** (see §7).

---

## 3. Problems Addressed (MVP)

The association-side pains of [Vision](Vision.md) §2 (spreadsheets, multichannel chaos, manual screening at scale) no longer apply. The MVP addresses:

**Adopter side**
1. **Application "black hole":** no feedback on whether the request was received, is under review or is closed. *Answered by the Adoption Tracker.*
2. **Adoption driven by looks, followed by returns:** *Answered by the Matchmaker.*
3. **Fear of immediate commitment:** *Answered by the Foster-to-Adopt trial.*

**Owner side (a person rehoming an animal)**
1. **Unstructured requests** arriving by private messages, with no history. *Answered by structured applications with status history and private notes.*
2. **Unsuitable applicants:** *Answered by the compatibility profile of the animal and the Matchmaker.*
3. **No overview** of who applied and in which stage. *Answered by the owner's application list.*

---

## 4. Actors

| Role | Description | Main capabilities |
| :--- | :--- | :--- |
| **Visitor** | Unauthenticated | Browse the catalog, view animal profiles, take the Matchmaker quiz (session only). |
| **Citizen** | Registered user. The same account can be **owner** and **adopter**. | Publish and manage own animals; review and decide on applications received; apply to other users' animals; follow applications; request a trial; report listings. |
| **Platform Administrator** | Patas operator | Moderate: handle reports, suspend users, remove listings. |

*Derived:* Staff, Volunteer and Foster roles disappear from the MVP.

**Rule:** a user cannot apply to their own animal (domain invariant).

---

## 5. MVP Feature Set

Effort: S (a few days), M (about 1 sprint for 1-2 people), L (more than 1 sprint).

### 5.1 Core (must have)

| ID | Feature | Effort | Notes |
| :-- | :-- | :-: | :-- |
| F1 | Authentication and registration | M | Better-Auth with JWT handoff (see [AuthenticationResearch](../research/AuthenticationResearch.md)). Depends on the stack decision (§11). |
| F2 | User profile and admin flag | S | Single `User` aggregate; admin is a platform flag. |
| F3 | Non-functional baseline | M | Docker Compose, responsive layout, basic accessibility, GDPR access rules, CI with linters and specification tests. |
| A1 | Animal listing management (owner) | M | Create, edit, unpublish. Photos. Adoption status as a State pattern. |
| A2 | Public catalog with filters | M | Species, size, age, location, compatibility. Badge showing the owner's name. |
| A3 | Structured compatibility profile of the animal | S | Form fields stored as `compatibility` JSONB; feeds filters and the Matchmaker. |
| A4 | Adoption application and state machine | L | Submitted, Screening, Interview, Completed, Rejected, Withdrawn, On Hold, Closed. Reservation rule, status history, private owner notes. |
| A5 | Adoption Tracker | S | Applicant timeline built from `StatusChange` history. |
| A6 | In-app notifications | S | Created from domain events (Observer). |
| A7 | Moderation | S | "Report" button, admin handles reports, suspends users, removes listings. |

### 5.2 Differentiators (should have)

| ID | Feature | Effort | Notes |
| :-- | :-- | :-: | :-- |
| M1 | Matchmaker quiz and rule-based matching | M | Hard filters, weighted score, explanation badges. Strategy pattern ([MatchingAlgorithms](../research/MatchingAlgorithms.md)). Visitors: session only. |
| M2 | Saved Matchmaker profile for Citizens | S | Includes household composition (children, dogs, cats). |
| T1 | Foster-to-Adopt trial | M | **Owner approves or declines** the request. No fee, no payment. Check-ins while active. |
| A8 | Owner's application list | S | Applications received, grouped by status, with actions. Not a drag-and-drop Kanban. |
| A9 | Email notifications | S | Same events as A6. Local SMTP catcher (Mailpit) keeps it offline-capable. |

### 5.3 Stretch (could have)

| ID | Feature | Effort |
| :-- | :-- | :-: |
| M3 | Tie-break by waiting time (Stage C, shelter seniority becomes "listing age") | S |
| A10 | Listing limits per user and anti-spam rate limits | S |

---

## 6. Domain Model Changes

*Derived* from MD1 and MD2.

| Element | Change |
| :-- | :-- |
| `Association`, `StaffProfile`, `association_memberships` | **Removed** |
| `WishlistItem`, `Pledge` | **Removed** (post-MVP) |
| `FosterProfile`, `FosterAssignment` | **Removed** (post-MVP) |
| `VolunteerProfile` | **Removed** (post-MVP) |
| `Animal.associationId` | Replaced by **`Animal.ownerId`** (reference to `User` by ID) |
| `Animal.location` and its state object | **Removed** (MD4). `Animal` holds one state object (adoption status). A derived query `isWithAdopter()` returns true for `In Trial` and `Adopted`. |
| `TrialPeriod` | Fee fields removed (`feeAmount`, `isFeePaid`, `paymentReference`). Approval belongs to the owner. |
| `User` | Keeps `MatchmakerProfile`; admin as a platform flag. Roles interface only if needed later. |
| **New:** `Report` | Entity for moderation: reporter, target listing or user, reason, status. Aggregate boundaries to be decided. |
| `Notification` | Unchanged. Event types change (no foster or wishlist events). |
| `AdoptionApplication` | Unchanged in structure. The "association" actor becomes "the animal's owner". |

**Data isolation rule (replaces association scoping):**
* The **owner** of the animal sees the applications for that animal.
* The **applicant** sees only their own applications.
* Contact details of the applicant are revealed to the owner only from `Interview` onward (GDPR, *to confirm*).

**Pattern coverage after the cut:** State (animal, application, trial), Strategy (matching), Observer (notifications on transitions), Factory (creation of animals and applications). This still covers every pattern named in `AGENTS.md` §2 that has a concrete use.

---

## 7. State Machine Changes

| Machine | MVP status |
| :-- | :-- |
| Animal adoption status | **Kept** (Available, Reserved, In Trial, Adopted, Unavailable) |
| Adoption application | **Kept** |
| Trial period | **Kept**, simplified: no fee or payment step. `Requested → Approved → Active` becomes `Requested → Active` if the team does not want a separate approval state (*open*, see §11). |
| Animal location | **Removed** (MD4) |
| Foster assignment | Removed (post-MVP) |
| Wishlist item and Pledge | Removed (post-MVP) |
| Association verification | Removed |

**Animal location (decided, MD4).** The second state dimension was introduced to support fostering (Vision, option B: adoption status and location as independent dimensions, so that a fostered animal can still be `Available`). Without fostering, the only remaining locations are "with owner" and "with adopter", and these are fully determined by the adoption status:

| Adoption status | Where the animal is (derived) |
| :-- | :-- |
| Available, Reserved, Unavailable | With owner |
| In Trial, Adopted | With adopter |

Keeping a separate location would duplicate the status and allow contradictory states (e.g. `Adopted` and "with owner"). It is therefore removed, and reintroduced together with fostering (add a `location` column and machine, backfill from the status). **An ADR is required** (`AGENTS.md` §6).

**Cross-machine rules that remain:** reservation on `Interview`, held applications resume when the reservation is released, other open applications become `Closed` when the animal is `Adopted`, trial `Active` moves application and animal, every application transition creates a history entry and a notification.

---

## 8. Scope Summary

### In the MVP
Authentication, user-owned catalogs, public catalog with filters, structured compatibility profile, adoption applications with the full state machine, Adoption Tracker, in-app (and email) notifications, Matchmaker, Foster-to-Adopt trial without payment, moderation.

### Removed from the MVP (vs. [Vision](Vision.md))
Association registration and verification, staff roles and association isolation, Kanban drag-and-drop, Foster family engine, volunteering (walks and roster), solidarity wishlist and pledges, trial fee and Stripe.

### Out of scope (unchanged)
Real payments, online monetary donations, native mobile apps, legal adoption contracts, veterinary records, recording animal deaths.

### Also deferred
Chat between users (notifications and the tracker substitute it in the MVP), swipe-based discovery, LLM trait extraction (Cloudflare Workers AI), vector tie-breaking, bonded pairs, post-adoption check-ins, passive "soulmate" notifications, multimodal photo assistance.

---

## 9. Post-MVP Roadmap

| Increment | Content | Path from MVP |
| :-- | :-- | :-- |
| **Associations** | Association entity, verification, staff, shared catalog per association | Create one publisher per user, repoint `Animal.ownerId`, add the association aggregate. |
| **Fostering** | Foster profiles, parametric engine, location state machine | Reintroduce the location dimension. |
| **Wishlist** | Needs and pledges, for associations | Needs the association concept to limit abuse. |
| **Volunteering** | Walks and roster | Needs associations or facilities. |
| **Trial fee** | Payment through Stripe (test mode) | Optional. |
| **Matching extensions** | Swipe, LLM extraction, screening dossier, soulmate notifications | See [MatchingAlgorithms](../research/MatchingAlgorithms.md). |

---

## 10. Non-Functional Requirements, Trust and Safety

* **GDPR:** applicant data accessible only to the applicant and to the owner of that animal; contacts revealed from `Interview` (*to confirm*).
* **Responsive web and basic accessibility.**
* **Offline-capable demo:** everything runs in Docker with no mandatory external service (email through a local catcher, no Stripe, no LLM).
* **Trust and safety** matters more than in the original vision, because there is no organization behind a listing:
  * Terms of use forbid charging for the animal (adoption, not sale).
  * Report button and admin removal (A7).
  * Optional limit of active listings per user (A10).
* **Cold start:** the demo needs seed data in the database (real data through the application, not static mockups: `AGENTS.md` §5).
* **Quality gates:** linters and specification tests pass in CI (`AGENTS.md` §3 and §4).

---

## 11. Open Questions (to decide before implementation)

1. **Teacher approval of the pivot.** *Resolved:* the teacher approved the scope change.
2. **Trial approval state:** keep `Requested → Approved → Active`, or simplify to `Requested → Active` since there is no payment step?
3. **Contact visibility:** reveal applicant contact from `Interview` (proposed), or earlier or later?
4. **Listing limits per user** and numeric value (A10).
5. **Admin moderation model:** does `Report` become its own aggregate, and what are the states (`Open`, `Resolved`, `Dismissed`)?
6. **Frontend stack:** [AuthenticationResearch](../research/AuthenticationResearch.md) assumes Next.js, but `patas-frontend` is a Vite and React scaffold. Better-Auth needs a Node runtime, so confirm the stack before F1. Needs an ADR.
7. **Decision D1** (referenced in [Vision](Vision.md) §7 but never defined) is resolved by this document: the Foster Engine, Operational Roster and Volunteer Hub are post-MVP.

---

## 12. Suggested Sprint Plan

| Sprint | Content |
| :-- | :-- |
| 1 | F1, F2, F3, A1, A2 (catalog with filters from real data) |
| 2 | A3, A4, A5, A6 (compatibility profile, application flow, tracker, in-app notifications), own-animal invariant |
| 3 | M1, M2, A8, A9, A7 (Matchmaker, owner list, email, moderation) |
| 4 | T1 (trial), seed data, usability tests, hardening; stretch: M3, A10 |

---

## 13. Impact on Existing Documents

These documents still describe the association-based model and must be updated once the team confirms this document:

| Document | Required change |
| :-- | :-- |
| [Vision](Vision.md) | Mark as long-term vision, point to this document; or revise statement, actors, pillars, platform model, prioritization table, out-of-scope. |
| [DomainModel](../domain/DomainModel.md) | Remove association, staff, wishlist, foster and volunteer elements; add `ownerId`; remove `location` (`Animal` holds one state object); add `Report`. |
| `StateMachines.md` | **Done:** removed and replaced by [AdoptionPipeline](../domain/AdoptionPipeline.md) (proposed). |
| [PrototypeFlows_Fostering_Donations](PrototypeFlows_Fostering_Donations.md) | Becomes post-MVP reference; MVP flows (publish animal, apply, track, trial) to be written. |
| [Glossary](../domain/Glossary.md) | Remove association terms; add owner, report. |
| [DatabaseDesignDecisions](../architecture/DatabaseDesignDecisions.md) and `database/create.sql` | Remove association tables; `animals.owner_id` references `users`; drop the `location` column if present; add reports. Check every table that references `association_id`. |
| [MatchingAlgorithms](../research/MatchingAlgorithms.md) | Replace "shelter seniority" with listing age; "staff" becomes "owner". |
| **New** | ADR for MD2 (pure marketplace); ADR for MD4 (dropping the location machine); ADR for the frontend stack. |
