# Retrospective

### What we did well

* **We divided the work better** and made implementations more independent of other team members' work.
* **We added Fibonacci work estimates** to the issues, to attempt to distribute and plan the work in a more efficient way.
* **We updated the vision** to follow the expected Vision Board, to keep the development focused on what we want the application to be.

* **We built a quality pipeline** that enforces standards and integrated it into the pull request process.
* **We matched tests to the work.** Each acceptance test has its own file, and CI runs them as separate steps so failures are immediately identifiable. We also linked them in Github for easy identification with their respective user stories.

### What we'll do differently

* **We left a lot of work** for the final stretch of the sprint, making a lot of PRs at the same time.
* **Alembic migrations were out of order** due to the removing of postal code in one story and the matchmaking swipe in another, causing merge conflicts, we might need to be more specific on how we check what depends on other features, not just grouping by features.
* **We had some CI problems**, as the CI/CD is in constant improvement, but should be stable now for the next iterations.

### Puzzles

* **How should the Matchmaker feed evolve?** The current batch-local ranking (ADR 0026) works for discovery, but as the catalog grows, should we move to a persistent score cache or a recommendation engine?
* **How do we prevent frontend and backend enum drift?** Status labels are mirrored by hand in `lib/adoption-status.ts` (ADR 0017, decision 9). Should we generate the frontend labels from the backend enums, or accept the manual sync with a type check?
* **How do we handle rate limiting?** The public username check endpoint (ADR 0024, decision 5) and the swipe feed (ADR 0026) are unbounded. When do we add rate limiting, and what are the thresholds?