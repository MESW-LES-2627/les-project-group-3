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

Full document (archived, not maintained): [Product Vision](docs/archive/Vision.md).

## MVP

The MVP is a **peer-to-peer adoption platform**: anyone can publish an animal for
adoption, and anyone can find one that fits their home with the **Matchmaker** and adopt
it through a conversation with the owner, from the first message to the handover, all
inside the platform. Applicants follow every request in the **Adoption Tracker**.

Full feature list: [MVP](docs/product/MVP.md).

## Documentation

### Product

| Document | What it covers |
| :-- | :-- |
| [MVP](docs/product/MVP.md) | Features the application will have |

### Domain

| Document | What it covers |
| :-- | :-- |
| [Adoption Pipeline](docs/domain/AdoptionPipeline.md) | Adoption application and animal status lifecycles, chat and handover (proposed) |
| [Glossary](docs/domain/Glossary.md) | Ubiquitous language used in code and stories |

### Architecture

| Document | What it covers |
| :-- | :-- |
| [Architecture Decision Records](docs/architecture/adr/) | One record per structural decision (authentication, deployment, aggregates, API, services) |
| [OOD deliverables](docs/design/) | Class diagram, component diagram and event storming |
| [Testing policy](docs/process/TESTING.md) | What each kind of test covers, what is measured, the levels, and what to do when the build is red |

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
| [Vertical prototype spec](docs/iterations/0/VerticalPrototypeSpec.md) | Iteration 0 slice: publish an animal, see it in the catalog |
| [Demo steps](#demo-publish-an-animal-and-see-it-in-the-catalog) | How to run the Iteration 0 demo |
| [CI workflow](.github/workflows/ci.yml) | Linters, tests, coverage gates, mutation, dependency audit and deploy ([ADR 0021](docs/architecture/adr/0021-quality-pipeline.md)) |

### Archive

[docs/archive](docs/archive/) keeps the documents written for the long-term Vision
(product vision, domain model, database design, fostering and donation flows). They are
no longer maintained.

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
   schema and creates it in the next step; the old `create.sql` baseline is archived
   in `docs/archive/` and is not run by Compose.

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

1. Open <http://localhost:3000>. Visitors land on the public catalog (`/animals`).
2. Create an account at `/register`; you are taken back to the catalog, which now
   shows **Publish an animal**.
3. Publish an animal (name, species, optional age). It appears in the catalog as
   `available`, owned by you. A blank name is rejected by the backend's domain and
   nothing is stored.
4. Log out (clear the site cookies) and reload: the animal is still listed.

Optional: `pnpm seed:demo` (in `patas-frontend`, with the stack running) fills the
catalog with sample animals published by three demo users through the application.
Their password is printed by the script and is for local use only.

Then `docker compose exec backend python scripts/seed_applications.py` adds sample
adoption requests in every state (open, accepted, declined, withdrawn, closed,
adopted) on top of those animals. It is safe to run again.

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
user must be allowed to create databases.

Tests are grouped by what they check, and the folder a test lives in is its kind:

| Folder | What it covers | Needs the database |
| :-- | :-- | :-- |
| `tests/unit` | Domain rules and pure logic | No |
| `tests/integration` | Repositories, use cases, migrations and endpoints | Yes |
| `tests/acceptance` | One file per acceptance test (AT) of the board, through HTTP | Yes |

```sh
uv run pytest tests/unit                    # fast, no database
uv run pytest -m acceptance                 # every AT
uv run pytest tests/acceptance -k at_16     # one AT
```

Helpers shared by several kinds of test live in `tests/support`. To run the backend
linter as well:

```sh
uv run ruff check .
```

The frontend tests cover its logic (API helpers, form checks, data mapping) and need no
browser or database. They live in `patas-frontend/tests/unit/lib`, one file per file of
`src/lib`. Screens and components are checked by hand.

```sh
cd patas-frontend
pnpm install
pnpm test                # run the tests
pnpm test:coverage       # the same, with the coverage report in coverage/
pnpm lint && pnpm typecheck
```

The scripts of the quality pipeline (the coverage gate, the mutation score and the metrics
report) have their own tests, which need nothing but Python:

```sh
python -m unittest discover -s scripts/quality/tests
```

### Logs and stopping the application

```sh
docker compose logs -f backend frontend db
docker compose down
```

`docker compose down` preserves the PostgreSQL data volume. To intentionally delete
the local database and all its data as well, use `docker compose down -v`.
