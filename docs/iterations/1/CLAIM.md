# CLAIM: Iteration 1

Group 3, Patas. Iteration 1.  
Every repository link below points at the tag `iter-1`, so nothing needs hunting.

## Links

| Item | Link |
| :-- | :-- |
| Tag | [iter-1](https://github.com/MESW-LES-2627/les-project-group-3/tree/iter-1) |
| Compare with the last tag | [`iter-0...iter-1`](https://github.com/MESW-LES-2627/les-project-group-3/compare/iter-0...iter-1) |
| Production | [les-project-group-3-deploy.vercel.app](https://les-project-group-3-deploy.vercel.app) |
| Staging | None |
| Pipeline | [CI status of the tagged commit](https://github.com/MESW-LES-2627/les-project-group-3/commit/iter-1). Workflow: [ci.yml](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-1/.github/workflows/ci.yml) |
| MVP | [MVP](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-1/docs/product/MVP.md) |
| Vision | [Product vision](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-1/docs/archive/Vision.md) |
| Stories in this increment | [Iteration 1 milestone](https://github.com/MESW-LES-2627/les-project-group-3/milestone/2) |
| How to run the tests | [Running tests and checks](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-1/README.md#running-tests-and-checks) |
| Board snapshots | [Start](../../screenshots/Iteration-1-Board-Start.png) · [End](../../screenshots/Iteration-1-Board-End.png) |
| Retrospective | [Retrospective](#retrospective) |
| AI log | [AI log](#ai-log) |

## Features delivered

The decisions below describe the iteration's implemented scope.

| Feature | User stories / acceptance tests | What was added | Architecture decision |
| :-- | :-- | :-- | :-- |
| Shared navigation and catalog presentation | Supporting UI for [US-02: See an animal's profile](https://github.com/MESW-LES-2627/les-project-group-3/issues/17) and [US-09: See and edit my profile](https://github.com/MESW-LES-2627/les-project-group-3/issues/24). | A shared, session-aware header; login, registration and logout navigation; and a clearer catalog that continues to render live backend data. | [ADR 0007](../../architecture/adr/0007-ui-improvements.md) |
| Saved Matchmaker profile | [US-08: Save my Matchmaker profile](https://github.com/MESW-LES-2627/les-project-group-3/issues/23); [AT-07: Save and update my Matchmaker profile](https://github.com/MESW-LES-2627/les-project-group-3/issues/31); [AT-08: The Matchmaker profile is private](https://github.com/MESW-LES-2627/les-project-group-3/issues/32). | Registered users can view, save, replace and delete their household and lifestyle answers through a profile page with a live summary and explicit validation. | [ADR 0008](../../architecture/adr/0008-matchmaker-profile.md), [ADR 0009](../../architecture/adr/0009-matchmaker-profile-page.md) |
| Detailed animal descriptions | [US-01: Describe my animal in detail](https://github.com/MESW-LES-2627/les-project-group-3/issues/16); [US-07: Describe how my animal lives with others](https://github.com/MESW-LES-2627/les-project-group-3/issues/22); [AT-01: Publish a fully described animal](https://github.com/MESW-LES-2627/les-project-group-3/issues/25); [AT-02: Invalid data is rejected on publish](https://github.com/MESW-LES-2627/les-project-group-3/issues/26). | Publishing supports optional animal profile and care details, including compatibility, activity, care needs and free-text notes; unanswered optional fields do not prevent publishing. | [ADR 0010](../../architecture/adr/0010-animal-profile-fields.md) |
| Comparable animal match profile | [US-07: Describe how my animal lives with others](https://github.com/MESW-LES-2627/les-project-group-3/issues/22); supports [US-10: See how well an animal fits my home](https://github.com/MESW-LES-2627/les-project-group-3/issues/39). | A derived profile translates animal details to the Matchmaker scales and is included in animal API responses; no duplicate profile is stored. | [ADR 0011](../../architecture/adr/0011-animal-match-profile.md) |
| Owner animal management | [US-04: See all my animals](https://github.com/MESW-LES-2627/les-project-group-3/issues/19); [US-05: Unpublish my animal](https://github.com/MESW-LES-2627/les-project-group-3/issues/20); [AT-04: Only the owner manages an animal](https://github.com/MESW-LES-2627/les-project-group-3/issues/28); [AT-05: An unpublished animal disappears from public view](https://github.com/MESW-LES-2627/les-project-group-3/issues/29). | Owners can list their published and unpublished animals and unpublish their own listings; unpublished animals are excluded from public listings and details. | [ADR 0012](../../architecture/adr/0012-owner-animals-and-unpublishing.md) |
| Compatibility results | [US-10: See how well an animal fits my home](https://github.com/MESW-LES-2627/les-project-group-3/issues/39); [AT-10: The animal page shows my fit and why](https://github.com/MESW-LES-2627/les-project-group-3/issues/40); [AT-11: I can choose how strict the match is](https://github.com/MESW-LES-2627/les-project-group-3/issues/41). | Signed-in users with a Matchmaker profile can calculate a loose or strict fit for an animal and see the score with reasoned results; explicit household safety conflicts can exclude a match. | [ADR 0013](../../architecture/adr/0013-compatibility-scoring.md) |
| Edit an animal | [US-03: Edit my animal](https://github.com/MESW-LES-2627/les-project-group-3/issues/18); [AT-03: Edits show up in the profile and the filters](https://github.com/MESW-LES-2627/les-project-group-3/issues/27); [AT-04: Only the owner manages an animal](https://github.com/MESW-LES-2627/les-project-group-3/issues/28). | Owners can load and replace their animal's listing details, including unpublished animals; ownership is checked and editing does not republish a listing. | [ADR 0014](../../architecture/adr/0014-editing-an-animal.md) |
| Public animal profile and publisher name | [US-02: See an animal's profile](https://github.com/MESW-LES-2627/les-project-group-3/issues/17); [US-09: See and edit my profile](https://github.com/MESW-LES-2627/les-project-group-3/issues/24); [AT-09: Change my display name](https://github.com/MESW-LES-2627/les-project-group-3/issues/33). | Visitors can view an animal's detailed profile and current publisher display name; users can update their display name, and unpublished listings remain unavailable publicly. | [ADR 0015](../../architecture/adr/0015-public-animal-profile-page.md) |
| Catalog filters and district | [US-06: Filter the catalog](https://github.com/MESW-LES-2627/les-project-group-3/issues/21); [AT-06: Catalog filters combine](https://github.com/MESW-LES-2627/les-project-group-3/issues/30); also supports the edit behavior in [AT-03](https://github.com/MESW-LES-2627/les-project-group-3/issues/27). | Visitors can filter by species, size, age group and district. Filter values remain in the URL so results can be shared and restored with browser navigation. | [ADR 0016](../../architecture/adr/0016-catalog-filters.md) |

## Retrospective

### What we did well

* We recorded decisions alongside the user-story work: ADRs 0007–0016 make
  responsibilities, API choices and unresolved assumptions traceable.
* We defined the scope early, then divided and assigned the work to fit each
  member's schedule.
* We defined tests and test cases at the start of the sprint and aligned them
  with the planned features.

### What we'll do differently

* **Plan dependencies and ownership before parallel work starts.** Several
  features depended on one another, so parts of the team had to wait for a
  teammate's work to finish. We'll identify and sequence those dependencies
  earlier.
* **Verify frontend changes in a browser, not only through builds.** A passing
  lint, typecheck and build did not catch missing generated styles; include a
  browser check in UI review.
* **Agree on business assumptions before treating them as policy.** The
  matching translations and scoring values recorded in ADRs 0011 and 0013 when 
  the PR was created were assumptions or placeholders that still needed team agreement.

### Puzzles

These are discussion topics, not blockers or requests to change delivered
features:

* How should the matchmaking algorith evolve? Is the current implementation enough or will we have to tweak it in the future when new animal attributes or user fields are though and added?
* How will the adoption pipeline work, and how should it integrate with the
  matching features developed in this iteration?
* How should we prevent frontend and backend copies of enum values and display
  labels from drifting apart?


## AI log

Failures of the AI agent that needed human intervention (AGENTS.md §1).

| Date | Who | Model | What the AI got wrong | How it was caught | Fix |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 2026-11-01 | ammp102 | Claude (fable 5.1) | When `Push to Deploy Repo` failed with 403 (`denied to github-actions[bot]`), the AI repeatedly blamed missing fine-grained PAT scopes and secret naming (`DEPLOY_TOKEN` vs `DEPLOY_PAT`) instead of `actions/checkout@v4` persisting `GITHUB_TOKEN` in `.git/config`. Also gave a Bash-only `read -p` prompt that failed in macOS `zsh`. | Re-running the workflow after verifying token scopes and debug logs (`secrets.DEPLOY_TOKEN` evaluated to `'***'`) still failed with 403; running `read -rsp` in `zsh` threw `read: -p: no coprocess`. | Added `persist-credentials: false` to `actions/checkout@v4`, authenticated with `ammp102:$DEPLOY_PAT`, and pushed `HEAD:main` in the deploy sync workflow. |
| 2026-10-30 | frutastontas | Claude (fable 5.1)  | In the strict mode design for the compatibility score, a blank owner answer counted 0.25 and became the weakest link, so one skipped field could cap an otherwise perfect animal, and an animal with nothing answered scored 6. | Checking the formula against a worked example before writing the strict strategy; the choice was put to the developer. | The weakest link now ignores blank answers; they cost only through the average. |
| 2026-11-01 | frutastontas | Claude (opus 5.5)  | Added three fields to `AnimalMatchProfile` without updating the animal response model, and reported the suite as passing while `tests/auth` cannot run on the host (an OpenSSL crash), so the failure stayed hidden until the endpoint task. | A guard test failed in the container run. | Exposed the fields in the response and updated the two expected objects; the whole suite now runs in the container. |
| 2026-11-01 | frutastontas | OpenAI GPT-6 | Created three board issues nobody asked for (#48 to #50) when a script half-ran, then said nothing else had been created without checking. | The developer interrupted, and the issue list showed them. | Closed as not planned (deleting needs a repo admin); the text of any board change is now shown first. |
| 2026-11-03 | MatviiSukFEUP | Claude (fable 5.1)  | For US-03 the AI wrote overly long comments, docstrings and docs (such as ADR 0014) that restated the code or repeated each other, adding text to keep up to date and making the code harder to maintain. | Reviewing the staged commit before committing it. | Cut the comments to the non-obvious reasons only, made docstrings one line like the surrounding code, and shortened ADR 0014. |
| 2026-10-27 | diogo-febra-ferreira | vscode copilot (gpt-6-luna) | While brainstorming possible animal details, the AI misunderstood what people look for when adopting an animal and suggested less useful details, such as time spent at a shelter or food preferences. | Reviewing the suggestions against the information relevant to choosing an animal to adopt. | Refocused the discussion on adoption-relevant information and did not carry those suggestions forward as feature requirements. |
