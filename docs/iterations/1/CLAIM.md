# CLAIM: Iteration 1

Group 3, Patas. Iteration 1 — Move.
Every link below points at the tag `iter-1`, so nothing needs hunting.

## Links

| Item | Link |
| :-- | :-- |
| Tag | [iter-1](https://github.com/MESW-LES-2627/les-project-group-3/tree/iter-1) |
| Compare with the last tag | [`iter-0...iter-1`](https://github.com/MESW-LES-2627/les-project-group-3/compare/iter-0...iter-1) |
| Production | [les-project-group-3-deploy.vercel.app](https://les-project-group-3-deploy.vercel.app) |
| Pipeline | [CI status of the tagged commit](https://github.com/MESW-LES-2627/les-project-group-3/commit/iter-1). Workflow: [ci.yml](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-1/.github/workflows/ci.yml) |
| Stories in this increment | [Iteration 1 milestone](https://github.com/MESW-LES-2627/les-project-group-3/milestone/2) |
| Retrospective | [Retrospective](#retrospective) |
| AI log | [AI log](#ai-log) |

## AI log

Failures of the AI agent that needed human intervention (AGENTS.md §1).

| Date | Who | What the AI got wrong | How it was caught | Fix |
| :-- | :-- | :-- | :-- | :-- |
| 2026-11-01 | ammp102 | When `Push to Deploy Repo` failed with 403 (`denied to github-actions[bot]`), the AI repeatedly blamed missing fine-grained PAT scopes and secret naming (`DEPLOY_TOKEN` vs `DEPLOY_PAT`) instead of `actions/checkout@v4` persisting `GITHUB_TOKEN` in `.git/config`. Also gave a Bash-only `read -p` prompt that failed in macOS `zsh`. | Re-running the workflow after verifying token scopes and debug logs (`secrets.DEPLOY_TOKEN` evaluated to `'***'`) still failed with 403; running `read -rsp` in `zsh` threw `read: -p: no coprocess`. | Added `persist-credentials: false` to `actions/checkout@v4`, authenticated with `ammp102:$DEPLOY_PAT`, and pushed `HEAD:main` in the deploy sync workflow. |
| 2026-10-30 | frutastontas | In the strict mode design for the compatibility score, a blank owner answer counted 0.25 and became the weakest link, so one skipped field could cap an otherwise perfect animal, and an animal with nothing answered scored 6. | Checking the formula against a worked example before writing the strict strategy; the choice was put to the developer. | The weakest link now ignores blank answers; they cost only through the average. |
| 2026-11-01 | frutastontas | Added three fields to `AnimalMatchProfile` without updating the animal response model, and reported the suite as passing while `tests/auth` cannot run on the host (an OpenSSL crash), so the failure stayed hidden until the endpoint task. | A guard test failed in the container run. | Exposed the fields in the response and updated the two expected objects; the whole suite now runs in the container. |
| 2026-11-01 | frutastontas | Created three board issues nobody asked for (#48 to #50) when a script half-ran, then said nothing else had been created without checking. | The developer interrupted, and the issue list showed them. | Closed as not planned (deleting needs a repo admin); the text of any board change is now shown first. |
| 2026-11-03 | MatviiSukFEUP | For US-03 the AI wrote overly long comments, docstrings and docs (such as ADR 0014) that restated the code or repeated each other, adding text to keep up to date and making the code harder to maintain. | Reviewing the staged commit before committing it. | Cut the comments to the non-obvious reasons only, made docstrings one line like the surrounding code, and shortened ADR 0014. |
