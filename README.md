# Patas: Collaborative Animal Welfare Platform

MESW, Software Engineering Laboratory (2026/27), Group 3.

## Vision

> Patas is a collaborative web platform that centralizes and simplifies the entire
> animal care and adoption cycle, for people looking to adopt, foster or care for
> animals and for the associations that protect them.

The long-term vision rests on four options: **Adopt** (with smart lifestyle matching
and an optional Foster-to-Adopt trial), **Foster** (families hosting animals for a
period), **Care** (volunteers walking, feeding and transporting animals) and
**Contribute** (a wishlist of supplies associations need). Applicants follow their
process in real time through the **Adoption Tracker**, ending the "black hole" of
unanswered applications.

Full document: [Product Vision](docs/product/Vision.md).

## MVP Vision: what we had to let go

Eight weeks (4 sprints) cannot deliver the full vision, so the MVP pivots to a
**peer-to-peer adoption marketplace**: any registered user can publish animals they
need to rehome, and anyone can find and adopt one. We kept what answers the adopter's
main pains and cut everything that depended on associations.

| Let go | Why | Returns with |
| :-- | :-- | :-- |
| Associations: registration, verification, staff roles, data isolation | An animal's owner is now a `User` (MD1–MD3). Abstractions for associations would solve a problem the MVP no longer has, and the later migration is cheap. | Associations increment |
| Fostering: foster family engine and the animal location state machine | Without fostering, location is fully derived from adoption status. A separate machine would allow contradictory states (MD4). | Fostering increment |
| Volunteering: walks, operational roster, volunteer hub | Needs associations or facilities to organize shifts. | Volunteering increment |
| Solidarity wishlist and pledges | Needs the association concept to limit abuse. | Wishlist increment |
| Trial fee and Stripe payments | The trial stays, approved by the owner, but with no fee. | Trial fee increment |
| Kanban board for applications | Replaced by a simpler owner's application list. | — |

**What stays:** authentication, public catalog with filters, adoption applications with
their full state machine, Adoption Tracker, in-app and email notifications, the
Matchmaker, and the Foster-to-Adopt trial. **New in the MVP:** moderation (reporting
listings and users), because no organization stands behind a listing anymore.

Full document: [MVP Vision](docs/product/MVPVision.md).

## Documentation

### Product

| Document | What it covers |
| :-- | :-- |
| [Vision](docs/product/Vision.md) | Long-term product vision, pillars, actors and state models |
| [MVP Vision](docs/product/MVPVision.md) | Scope pivot, MVP feature set and sprint plan |
| [Prototype flows: fostering and donations](docs/product/PrototypeFlows_Fostering_Donations.md) | Happy paths for post-MVP modules |

### Domain

| Document | What it covers |
| :-- | :-- |
| [Domain Model](docs/domain/DomainModel.md) | Aggregates, entities and relationships |
| [State Machines](docs/domain/StateMachines.md) | Lifecycles and cross-machine rules |
| [Glossary](docs/domain/Glossary.md) | Ubiquitous language used in code and stories |

