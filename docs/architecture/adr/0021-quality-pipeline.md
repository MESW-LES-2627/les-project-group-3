# ADR 0021: Quality pipeline

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-11-13 |
| **Scope** | Tasks #82 and #83: tests, coverage, mutation, audit, deploy and the metrics report |
| **Related** | [0018-test-layout](0018-test-layout.md), [Testing policy](../../process/TESTING.md) |

## Context

CI ran the tests and the linters, but nothing said what the tests are for, no number
said how much of the logic they reach, the frontend had no tests, and the deploy
(`sync.yml`) ran in parallel with CI and pushed `main` even when CI was red.

## Decisions

1. **A written policy.** [`docs/process/TESTING.md`](../../process/TESTING.md) is the
   one place that says what each kind of test covers, what is not tested and why, what
   is measured and at which levels.
2. **Frontend logic is tested with Vitest**, version 4: the 5.x line needs Node 22 and
   CI uses Node 20. The tests live in `patas-frontend/tests/unit/lib` and replace only
   the network and the sign-in boundary. Screens and components stay manual.
3. **Measure code with logic, by branch coverage.** A table of options adds lines but
   no branches, so branches are the headline number. The scope of each side is listed
   in the policy.
4. **The levels live in `quality.json`.** CI, the report and the policy read the same
   numbers, so they cannot drift apart.
5. **Two gates.** The coverage of the lines a pull request changes (`diff-cover`, on
   pull requests) and a floor on the branch coverage of each side
   (`scripts/quality/gate.py`). A missing report fails the gate; it never reads as a
   pass.
6. **Mutation testing (`mutmut`) on the domain.** Only unit tests run, and repositories
   are left out because integration tests cover them. The score is reported and never
   blocks, but a run that tried no mutants fails. `mutmut` does not run on Windows, so
   it is installed by the CI job and is not a project dependency.
7. **A dependency audit** of the production dependencies of both sides (`pip-audit`,
   `pnpm audit`).
8. **One pipeline, one chain.** The deploy is a job of `ci.yml` with `needs` on the
   quality gate and the audit, so it runs on the commit that was tested and does not run
   when anything is red. `sync.yml` is removed.
9. **A metrics report with one row per merge** (`scripts/quality/report.py`), served by
   GitHub Pages from a `gh-pages` branch that CI writes, for `staging` and `main`,
   backend and frontend side by side. What could not be measured is `n/d`, never `0`.
10. **Pull requests go to `staging`, then `staging` to `main`.** CI runs on both.

## Alternatives not taken

* **Codecov or SonarCloud.** They give coverage history, but not the test count, the
  mutation score or the same scope in one place, they need an app installed in the
  organisation, and the numbers would depend on an outside service.
* **Only a job summary.** No fixed link and no history.
* **The report in a `METRICS.md` on `main`.** Every merge would commit to `main` and run
  CI again.
* **Deploy by `workflow_run` on the old `sync.yml`.** More fragile, and the link to the
  tested commit is less obvious than `needs`.

## Pending team agreement

`AGENTS.md` section 6 asks for decisions shared by the team to be agreed before they are
implemented. These are proposals until the team accepts them:

* the levels: 90 % of the changed lines and an 85 % branch floor;
* the audit thresholds: any known vulnerability in the backend, high or above in the
  frontend;
* the scope, which includes `routers/` and `auth/` on the backend;
* rows for both `staging` and `main`.

## Consequences

* A pull request that touches logic without tests fails CI.
* A new advisory can turn a build red without a code change.
* Only an administrator can make a green CI a condition to merge (a repository rule).
* The first run after a merge creates the `gh-pages` branch; Pages is enabled once, in
  the repository settings.
* The deploy job moves a token and an account that belong to someone else, so it cannot
  be tried from a branch. The `if` keeps it from running outside `main`.
