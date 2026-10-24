# Architecture Decision Record: Database Design & Baseline Schema

> **Document:** Architecture and Relational Modeling Decision Record
> **Context:** MESW, Software Engineering Laboratory (2026/27)
> **Product:** Patas, Collaborative Animal Welfare Platform
> **Related File:** [create.sql](create.sql)

---

## 1. Context and Motivation

The Patas project defined its domain model in [DomainModel](DomainModel.md) and the lifecycle state machines in `StateMachines.md` (removed), with the terminology fixed in [Glossary](../domain/Glossary.md) and the scope in [Vision](Vision.md).
To support backend API development (FastAPI / SQLAlchemy / Alembic) and maintain compliance with the governance guidelines in [AGENTS](../../AGENTS.md), it was necessary to consolidate, optimize, and critically audit the initial relational database schema (PostgreSQL 16).

This document formalizes the architectural decisions made collaboratively by the team. Decisions 1 to 6 correspond to the initial version of the schema; Decisions 7 to 11 result from the **alignment review** with the corrected version of the domain documents (new states, entities, and rules) and the script validation in a PostgreSQL 16 instance.

---

## 2. Architectural Decisions

### Decision 1: Repositioning and Consolidation of SQL Scripts
* **Decision:** The `database/` folder was moved outside the backend to reside at the repository root (`/database`), and the previously fragmented scripts (`schema.sql`, `indexes.sql`, `triggers.sql`) were unified into a single canonical and self-sufficient file: [create.sql](create.sql).
* **Justification:**
  * Decouples the pure relational specification from the backend framework implementation.
  * Adopts the academic reference pattern (LBAW/FEUP), allowing the complete end-to-end schema to be created in a single sequential execution.
  * Isolates all tables and types in a dedicated `patas` schema (`DROP SCHEMA IF EXISTS patas CASCADE; CREATE SCHEMA patas; SET search_path TO patas;`), ensuring clean *namespacing* and future compatibility with Alembic (`version_table_schema = 'patas'`).

---

### Decision 2: Strict Timestamps Policy (`created_at` and `updated_at`)
* **Decision:** Limit the presence of `created_at` and `updated_at` exclusively to entities that have real functional lifecycle or audit value.
* **Mapping:**
  * **Keep `created_at` and `updated_at`:**
    * `associations`: Creation and updates of institutional / verification data.
    * `users`: Account registration and profile update.
    * `animals`: Entry into the shelter and state / adoption transitions.
    * `wishlist_items`: Creation of the need and updates to the target and state (active / closed).
    * `foster_assignments`: Moment of proposal and assignment transitions (accepted, active, completed...).
  * **Special Cases:**
    * `adoption_applications`: Uses `submitted_at` (ubiquitous domain language for the submission moment) and `updated_at` for state machine transitions.
    * `trial_periods`: Keeps only `updated_at`. By gaining its own lifecycle (`requested`, `approved`, `active`...), it needed to record the moment of the last transition; the period dates remain explicit in `start_date` and `end_date`.
    * `matchmaker_profiles`: Keeps only `updated_at` to assess the "freshness" of preferences in the affinity calculation.
    * `pledges`: Keeps only `created_at` (donation commitment date).
    * `association_memberships`: Keeps only `created_at` (static record of joining the staff; has no editable attributes).
    * `notifications`: Keeps `created_at` and `read_at` (moment it was viewed in the application).
  * **Immutable *append-only* tables (a single event timestamp):**
    * `trial_check_ins`: `logged_at`.
    * `application_status_changes`: `changed_at`.
    * `application_notes`: `created_at`.
  * **No Timestamps:**
    * `volunteer_profiles` and `foster_profiles`: Accessory profiles 1:1 coupled to the `User` lifecycle.
* **Impact:** Only **8 triggers** `BEFORE UPDATE` for `updated_at` (the original 6, plus `foster_assignments` and `trial_periods`), eliminating unnecessary RDBMS processing in the remaining tables.

---

