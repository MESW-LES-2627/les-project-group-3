# AGENTS.md

> **Engineering Governance and AI Development Guidelines**
>
> **Context:** MESW — Software Engineering Laboratory (2026/27)
>
> **Product:** Patas — Collaborative Animal Protection Platform

---

## 1. Human-Agent Relationship and Decision-Making Principles

* **Architecture Decisions Belong to the Developer:**
  * The agent **must not make architectural decisions autonomously**.
  * The agent may suggest architectural alternatives, but must clearly explain the trade-offs (coupling, cohesion, testability, maintainability) and wait for explicit approval before proceeding.
* **Required Educational Explanation ("The Room Wins"):**
  * Any team member may be asked to individually defend the code during the in-person evaluation.
  * All agent-generated code must be clearly explained to the developer (except for trivial mechanical changes). If the team does not understand the generated code, it must not be added to the repository.
* **Traceability and AI Log:**
  * The use of AI must be auditable and documented.
  * Any hallucination, incorrect proposal, or agent failure that requires human intervention and correction must be flagged for recording in the `CLAIM.md` for the relevant iteration.

---

## 2. Modeling Paradigm and Design Patterns

* **Object-Oriented Design Is Mandatory:**
  * All system design must follow strict object-oriented programming (OOP) principles.
  * Encapsulate state, use polymorphism, maintain a clear separation of responsibilities (SRP), and build rich domain models.
  * Do not use anemic models with procedural logic scattered across services when the domain should encapsulate its own invariants.
* **Deliberate Use of Design Patterns:**
  * Use classic patterns (GoF) whenever there is a concrete functional justification:
    * **Strategy:** For interchangeable affinity-calculation algorithms in the *Matchmaker* and for triage policies.
    * **Factory / Abstract Factory:** For controlled instantiation of complex aggregates and foster-care types.
    * **State:** For formal finite state machines governing the animal lifecycle and the *Adoption Tracker*.
    * **Observer:** For domain events and notifications decoupled from state transitions.
  * Avoid *overengineering*: each pattern introduced must solve a concrete extensibility or coupling problem.

---

## 3. Specification-Focused Testing Strategy

* **Specification-Driven Testing:**
  * Tests must verify specification contracts, domain invariants, and concrete business rules.
  * Do not inflate the test suite merely to increase raw test counts or meaningless coverage metrics.
* **Ability to Catch Real Failures:**
  * Every test must be capable of failing when the expected behavior regresses. Avoid tests based exclusively on mocks of internal implementation details.
* **Functional Vertical Slices:**
  * Code and tests must validate vertical slices that run from user input through to the persistence layer.

---

## 4. Quality, Tooling, and Linters

* **Compliance with Linters and Formatters Is Mandatory:**
  * All code must pass the project's configured linters and static analysis tools with no outstanding warnings.
  * Do not suppress static analysis rules without a well-founded technical justification.
* **Automation and Continuous Integration (CI):**
  * The specification test suite and linters must pass 100% in the CI pipeline before any merge.

---

## 5. Prohibited Practices (Red Lines)

1. **Dead Demos:** Do not build isolated interfaces or visual mockups backed by static data that are not connected to the logic and data model.
2. **Friday Dumps:** Do not accumulate massive changes without an incremental commit history. The version history must reflect progress distributed over time.
3. **Opaque / Unexplained Code:** Code whose purpose or operation is not understood by the developer must not be submitted.
4. **Violation of the Definition of Done:** A feature is not considered complete if it cannot be run from the tag for its iteration (`iter-N`).

## 6. Business Communication and Design Documentation

* **Prior Alignment on Business Logic:**
  * Any significant business logic decision, triage rule, or domain validation must **be communicated to and aligned with the team before it is decided or implemented**.
  * Developers and agents must not unilaterally assume or change business workflows without team validation.
* **Architecture and Modeling Decisions Must Be Documented:**
  * All structural architectural decisions (adopted patterns, aggregate design, API contracts, and entity models) must be formally documented in the repository (e.g., Architecture Decision Records / ADRs or notes in the technical documentation).
  * The goal is to ensure transparency, consistency, and shared technical understanding across the team.
  