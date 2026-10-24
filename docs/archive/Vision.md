# Product Vision & Strategic Ideas Repository: Patas

| Metadata | Detail |
| :--- | :--- |
| **Project** | Patas: Collaborative Animal Welfare Platform |
| **Context** | Web Project / Software Engineering (Agile Process in 4 Sprints) |
| **Date** | October 2026 |
| **Status** | Consolidated Vision & Open Ideas Repository |

---

## 1. Product Vision Statement

> **For** animal lovers looking to adopt, foster or care for animals, and for animal protection associations struggling with administrative overload,  
> **Patas** is a collaborative web platform that centralizes and simplifies the entire animal care and adoption cycle.  
> **Unlike** manual processes relying on spreadsheets, chaotic group chats and scattered applications that leave adopters in the dark,  **our product** combines an open exploration route with smart lifestyle matching, full transparency through a real-time *Adoption Tracker*, and a guided *Foster-to-Adopt* model, complemented by community volunteering and a solidarity wishlist of goods. By doing so, we maximize compatibility between families and animals, drastically reduce the risk of returns, and relieve associations of heavy manual workloads.

**Our main priority is giving these animals love and a better life.**

### Core Options

* **Adopt:** people look for the animal that best fits their home and family and adopt it; a temporary stay (*Foster-to-Adopt*) is possible before finalizing the decision, to ensure the fit is right.
* **Foster:** someone volunteers to provide housing and care for one or multiple animals for a period of time.
* **Care:** users volunteer to walk animals, feed them, clean them or take them to the vet.
* **Contribute:** associations can create lists of necessities regarding supplies so that people know what is necessary if they intend to make a donation.

---

## 2. Identified Real Pains (The Problem Space)

### On the Associations' and Shelters' Side
1. **Communication Chaos and Loss of History:** Applications and questions arrive simultaneously via WhatsApp, Instagram, email and isolated forms, causing data loss and duplicated effort.
2. **Reliance on Manual Spreadsheets:** Tracking of animal status (available, in foster care, adopted) and of volunteer schedules is done in shared Excel files with fragile access.
3. **Overload from Incompatible Screening:** Receiving applicants whose living conditions clash with the animal's needs, increasing the time spent on rejections.
4. **Disorganized Donation Collection:** Difficulty communicating the exact material needs of the moment (e.g., renal food, blankets in winter, milk replacer for litters).

### On the Citizens' and Adopters' Side
1. **The Application "Black Hole":** Submitting long forms without knowing whether they were received, are under review, or whether the animal has already been adopted.
2. **Adoptions Driven by Looks vs. Returns:** Choices made solely on appearance or a photo, without assessing routine or temperament, leading to painful returns.
3. **Fear of Immediate Commitment:** Willingness to adopt held back by fear that the animal won't adapt to the home, the children or other existing pets.
4. **Wanting to Help Without Being Able to Adopt:** People who want to help (walking dogs, playing with cats, donating food) but don't know where or how to offer themselves in a practical, low-bureaucracy way.

---

## 3. Actors & Roles

| Role | Description | Main Capabilities |
| :--- | :--- | :--- |
| **Visitor** | Unauthenticated user | Browse the catalog, view animal profiles and wishlists, take the Matchmaker quiz. |
| **Citizen (Registered User)** | Authenticated person | Submit and track adoption applications, request a Foster-to-Adopt period, pledge wishlist items. |
| **Volunteer** | Registered citizen with a volunteer profile | Sign up for walk/socialization slots and operational shifts (feeding, cleaning, vet transport). |
| **Foster Family** | Registered citizen with a fostering profile | Register fostering availability and conditions. |
| **Association Staff** | Member of a specific association | Manage that association's animals, applications, rosters, wishlist and payment settings. |
| **Platform Administrator** | Patas operator | Register and verify associations, moderate content. |

---

## 4. Platform Model (Multiple Associations)

* Patas is a **multi-association platform**: each association has its own space (animals, applications, volunteers, wishlist), and the public catalog aggregates animals from all verified associations.
* Each association's data is isolated: staff only see and manage their own association's records.
* New associations go through a **registration and verification** process by the Platform Administrator before publishing animals.
* **Single-association deployment:** the platform must remain deployable for a single association (e.g., an instance dedicated to one shelter) without structural changes.

---

## 5. Strategic Pillars & Ideas Repository

