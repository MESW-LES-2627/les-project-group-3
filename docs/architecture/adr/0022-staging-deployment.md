# ADR 0022: Staging deployment and branch promotion flow

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-11-14 |
| **Scope** | Task #84: Staging deployment environment and CI/CD flow |
| **Related** | [0002-deployment-and-runtime-architecture](0002-deployment-and-runtime-architecture.md), [0021-quality-pipeline](0021-quality-pipeline.md) |

## Context

Features were previously merged directly into `main` and deployed straight to production. This lacked a safe environment to test database migrations, frontend-backend integration, and storage in a deployed context before exposing them to users. We need a staging environment that mirrors production and a promotion flow that guarantees only verified code reaches users.

## Decisions

1. **Strict Branch Promotion Flow:** All feature branches must target the `staging` branch. Production releases happen strictly by opening a pull request from `staging` into `main`. Direct feature merges to `main` are prohibited.
2. **Infrastructure Duplication:** The staging environment operates on completely independent infrastructure from production to ensure data safety:
   * **Database (Neon):** A separate Neon project (or isolated branch) for the staging Postgres database.
   * **Backend (Render):** A separate Render Web Service connected to the staging database.
   * **Frontend (Vercel):** A staging deployment on Vercel connected to the staging backend API.
3. **Automated Deployment via GitHub Actions:** The `ci.yml` deploy job pushes the repository state to a deployment mirror repository. The workflow dynamically pushes the tested commit to the deploy repository's `staging` branch (triggering the staging build) or `main` branch (triggering the production build), depending on the origin of the push.
4. **Deploy Gate:** As defined in ADR 0021, a deploy to staging only occurs if the CI quality gate (linters, typechecks, specification tests) passes successfully.
5. **PR Template Enforcement:** The pull request template includes a mandatory checkbox reminding developers to target `staging` for all standard features.

## Consequences

* **Positive:** Developers can manually verify features and migrations in a live cloud environment before they affect users.
* **Positive:** The production database is shielded from experimental migrations or broken API contracts.
* **Negative:** The team must maintain dual environment variables (secrets, DB URLs) across Vercel and Render.
* **Negative:** Releasing a feature now takes two pull requests (Feature $\rightarrow$ Staging, then Staging $\rightarrow$ Main).