### Decision 3: Index Strategy and HOT (Heap-Only Tuples) Optimization
* **Decision:** Remove indexes on mutable columns and delegate foreign key indexes to the ORM / Alembic.
* **Technical Justification:**
  * **Preservation of HOT Updates:** In PostgreSQL, updating an indexed column forces an index rewrite and prevents *Heap-Only Tuples*. By eliminating indexes on columns like `adoption_status`, `location`, `status`, and `pledge_status`, **animal and application state transitions produce HOT updates with zero writes to secondary indexes**.
  * **Omission of Manual FK Indexes:** Alembic / SQLAlchemy will generate relational indexes on foreign keys during model generation, avoiding duplication in the baseline script.
  * **Case-Insensitive Uniqueness:** Kept the functional index `idx_users_email_lower` (`UNIQUE ON users (lower(email))`) to support fast authentication and shield the business rule against uppercase/lowercase duplicates.
* **Conscious Exception:** The partial unique indexes that guarantee domain invariants (Decisions 4 and 8) have a predicate on `status`, so transitions that **enter or exit** this predicate are no longer HOT. This cost is accepted because these transitions are rare (entering an interview, starting a foster period) and the integrity guarantee compensates for it.

---

### Decision 4: Uniqueness Rule in Adoption Applications
* **Decision:** Implementation of a **Partial Unique Index** on `adoption_applications`:
  ```sql
  CREATE UNIQUE INDEX idx_adoption_applications_one_open_per_applicant_animal
      ON adoption_applications (applicant_id, animal_id)
      WHERE status NOT IN ('completed', 'rejected', 'withdrawn', 'closed');
  ```
* **Analyzed Trade-off:**
  * A table constraint `UNIQUE (applicant_id, animal_id)` would forever prevent a citizen from submitting a new application for the same animal, even after a past rejection or withdrawal.
  * The partial index fulfills the domain invariant: **at most 1 active application simultaneously**, allowing new attempts if the previous process has ended.
* **Note:** The new state `on_hold` is not terminal, so it still counts as an active application.

---

### Decision 5: Full-Text Search (GIN) and Matchmaker Support
* **Decision:** Add the `description text` column to `animals` and create a `GIN` index for vectorial textual search in Portuguese.
* **Implementation:**
  * `tsvectors` column indexed with weights: Name (A), Species (B), and Description (C).
  * **Optimized Trigger against Write Amplification:**
    ```sql
    IF (NEW.name <> OLD.name OR NEW.species <> OLD.species OR NEW.description IS DISTINCT FROM OLD.description) THEN
        NEW.tsvectors = ...;
    END IF;
    ```
    Operational updates to `adoption_status`, `location`, or `updated_at` **do not recalculate `tsvectors` nor touch the GIN index**.
* **Alignment with the Matchmaker:**
  * The free text `description` column accommodates behavioral notes from the shelter without requiring dozens of sparse and rigid columns in the database.
  * An application service layer in the backend (*Write-Time Parser* / NLP) will process this text to feed the *Matchmaker* affinity algorithms.
* **Complement (alignment review):** The catalog requires filters by size, age, and compatibility (see [Vision](Vision.md), Pillar 1). While `age_in_months`, `size`, `temperament`, and `photos` are explicit relational columns, multi-dimensional compatibility and behavioral criteria are consolidated into an extensible native `compatibility jsonb` column indexed with GIN (see Decision 12).

---

### Decision 6: Member Governance and Data Types
* **Staff Members (`association_memberships`):** Maintained as a pure N:M relationship without a `role` column. All association members share the same privileges for the MVP scope. This corresponds to the `StaffProfile` of the domain model and is what enforces data isolation between associations.
* **Platform Administrator:** Represented by `users.is_platform_admin` (the `AdminRole` in the domain model).
* **Enumerated Types (`ENUM`):** Preserved as native PostgreSQL types (`CREATE TYPE ... AS ENUM`) to ensure strong integrity at the relational engine's data catalog level.

---

### Decision 7: Alignment with State Machines
* **Decision:** Enumerated types and state columns now exactly reflect `StateMachines.md` (removed).
* **Changes:**