```
                                          ┌────────────────────────┐
                                          │     PATAS PLATFORM     │
                                          └───────────┬────────────┘
                                                      │
       ┌──────────────────┬──────────────────┬────────┴─────────┬──────────────────┐
       ▼                  ▼                  ▼                  ▼                  ▼
 [ 1. ADOPTION ]   [ 2. FOSTERING ]  [ 3. VOLUNTEERING ] [ 4. SOLIDARITY ]  [ 5. BACK-OFFICE ]
 • Dual Discovery  • Foster-to-Adopt • Walks             • Goods Wishlist   • Application Kanban
 • Real-Time       • Parametric      • Socialization     • Pledges &        • Animal Management
   Tracker           Foster Engine   • Operational Roster  Direct Delivery  • Volunteer Hub
```

---

### Pillar 1: Discovery & Responsible Adoption

* **Path 1 (Open Universal Catalog):**
  * Fast, unobstructed browsing of all registered animals across associations.
  * Clear filters: species, size, age, location, association, compatibility (children, other dogs, cats).
  * Rich animal profile: photos, age, size, temperament, compatibility (children, dogs, cats), story and required routine. These same attributes feed the catalog filters and the Matchmaker.

* **Path 2 (Optional Compatibility Algorithm, "Matchmaker"):**
  * Short lifestyle questionnaire: average time away from home, physical activity level, housing type and previous experience.
  * The system highlights animals with the highest behavioral affinity, explaining why (without blocking access to the remaining animals).
  * Visitors' answers are used only for the current session; for Citizens they are saved in an editable *Matchmaker Profile*, so recommendations improve as their lifestyle changes.
  * **The algorithm's design is intentionally left open at this stage** and will be detailed later. Envisioned direction: a swipe-based discovery experience ("Tinder-style") in which the user's choices refine future suggestions.