> The domain documents and the database design still describe the full Vision
> (associations, fostering). The MVP changes are listed in
> [MVP Vision §13](docs/product/MVPVision.md#13-impact-on-existing-documents).

### Architecture

| Document | What it covers |
| :-- | :-- |
| [Architecture Decision Records](docs/architecture/adr/) | One record per structural decision (authentication, deployment, aggregates, API, services) |
| [Database Design Decisions](docs/architecture/DatabaseDesignDecisions.md) | Baseline schema decisions |

### Research

| Document | What it covers |
| :-- | :-- |
| [Authentication research](docs/research/AuthenticationResearch.md) | Spike that led to the authentication ADR |
| [Matching algorithms](docs/research/MatchingAlgorithms.md) | Matchmaker design (Strategy pattern) |

### Process and Iteration 0

| Document | What it covers |
| :-- | :-- |
| [Definition of Done](docs/process/DEFINITION_OF_DONE.md) | When a story counts as done |
| [Pull request template](.github/pull_request_template.md) | DoD evidence checklist for every PR |
| [AGENTS.md](AGENTS.md) | Engineering rules and AI usage guidelines |
| [Vertical prototype spec](docs/integrations/vertical-prototype/VerticalPrototypeSpec.md) | Iteration 0 slice: publish an animal, see it in the catalog |
| [Demo steps](#demo-publish-an-animal-and-see-it-in-the-catalog) | How to run the Iteration 0 demo |
| [CI workflow](.github/workflows/ci.yml) | Linters and tests on every PR |

## Run the application with Docker Compose

Docker Compose runs PostgreSQL, the FastAPI backend, and the Next.js frontend. You do
not need to install Python, `uv`, Node.js, or pnpm on your machine.

### Prerequisites

- Docker Engine with the Docker Compose v2 plugin
- Ports `3000`, `5433`, and `8000` available on your machine

Run all commands below from the repository root, where `docker-compose.yml` is located.

### Configure the development environment (optional)

Compose has development defaults for the database credentials and authentication
secrets, so the application can be started without a local environment file. These
defaults are for local development only and must not be used in a deployed environment.

To override them, create a `.env` file in the repository root. For example:

```dotenv
POSTGRES_USER=patas_admin
POSTGRES_PASSWORD=choose-a-local-password
POSTGRES_DB=patas_db
JWT_SECRET=replace-with-a-long-random-secret
BETTER_AUTH_SECRET=replace-with-a-different-long-random-secret
BETTER_AUTH_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:3000
```

Keep the database password consistent with any other service configuration you add.
Compose reads this file automatically. The root `.env` is ignored by Git; never commit
production secrets.

### First-time setup

> **Upgrading an existing checkout?** Older setups created the database from
> `database/create.sql`, and an earlier `0003` migration created a different animal
> table. Both are incompatible with the current migrations: reset the local
> database once with `docker compose down -v` (this deletes local data).

1. Start PostgreSQL and wait for its health check:

   ```sh
   docker compose up -d db
   docker compose ps
   ```

   PostgreSQL is available to tools on your machine at `localhost:5433`. Containers
   connect to it using the Compose service name `db`. Alembic owns the application
   schema and creates it in the next step; `database/create.sql` is retained as a
   reference and is not run by Compose.

2. Apply the backend's Alembic migrations. These create/update the domain tables and
   the `patas_auth` schema used by Better Auth:

   ```sh
   docker compose run --build --rm backend alembic upgrade head
   ```

3. Create or update Better Auth's tables in `patas_auth`:

   ```sh
   docker compose run --build --rm frontend-migrate
   ```

   This one-off service is built from the frontend's migrator Docker target. It uses
   `pnpm dlx` to download and run the `auth` CLI, so the container needs internet access
   when the migration runs. The migrator uses Node 22 for CLI compatibility; this does
   not change the Node version used by the frontend. It is separate from the web
   frontend, so it does not run every time the app starts.

4. Build and start the backend and frontend:

   ```sh
   docker compose up --build -d backend frontend
   docker compose ps
   ```

   The frontend is on port `3000`, the backend API is on port `8000`, and
   PostgreSQL is published on port `5433`.

### Demo: publish an animal and see it in the catalog

1. Open <https://les-project-group-3-deploy.vercel.app>. Visitors land on the public catalog (`/animals`).
2. Create an account at `/register`; you are taken back to the catalog, which now
   shows **Publish an animal**.
3. Publish an animal (name, species, optional age). It appears in the catalog as
   `available`, owned by you. A blank name is rejected by the backend's domain and
   nothing is stored.
4. Log out (clear the site cookies) and reload: the animal is still listed.

Optional: `pnpm seed:demo` (in `patas-frontend`, with the stack running) fills the
catalog with sample animals published by three demo users through the application.
Their password is printed by the script and is for local use only.

`pnpm smoke:auth` (in `patas-frontend`, with the stack running) checks the same
handoff automatically.

### Applying migrations after updates

When a backend or frontend change adds a database migration, run the corresponding
command from the repository root before restarting the application:

```sh
docker compose run --build --rm backend alembic upgrade head
docker compose run --build --rm frontend-migrate
docker compose up --build -d backend frontend
```

The backend migration command is safe to run when there are no new migrations. Run
the frontend migration command when Better Auth's schema or dependencies have changed.

### Running tests and checks

The backend test suite uses PostgreSQL. Start the Compose database from the repository
root, then install the backend's development dependencies and run the tests:

```sh
docker compose up -d db
cd patas-backend
uv sync --group dev
uv run pytest
```

The tests create and reset a separate `patas_test` database, so the configured database
user must be allowed to create databases. To run the backend linter as well:

```sh
uv run ruff check .
```

### Logs and stopping the application

```sh
docker compose logs -f backend frontend db
docker compose down
```

`docker compose down` preserves the PostgreSQL data volume. To intentionally delete
the local database and all its data as well, use `docker compose down -v`.
