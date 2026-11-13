# Testing policy

> **Document:** What we test, what we measure, and what we do when the build is red
> **Context:** MESW, Software Engineering Laboratory (2026/27)
> **Product:** Patas, Collaborative Animal Welfare Platform

Levels marked **(proposed)** are not agreed with the team yet. The pipeline reads them
from one place (see [Where the levels live](#where-the-levels-live)), so changing one
is a one-line change.

## What a test is for

A test checks behaviour that can break: a rule, a decision, or the mapping between what
the backend says and what a person sees. A test that only restates a table or a label is
not written, and is not counted.

## Kinds of test

| Kind | Covers | Where | Needs |
| :-- | :-- | :-- | :-- |
| Unit (backend) | Domain rules and use cases, with no I/O | `patas-backend/tests/unit` | nothing |
| Integration (backend) | Repositories, migrations, endpoints, races | `patas-backend/tests/integration` | PostgreSQL |
| Acceptance (backend) | One file per acceptance test (AT) of the board, through HTTP | `patas-backend/tests/acceptance` | PostgreSQL |
| Frontend | API helpers, form checks, data mapping | `patas-frontend/tests/unit/lib` | nothing |

How to run each one is in the [README](../../README.md#running-tests-and-checks).

## What we deliberately do not test

| Not tested | Why |
| :-- | :-- |
| Screens and components | They are checked by hand by a teammate who did not write them (Definition of Done, item 8). A browser test would be slow and would break on layout, not on behaviour. |
| Option tables, labels and wording | They are data. A test would repeat the file it checks and could only fail when someone edits the data on purpose. |
| Wiring with no rule of our own | App start-up, the database session, the Better Auth client, the health endpoint, the environment lookup. |
| Generated code and getters | Nothing in them can break on its own. |

Migrations **are** tested (they apply from scratch on a real database), but they are not
part of the coverage figure because they hold no branches to measure.

## What is measured

Only code with logic is measured.

| Side | Measured | Left out |
| :-- | :-- | :-- |
| Backend | `models/`, `services/`, `routers/`, `auth/` | `main.py`, `database.py`, `config.py`, `routers/health.py`, `alembic/` |
| Frontend | `src/lib` | `auth.ts`, `auth-client.ts`, `backend.ts` |

The headline number is **branch coverage**. Lines and statements are reported too, but a
table of options adds lines and no branches, so branches say less about filler and more
about decisions that are actually taken.

Coverage says what ran, not what was checked. For that, **mutation testing** runs on the
domain (`models/`): it changes the code on purpose and counts how many changes the tests
notice.

## Levels

| What | Level | Effect |
| :-- | :-- | :-- |
| Lines changed in a pull request | at least 90 % covered **(proposed)** | CI fails below it |
| Whole project, branch coverage | at least 85 % **(proposed)** | CI fails below it |
| Mutation score on `models/` | reported | does not block |

Both sides, backend and frontend, are held to the same levels.

## Where the levels live

In one file, `quality.json`, at the root of the repository. The CI jobs, the report and
this page all use it, so they cannot drift apart.

## Where to see the numbers

- **On a pull request:** the coverage of the lines it changes, backend and frontend, in
  the run summary.
- **For the whole project:** one page at a fixed link, with one row per merge so tests can
  be seen arriving with the changes. Backend and frontend sit side by side: number of
  tests, branch coverage, coverage of the changed lines and mutation score.

## When the build is red

- Nobody merges, and the deploy does not run.
- Whoever broke it fixes it, or reverts the change, before starting anything else.
- A failing test is never skipped, loosened or deleted to get green. If the rule changed,
  the test changes with it and the pull request says why.
- A flaky test counts as a failure: it is fixed, or removed with a note, never rerun until
  it passes.
- Merging is blocked while the build is red by a repository rule that requires the CI
  checks; only an administrator can change that rule.
