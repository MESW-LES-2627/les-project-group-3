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
| 2026-11-03 | MatviiSukFEUP | For US-03 the AI wrote overly long comments, docstrings and docs (such as ADR 0013) that restated the code or repeated each other, adding text to keep up to date and making the code harder to maintain. | Reviewing the staged commit before committing it. | Cut the comments to the non-obvious reasons only, made docstrings one line like the surrounding code, and shortened ADR 0013. |