| Element | Change | Origin |
| :--- | :--- | :--- |
| `verification_status` | New value `suspended` | Machine 7 (Association Verification) |
| `animal_location` | New values `awaiting_pickup` and `with_adopter` | Machine 2 (Location) |
| `application_status` | New value `on_hold` | Machine 3 (Application) |
| `application_status_changes` | Tracks status history (eliminates redundant `previous_status` column) | Machine 3 |
| `trial_periods.status` | New column `trial_status` (`requested`, `approved`, `active`, `succeeded`, `failed`, `declined`, `cancelled`) | Machine 4 (Trial) |
| `trial_periods.outcome_notes` | Free-form notes/outcome details upon completion or failure | Machine 4 |
| `trial_periods.start_date / end_date` | Defined when the trial becomes `active` | Machine 4 |
| `trial_periods.payment_reference` | New column for payment reference (e.g., Stripe test mode) | Vision, Pillar 2 |
| `associations.default_trial_fee` | Default fee, copied to `trial_periods.fee_amount` upon approval | DomainModel, decision 5 |
| `foster_assignments` | New table with `foster_assignment_status` (`proposed`, `accepted`, `active`, `completed`, `declined`, `cancelled`) | Machine 5 (Foster Assignment) |
| `matchmaker_profiles.experience` | New column `experience_level` (previous experience) | Vision, Pillar 1 |
| `foster_profiles` | Now stores `accepted_species`, `max_size`, `max_simultaneous_animals`, availability window (`available_from`, `available_until`, `NULL` = continuous), and `is_active` | Vision, Pillar 2; DomainModel |

* **Integrity rules in `CHECK`:** `end_date >= start_date`; non-negative fees.

---

### Decision 8: Concurrency Invariants Guaranteed by Partial Indexes
* **Decision:** Domain reservation and concurrency rules are guaranteed by the RDBMS through partial unique indexes, while cross-dimension status synchronization (`adoption_status` vs. `location`) is managed by the application/domain aggregate layer.
* **Implementation:**
  * **Partial unique index** `idx_adoption_applications_one_reserving_per_animal`: at most **one** application per animal in `interview` or `trial_period` (reservation rule).
  * **Partial unique index** `idx_foster_assignments_one_open_per_animal`: at most **one** foster assignment in `proposed`, `accepted`, or `active` per animal.
* **Rationale for Domain Layer Synchronization:** Physical shelter operations often involve handoff delays (e.g. animal marked adopted before physical pickup, or adopted while in foster care). Enforcing a rigid boolean 1:1 check in SQL would abort realistic transactions. Hence, lifecycle orchestration is encapsulated in domain aggregates and service handlers rather than rigid relational CHECK constraints.

---

### Decision 9: Wishlist without Hard Limits, with Target and Derived Priority
* **Decision:** `wishlist_items.needed_quantity` was replaced by `target_quantity` (**indicative** target) and the `status` column (`active` / `closed`) was added.
* **Justification:**
  * As long as an item is on the list, any quantity can be pledged: **no restriction limits the sum of `pledges`**. The association removes the item from the list (`closed`) when it considers it has enough.
  * The target serves only to sort by relevance, not to block.
* **Derived quantities, never stored:** the `wishlist_item_progress` view calculates `confirmed_quantity`, `pledged_quantity`, `committed_quantity`, `remaining_to_target`, `coverage` (committed divided by the target), and `priority`:

| Priority | Coverage |
| :--- | :--- |
| `high` | below 50% |
| `medium` | from 50% up to below 100% |
| `low` | 100% or more (remains listed and accepting pledges until closed) |

* **Open point:** the thresholds (50% and 100%) and the possibility of manual priority are recorded as Decision D6 in [Vision](Vision.md).

---

### Decision 10: Application History, Private Notes, and Notifications
* **Decision:** Three tables support explicit requirements from the Vision:
  * **`application_status_changes`** (*append-only*): state history (`from_status` is `NULL` on initial submission). It is the source for the *Adoption Tracker* timeline and avoids redundant status columns.
  * **`application_notes`** (*append-only*): generalized private staff notes across the application lifecycle (screening, interview, trial follow-ups), never exposed to the applicant.
  * **`notifications`**: in-app notifications created by domain events, with `read_at`.
* **Justification:** Essential for the *Adoption Tracker* and internal association auditability without cluttering the core application aggregate.

---

### Decision 11: Defect Fix in `volunteer_profiles` `CHECK`
* **Problem:** The previous version of the script **did not execute**: PostgreSQL rejects subqueries in `CHECK` constraints (`ERROR: cannot use subquery in check constraint`), and `volunteer_profiles_preferences_not_blank_check` used `NOT EXISTS (SELECT ... FROM unnest(...))`.
* **Decision:** The validation was moved to the `IMMUTABLE` function `text_array_has_no_blank(text[])`, used by `volunteer_profiles.preferences` and `animals.photos`.
* **Verification:** The complete script was executed in PostgreSQL 16 without errors, and the constraints, partial indexes, the view, full-text search, and the 8 triggers were tested with valid and invalid inserts.

