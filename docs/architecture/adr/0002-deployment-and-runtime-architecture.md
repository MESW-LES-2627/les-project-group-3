# ADR 002: Deployment, Containerization, and Runtime Architecture

## Status
Accepted

## Context
For the Software Engineering Lab course, the application must be accessible 24/7 for evaluation without unpredictable downtime or cold-start delays. Additionally, schema updates and database migrations need to run seamlessly and automatically to prevent runtime version mismatches between the frontend and backend.

## Decision
1. **Container Orchestration:** Standardized on Docker Compose running PostgreSQL 16, FastAPI (Python 3.12 managed via Astral `uv`), and Next.js 16 (Node 20 in standalone mode).
2. **Automatic Migrations:** Database migrations are automatically executed upon application startup via FastAPI's lifespan event hook, ensuring the schema stays up-to-date across local, testing, and production (Render/Docker) environments without manual shell intervention.
3. **Quality Gates:** GitHub Actions automatically enforces Ruff linting/formatting and Pytest (with automated database setup/migrations) against an ephemeral PostgreSQL service for the backend, alongside ESLint, TypeScript typecheck, and standalone builds for the frontend.
4. **Continuous Availability:** Backend and database run on an always-on virtual server (eliminating PaaS cold starts), while the frontend is deployed with preview environments on Vercel.

## Consequences
- **Positive:** Deterministic local and production deployments; self-healing database schemas on boot eliminate runtime 500 errors caused by missing columns/tables; pull requests are blocked if tests, typing, or linting fail.
- **Negative:** Build-time environment variables (`NEXT_PUBLIC_API_URL`) must be explicitly declared during Docker image creation.