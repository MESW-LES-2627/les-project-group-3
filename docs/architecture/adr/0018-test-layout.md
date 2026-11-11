# ADR 0018: Test layout

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-11-10 |
| **Scope** | Test layout task (#79), backend tests |
| **Related** | [0017-adoption-base](0017-adoption-base.md) (decision 10, tests start from a factory) |

## Context

Backend tests grew into folders named after what they were first written for:
`tests/auth` held endpoint tests for animals and the Matchmaker, `tests/models` mixed
pure domain tests with repository tests that need a database, and `tests/adoption`
held integration tests. Acceptance tests (`test_at_NN_...`) sat inside endpoint files
beside tests that are not acceptance tests. There was no way to run only the tests
that need no database, and CI ran everything as one step.

## Decisions

1. **The folder is the kind of test.** `tests/unit` needs no database, network or app.
   `tests/integration` uses something real: a database, a socket or the app, so
   repositories, use cases, migrations and endpoint tests live there. `tests/acceptance`
   holds the acceptance tests of the board. Inside `unit`, folders follow
   `src/patas_backend`.
2. **One file per acceptance test**, named after it: `test_at_16_send_a_request_to_adopt.py`
   for AT-16 (#70). A story's done-when says "`test_at_NN_...` passes in CI", and now
   there is one file to point at in a pull request.
3. **The marker comes from the folder.** `tests/conftest.py` marks each test `unit`,
   `integration` or `acceptance`, and refuses to collect a test outside the three
   folders. A marker written by hand can be forgotten or wrong; a path cannot.
   `--strict-markers` is on, so a misspelt marker is an error.
4. **Shared helpers live in `tests/support`**, which is on pytest's `pythonpath`: the
   token issuer, the adoption factory, and the helper modules that an acceptance file
   and its endpoint file share. Fixtures that every kind needs (`engine`, `client`,
   `issuer`) are in `tests/conftest.py`; the others sit next to the tests that use
   them.
5. **CI runs the three kinds as three steps** in the same job, so a red step says which
   kind failed. The total is the same as the single step it replaces.
6. **No test changed.** The move kept every test function identical: 334 functions, 605
   collected tests, compared by syntax tree before and after. Only locations, imports,
   conftests and two paths to `alembic.ini` changed.

## Alternatives not taken

* **Markers only, files where they were.** The smallest change, but a file's place
  would keep saying nothing about what it needs, and a forgotten marker would put a
  test in the wrong kind.
* **Folders per feature, then per kind** (`tests/adoption/unit`, and so on). It fits
  the vertical slices, but each folder would need its own copy of the fixtures, and
  running every acceptance test would still need markers.

## Pending team agreement

`AGENTS.md` section 6 asks for decisions shared by the team to be agreed before they
are implemented. The convention above is a proposal until the team accepts it: where a
new test goes, and that every acceptance test gets its own file.

## Consequences

* (+) `uv run pytest tests/unit` runs in seconds and needs no database.
* (+) Each AT is one file, found by its number, and runs alone with `-k at_16`.
* (−) A helper imported by several files lives in `tests/support` with its original
  private names (`_as`, `_publish`). Renaming them to public names would touch test
  bodies and was left for later.
* (−) Iteration 1's acceptance tests AT-01 to AT-06, AT-09 and AT-12 have no test
  named `test_at_NN`. Some of their rules may be covered under other names; this task
  did not look for them.
* (−) The three CI steps share one database, so they cannot run in parallel. Separate
  jobs would need a database each.
