# CLAIM: Iteration 0

Group 3, Patas. Vertical prototype: publish an animal and see it in the catalog.
Every link below points at the tag `iter-0`, so nothing needs hunting.

## Links

| Item | Link |
| :-- | :-- |
| Tag | [iter-0](https://github.com/MESW-LES-2627/les-project-group-3/tree/iter-0) |
| Compare with the last tag | First iteration, there is no earlier tag. [Whole history, root commit to `iter-0`](https://github.com/MESW-LES-2627/les-project-group-3/compare/d351ee989d0994d681ae3ee7a82112b6d49183b1...iter-0) |
| Production | TODO: production URL |
| Staging | TODO: staging URL, or "none" and why |
| Pipeline | [CI status of the tagged commit](https://github.com/MESW-LES-2627/les-project-group-3/commit/iter-0). Workflow: [ci.yml](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/.github/workflows/ci.yml) |
| MVP | [MVP Vision](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/product/MVPVision.md) |
| Vision | [Vision](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/product/Vision.md) |
| Stories in this increment | [Iteration 0 milestone](https://github.com/MESW-LES-2627/les-project-group-3/milestone/1) (issues, PRs and ADRs). Acceptance criteria on the tag: [AC1 to AC5](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/integrations/vertical-prototype/VerticalPrototypeSpec.md#22-acceptance-criteria-dod-1) |
| How to run the tests | [Running tests and checks](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/README.md#running-tests-and-checks) |
| Retrospective | [Retrospective](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/iterations/0/CLAIM.md#retrospective) |
| AI log | [AI log](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/iterations/0/CLAIM.md#ai-log) |

## What runs on this tag

The slice of [the vertical prototype spec](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/integrations/vertical-prototype/VerticalPrototypeSpec.md):
a person registers and logs in, publishes an animal, and the animal appears in the
public catalog, read from PostgreSQL with the publisher recorded as owner.

| Story | Criterion |
| :-- | :-- |
| AC1 | A logged-in user publishes a valid animal; it is in `GET /animals` with that user as owner and status `available`. |
| AC2 | A request without a valid JWT is rejected with 401 and nothing is stored. |
| AC3 | An invalid animal (blank name, negative age) is rejected by the domain and nothing is stored. |
| AC4 | The first authenticated call creates the user's row; a second call does not duplicate it. |
| AC5 | The catalog is public: a visitor without login sees the published animals. |

Demo steps someone else can follow: [README, publish an animal and see it in the catalog](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/README.md#demo-publish-an-animal-and-see-it-in-the-catalog).

## Team artefacts

| Artefact | Link |
| :-- | :-- |
| Architecture Decision Records | [0001 authentication](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/architecture/adr/0001-authentication.md) · [0002 deployment](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/architecture/adr/0002-deployment-and-runtime-architecture.md) · [0003 pnpm](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/architecture/adr/0003-frontend-package-management-pnpm.md) · [0004 animal aggregate](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/architecture/adr/0004-animal-aggregate.md) · [0005 fetch animal data](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/architecture/adr/0005-fetch-animal-data.md) · [0006 application services](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/architecture/adr/0006-application-services.md) |
| Definition of Done | [DEFINITION_OF_DONE.md](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/process/DEFINITION_OF_DONE.md) |
| Pull request template | [pull_request_template.md](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/.github/pull_request_template.md) |
| Engineering rules and AI guidelines | [AGENTS.md](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/AGENTS.md) |
| Domain Model | [DomainModel.md](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/domain/DomainModel.md) |
| State Machines | [StateMachines.md](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/domain/StateMachines.md) |
| Glossary | [Glossary.md](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/domain/Glossary.md) |

## Known gaps

* The domain documents and `database/create.sql` still describe the full Vision
  (associations, fostering). The MVP changes are listed in
  [MVP Vision §13](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/product/MVPVision.md#13-impact-on-existing-documents).

## Retrospective

**What went well**

* The slice runs end to end: register, login, JWT verified by FastAPI through JWKS,
  domain rules, PostgreSQL, catalog UI. Six ADRs record the decisions.
* CI runs ruff, pytest, eslint, tsc and the production build.
* The history is incremental: 8 active days with small commits (the busiest day,
  2026-10-16, had 19).

**What hurt**

* Two animal backends were built in parallel (PR #3 and `feat/animals-vertical-slice`).
  Merging them cost a day, and the decisions were aligned afterwards (AGENTS.md §6).
* CI took five commits to stabilise on 2026-10-17 (pnpm version, lockfile cache,
  permissions, database URL).
* Neon SSL took three attempts on 2026-10-21.
* Toolchain surprises: a Python 3.15 alpha broke the SQLAlchemy import (pinned to 3.12),
  Avast broke Docker builds on Windows, and `OPENSSL_Applink` crashes some local tests.
* Documents drifted from the code: the spec said DRAFT, DoD numbers were stale, and
  the domain documents still describe the full Vision.

**Proposed changes (pending team agreement)**

* Agree who owns which layer before coding starts.
* Fill the PR template's AI-errors item (#10) in each PR, not at the end.
* Pin toolchain versions on day one.
* Open a draft PR so CI runs before merging.
* Update docs in the same PR as the code.

## AI log

Failures of the AI agent that needed human intervention (AGENTS.md §1).

| Date | Who | What the AI got wrong | How it was caught | Fix |
| :-- | :-- | :-- | :-- | :-- |
| 2026-10-17 | frutastontas | Assumed that an invalid enum value sent through asyncpg surfaces as SQLAlchemy `DataError`. It surfaces as the generic `DBAPIError`. | Running the test; it failed. | Test now expects `DBAPIError` and matches the reason ([`test_animals_migration.py`](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/patas-backend/tests/test_animals_migration.py), commit `29336ed`). |
| 2026-10-16 | frutastontas | The auth research (§4) proposed configuring Better-Auth with a `schema: "patas_auth"` option. Better-Auth has no such option. | Checked against the Better-Auth docs while implementing auth. | Schema isolation is done through the connection `search_path` ([ADR 0001](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/architecture/adr/0001-authentication.md)). |
| 2026-10-21 | apinho | The first attempt at asyncpg SSL for Neon (`e572c14`) rewrote `database.py` and dropped `AsyncSessionLocal` and `get_db`. `routers/health.py` imports `get_db`, so the backend would not have started. | Redone on a new branch 3 minutes later (12:44 to 12:47). The first branch never reached `main`. | `699f2e5`, merged in PR #5. `b737499` restores the missing trailing newline. |
| 2026-10-19 | diogo-febra-ferreira | When first adding animal fetching from the database, the AI assumed the data came from `create.sql` rather than the migrations, and suggested a dozen nonexistent tables instead of the three that existed. | Reviewing the response and comparing it with the existing database | Specified the data source in queries. |