* **Adoption Tracker (End-to-End Transparency):**
  * Visual timeline for the applicant, in the style of parcel tracking (see the application state machine in [Section 6](#6-state-models)).
  * Notifications at every stage change, delivered **by email and in-app** (notification center within the platform), removing uncertainty and follow-up messages to the association.
  * The applicant always knows the outcome, including rejections and when the animal has been adopted by someone else.
  * The timeline is built from the application's status history, so every stage change is recorded with its date.

---

### Pillar 2: Flexible Temporary Fostering (Foster Care & Foster-to-Adopt)

* **Foster-to-Adopt (Optional Trial Period):**
  * An **optional stage** of the adoption application: the adopter may request a short trial period (e.g., 7 to 15 days) before finalizing the legal adoption.
  * **The adopter requests it; the association approves or declines it** for each application.
  * The association may set a **trial-period fee**, paid online through the platform (**Stripe, in test mode**, given the academic context of the project).
  * During the trial, the association follows up on the adaptation through the platform (check-ins, notes, trial end date), minimizing returns after definitive adoption.
  * The trial has its own lifecycle (`Requested → Approved → Active → Succeeded/Failed`, or `Declined`/`Cancelled`). The application only enters `Trial Period` once the trial is `Active` (approved and, if a fee applies, paid). If the trial is declined or cancelled, the application simply continues in `Interview` (e.g., toward a direct adoption). These lifecycles were in `StateMachines.md` (removed; see git history). The MVP pipeline is in [AdoptionPipeline](../domain/AdoptionPipeline.md).

* **Parametric Temporary Fostering Engine (Foster Families):**
  * Volunteer families register their availability with flexible parameters:
    * Capacity: accepted species, maximum size, number of simultaneous animals.
    * Physical conditions: house with garden, fenced yard, apartment with safety netting, available play space.
    * Time window: one-off fostering (weekend, other caregivers' holidays) or ongoing.
  * Associations can search foster families whose parameters match an animal's needs. Families already at their simultaneous capacity, or outside their time window, are excluded from results.
  * Assignment is a **proposal**: the family must accept before the animal's location changes to `Awaiting Pickup`. If the family declines, nothing changes for the animal.

---

### Pillar 3: Dynamic Volunteering and Socialization

* **Walking and Well-Being Sessions:**
  * Sign-up for time slots to walk dogs that spend the day in kennels, or for enrichment/socialization sessions with cats.
  * Sign-up **requires a simple registered account** (name, contact, acceptance of the volunteering terms), so that slots and responsibility can be managed.
  * Slot management per animal/shift, ensuring every animal gets its walk without overcrowding the facilities.

* **Operational Roster:**
  * Shifts for core facility tasks: feeding, cleaning enclosures, logistical support and transport to veterinary appointments.
  * Open to any registered volunteer, under the same simple-account requirement as walks.

---

### Pillar 4: Solidarity Wishlist and In-Kind Donations

* **Reverse Marketplace of Needs:**
  * The association publishes specific items currently needed, with a target quantity (e.g., *"10kg of gastrointestinal dry food"*, *"Fleece blankets for winter"*, *"Wet food for senior cats"*).
* **Pledges with Confirmation:**
  * The donor pledges any quantity of an item. Pledged quantities are shown publicly so other donors can see what is already committed.
  * There is **no hard limit** on pledges: an item stays open until the association decides it has enough and removes (closes) it from the list.
  * Each item has a soft **target quantity**. Targets block nothing; they drive a priority level (High, Medium, Low) based on how much of the target is already confirmed or pledged, and the wishlist is ordered by it.
  * The association confirms receipt, and only then is the received (confirmed) quantity updated. Pledges not fulfilled can be released by the association.
* **Donations Without Payment Intermediation:**
  * The user buys the items independently wherever they prefer and arranges the drop-off point/time or postal shipping. Wishlist donations do not go through the platform's payment system.

---

### Pillar 5: Association Management Cockpit (Back-Office)

* **Application Kanban Board:**
  * Column view by application state to move applications, add private screening notes and trigger automatic updates to the adopter.
* **Integrated Animal Management:**
  * Animal registration and editing, with the state model described in [Section 6](#6-state-models).
* **Volunteer and Roster Hub:**
  * Global view of attendance and active sign-ups per day and shift.
* **Foster-to-Adopt Settings:**
  * Approve/decline trial requests, define the trial fee and view payment status.

---

## 6. State Models

> **Normative source:** the detailed diagrams, transition rules and cross-machine synchronization lived in `StateMachines.md` (removed; see git history). This section summarizes them. The MVP adoption pipeline is in [AdoptionPipeline](../domain/AdoptionPipeline.md).
>
> **Decision recorded:** the original vision mixed temporary fostering and the adoption trial in a single animal state. Option B below (two independent dimensions) is adopted.
>
> | Option | Cohesion | Coupling | Testability | Maintainability |
> | :--- | :--- | :--- | :--- | :--- |
> | **A. Single state machine** (original: `Available → In Process → In Foster/Trial → Adopted`) | Low: one state mixes "where the animal is" with "how far its adoption has gone" | Fostering and adoption rules depend on each other | Fewer states, but cannot express "fostered and still available" | Every new location or process step multiplies the number of states |
> | **B. Two independent dimensions** (adoption status + location) | High: each dimension has a single responsibility | Fostering and adoption evolve independently | Each state machine can be tested in isolation; combinations need a few extra tests | New locations do not affect the adoption flow |
>
> Both options are compatible with the **State** pattern required by `AGENTS.md`; option B implies two state objects in the `Animal` aggregate instead of one.

### 6.1 Animal

**Adoption status** (`Deceased` is intentionally not modeled):

* `Available`: can receive applications.
* `Reserved`: one application has reached `Interview`; other open applications are put `On Hold`.
* `In Trial`: Foster-to-Adopt period is `Active`.
* `Adopted`: adoption completed. Not a terminal state: a later return moves the animal back to `Available`.
* `Unavailable`: temporarily not adoptable (medical, behavioral). Only reachable from `Available`; a reservation must be released first.

Transitions:

```
Available   ──► Reserved      (an application moves to Interview)
Available   ──► Unavailable   (medical/behavioral)      Unavailable ──► Available (recovered)
Reserved    ──► In Trial      (trial becomes Active)
Reserved    ──► Adopted       (direct adoption, no trial)
Reserved    ──► Available     (reserved application rejected/withdrawn)
In Trial    ──► Adopted       (trial succeeded)
In Trial    ──► Available     (trial failed / withdrawn, animal returned)
Adopted     ──► Available     (returned by owner)
```

**Location** (independent of adoption status): `At Shelter` | `Awaiting Pickup` | `In Foster Home` | `With Adopter` (during a trial and after adoption). A fostered animal can remain `Available` for adoption.

### 6.2 Adoption Application

```
Submitted ──► Screening ──► Interview ──► [Trial Period] ──► Completed
    │  ▲          │  ▲          │                │
    ▼  │          ▼  │          │                │
   On Hold ◄──────┘  │          │                │
   (animal reserved for another application; resumes when released)

Rejected | Withdrawn : from Submitted, Screening, On Hold, Interview, Trial Period
Closed               : from Submitted, Screening, On Hold (animal adopted by someone else)
```

* The animal becomes `Reserved` when an application moves to `Interview`; only one application can be in `Interview`/`Trial Period` per animal.
* `Trial Period` is optional (requested by the adopter, approved by the association, may require payment of the trial fee) and starts only when the trial is `Active`.
* If the reserved application is rejected or withdrawn, held applications resume.
* When the animal becomes `Adopted`, all remaining open applications move to `Closed`.
* Every transition triggers an email and in-app notification to the applicant.

### 6.3 Supporting state machines

Trial Period, Foster Assignment, Pledge and Association Verification were defined in `StateMachines.md` (removed; see git history).

---

## 7. Suggested Prioritization for the Agile Process (MVP vs. Evolution)

To ensure success within a 4-Sprint schedule (8 weeks of development), the broad vision is split into operational layers:

| Feature / Idea | MVP Priority (Sprints 1 to 4) | Next Increment / Future |
| :--- | :---: | :---: |
| **Authentication, Roles & Association Registration** | Essential (Sprint 1) | Advanced association verification |
| **Public Catalog with Filters** | Essential (Sprint 1) | None |
| **Back-Office: Animal & Status Management** | Essential (Sprint 1-2) | None |
| **Application Flow with Adoption Tracker (email + in-app)** | Essential (Sprint 2-3) | None |
| **Compatibility Algorithm / Quiz** | Differentiating Value (Sprint 3) | Swipe-based ("Tinder-style") discovery |
| **Foster-to-Adopt (optional trial + Stripe test payment)** | Differentiating Value (Sprint 4) | Extension to Multiple Foster Homes |
| **Walk Scheduling (registered volunteers)** | Optional (If Sprint 4 has slack) | Points Gamification |
| **Wishlist with Pledges & Confirmation** | Optional (Sprint 4 / Extension) | Integration with Local Stores |
| **Parametric Foster Family Engine** | Essential (sprint TBD, see Decision D1) | None |
| **Operational Roster (registered volunteers)** | Essential (sprint TBD, see Decision D1) | None |
| **Volunteer & Roster Hub (Back-Office)** | Essential (sprint TBD, see Decision D1) | None |

---

## 8. Out of Scope (MVP)

* Real (non-test) payment processing; Stripe is used in test mode only.
* Online monetary donations; the wishlist handles in-kind donations only.
* Detailed design of the Matchmaker algorithm (deferred, see Pillar 1).
* Native mobile applications.
* Legal adoption contracts and veterinary record management.
* Recording animal deaths (no `Deceased` state; the model focuses on actionable adoption states).

---

## 9. Non-Functional Requirements & Constraints

* **Data protection (GDPR):** applications contain personal and housing data; access is restricted to the applicant and the staff of the association concerned.
* **Data isolation:** each association only accesses its own data (see [Section 4](#4-platform-model-multiple-associations)).
* **Responsive web:** usable on mobile browsers.
* **Accessibility:** follow basic web accessibility guidelines.
* **Notifications:** email and in-app.
* **Payments:** Stripe in test mode; no real card data is processed.

---

## 10. Impact and Success Metrics

> The original metrics (zero unanswered applications, reduced return rates, volunteer growth) depend on real-world usage over long periods and cannot be measured within the project's timeframe. The metrics below can be verified during development and usability testing.

1. **Follow-Up Transparency:** 100% of application state changes generate a notification to the applicant; average time to first state change is visible to the association.
2. **Application Effort:** an applicant can find an animal and submit an application in a limited number of steps, validated in usability tests.
3. **Task Success:** association staff can complete core tasks (register an animal, move an application, approve a trial) in usability tests without assistance.
4. **Decision Quality (long term):** reduced return rates through the combination of the *Matchmaker* and the *Foster-to-Adopt* period, tracked by recording returns in the platform.
5. **Community Engagement (long term):** number of registered volunteers and fulfilled walk/socialization slots per association.

---

## 11. Related Documents

| Document | Purpose |
| :--- | :--- |
| [Glossary](../domain/Glossary.md) | Ubiquitous Language: exact names used in code and stories |
| [DomainModel](DomainModel.md) | Aggregates, entities and relationships |
| [AdoptionPipeline](../domain/AdoptionPipeline.md) | MVP adoption pipeline and lifecycles (proposed) |
| [PrototypeFlows_Fostering_Donations](PrototypeFlows_Fostering_Donations.md) | Happy paths for the Fostering and Wishlist prototype |

---


