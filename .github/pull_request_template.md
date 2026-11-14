## Story

<!-- Link or title of the user story, and the target iteration (iter-N). -->

## Summary

<!-- What changed and why, in a few sentences. -->

## Definition of Done

Full definition: [`docs/process/DEFINITION_OF_DONE.md`](../docs/process/DEFINITION_OF_DONE.md).
Tick an item only when its evidence is linked or written below it. If an item does not apply, say which one and why.

### Before
- [ ] **0. Target branch:** This PR targets `staging` (not `main`), unless it is a release PR promoting staging to production.
- [ ] **1. Acceptance criteria** are testable and listed here:
  <!-- list them -->
- [ ] **2. Business logic was agreed with the team beforehand:**
  <!-- link to the decision (doc, ADR, message) or "no business logic changed" -->

### Automatic
- [ ] **3. Specification tests** cover each acceptance criterion and at least one is a vertical slice (entry to persistence):
  <!-- criterion -> test name -->
- [ ] **4. Linters and static analysis** pass with no warnings or unjustified suppressions
- [ ] **5. CI is fully green:** <!-- link to the CI run -->

### Human
- [ ] **6. Design patterns** introduced are each justified in one line:
  <!-- pattern -> problem it solves, or "none introduced" -->
- [ ] **7. Structural decisions** are documented:
  <!-- link to ADR / technical note, or "no structural decisions" -->
- [ ] **8. A teammate other than the author approved the decisions** (business, logic, architecture):
  <!-- reviewer and where approval is recorded -->
- [ ] **9. The author can explain the feature and its design.** Reviewer's "why" question and the answer:
  <!-- Q: ...  A: ... -->
- [ ] **10. AI errors that needed human correction** are flagged for `CLAIM.md`:
  <!-- entry reference, or "none" -->

### Delivery
- [ ] **11. Commit history is incremental** (no single massive commit)
- [ ] **12. Runs on `iter-N`** with real data and persistence. Demo steps:
  <!-- numbered steps someone else can follow -->