---

### Decision 12: Extensible Compatibility Profile via Native JSONB and GIN Indexing (`jsonb_path_ops`)
* **Decision:** Replace static compatibility boolean columns (`good_with_children`, `good_with_dogs`, `good_with_cats`) on `animals` with an extensible native `compatibility jsonb NOT NULL DEFAULT '{}'::jsonb` column, accompanied by a structural object check constraint (`CHECK (jsonb_typeof(compatibility) = 'object')`) and indexed with a dedicated GIN index using native `jsonb_path_ops`.
* **Technical Justification:**
  * **Schema Evolution & Migration Independence:** In agile development and ongoing algorithmic tuning, the matching engine continually introduces new behavioral traits (e.g., `needs_yard`, `energy_level`, `barking_tendency`, `experience_needed`, `house_trained`, `good_with_birds`, `time_alone_tolerance`, `bonded_pair`). Modeling these as rigid relational columns forces disruptive database migrations and schema churn at every iteration.
  * **Rich Domain Model & Value Object Pattern (AGENTS.md Compliance):** In strict Domain-Driven Design and OOP, compatibility is not an independent entity with relational identity; it is a multi-dimensional `CompatibilityProfile` **Value Object** within the `Animal` Aggregate Root (matching `+Compatibility compatibility` in [DomainModel](DomainModel.md)). Relational identity and state machine dimensions (`adoption_status`, `location`, `association_id`) remain strictly normalized, while the behavioral profile is encapsulated.
  * **Native PostgreSQL 16 Performance (`jsonb_path_ops` & Containment `@>`):** Both `jsonb` and `jsonb_path_ops` are 100% native PostgreSQL core features requiring zero external extensions. The `jsonb_path_ops` operator class builds compact hash-based GIN index entries that support top-speed containment queries:
    ```sql
    -- Fast index scan for catalog and matching:
    SELECT * FROM animals WHERE compatibility @> '{"good_with_cats": true, "needs_yard": true}';
    ```
  * **Structural Integrity (Two-Tier Validation):** Relational integrity is enforced at the database level via `jsonb_typeof(compatibility) = 'object'`, while fine-grained attribute typing, enum constraints, and defaults are governed cleanly by application-layer Value Objects (Pydantic schemas in FastAPI).

---

## 3. Domain Model and Schema Mapping

| Domain Model ([DomainModel](DomainModel.md)) | Table |
| :--- | :--- |
| `User` | `users` |
| `MatchmakerProfile` | `matchmaker_profiles` |
| `VolunteerProfile` | `volunteer_profiles` |
| `FosterProfile` | `foster_profiles` |
| `StaffProfile` | `association_memberships` |
| `AdminRole` | `users.is_platform_admin` |
| `Association` | `associations` |
| `Animal` | `animals` |
| `FosterAssignment` | `foster_assignments` |
| `AdoptionApplication` | `adoption_applications` |
| `StatusChange` | `application_status_changes` |
| `InternalNote` | `application_notes` |
| `TrialPeriod` | `trial_periods` |
| `CheckIn` | `trial_check_ins` |
| `WishlistItem` | `wishlist_items` (+ `wishlist_item_progress` view) |
| `Pledge` | `pledges` |
| `Notification` | `notifications` |

---

## 4. Rules Left to the Application Layer

These rules are **not** in the schema, as they depend on context that the RDBMS cannot see or events between aggregates:

* Only `verified` associations can publish animals and wishlist items.
* `closed` items reject new pledges (existing ones can be confirmed or released).
* Validity of transitions for each state machine (State pattern, with domain exceptions).
* Reactions between aggregates via domain events (e.g., an application entering `interview` reserves the animal and places the remaining ones `on_hold`).
* Capacity and availability window of foster families in the parametric engine search.
* Data isolation by association (filtering by `association_memberships`).

---

## 5. Current State of Files

* Executable master script: [create.sql](create.sql)
* Conceptual domain document: [DomainModel](DomainModel.md)
* Lifecycle and state machines: `StateMachines.md` (removed)
* Terminology: [Glossary](../domain/Glossary.md)
* Vision and open decisions: [Vision](Vision.md)