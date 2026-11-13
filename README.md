# Book Management System — FastAPI

A learning project for building a book catalog REST API with Python and FastAPI, with an emphasis on maintainable architecture, relational modeling, testing, and reproducible development environments.

## Project status

Early development. The project skeleton is in place: uv project setup, an application factory, a health router, environment-based configuration, and a first set of tests and quality checks.

The database layer, models, migrations, entity endpoints, and seed data are planned work, not completed features. See [GitHub issues](https://github.com/GLinBoy/book-management-system-fastapi/issues) for implementation progress.

## Planned scope

- Manage books, authors, publishers, and categories.
- Associate books with multiple authors and categories.
- Search, filter, sort, and paginate catalog results.
- Validate input and return consistent API errors.
- Use SQLite for development and tests, and PostgreSQL for production.
- Use UUID v7 primary keys.
- Provide deterministic development seed data.
- Add automated tests, code-quality checks, Docker support, and CI.

Authentication is outside the current scope. This project is not ready for public production deployment.

## Technology choices

| Area                              | Technology                                     |
| --------------------------------- | ---------------------------------------------- |
| Python baseline                   | Python 3.14+                                   |
| Project and dependency management | uv                                             |
| API framework                     | FastAPI, synchronous request/database workflow |
| ASGI server                       | Uvicorn                                        |
| Database access                   | SQLAlchemy                                     |
| Database migrations               | Alembic                                        |
| Settings                          | pydantic-settings                              |
| PostgreSQL driver                 | Psycopg                                        |
| Testing                           | pytest, pytest-cov, HTTPX                      |
| Linting and formatting            | Ruff                                           |
| Static type checking              | mypy                                           |
| Development data                  | Faker                                          |

Direct dependencies are declared in `pyproject.toml`; resolved dependency versions are recorded in `uv.lock`.

## Prerequisites

- Git
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- A compatible Python interpreter; uv can install one if needed

The development workflow targets Linux, including Manjaro and Arch Linux under WSL 2. On WSL, keep the checkout inside the Linux filesystem, for example `~/projects`, rather than `/mnt/c`.

PostgreSQL and Docker are not required for local development with the default `dev` profile.

## Getting started

### 1. Clone the repository

```bash
git clone [https://github.com/GLinBoy/book-management-system-fastapi.git](https://github.com/GLinBoy/book-management-system-fastapi.git)
cd book-management-system-fastapi
```

If reviewing work that has not been merged, check out the relevant branch before continuing.

### 2. Synchronize the environment

```bash
uv sync --locked
```

This installs the project's dependencies, including the default development dependency group, into the project environment (`.venv`). The `--locked` option requires the committed lockfile to be current.

The committed `.python-version` selects the development interpreter. The `requires-python` setting in `pyproject.toml` declares the supported Python range; it serves a different purpose from interpreter selection.

If you need to install the selected Python minor version manually:

```bash
uv python install 3.14
uv sync --locked
```

### 3. Configure the environment (optional)

The default `dev` profile works without any configuration. To customize settings, copy the example file:

```bash
cp .env.example .env
```

See [Environment profiles](#environment-profiles) for details.

### 4. Run the application

```bash
uv run fastapi dev app/main.py
```

Local URLs:

- OpenAPI UI: http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/health

Entity endpoints under the planned `/api/v1` prefix are not implemented yet.

### 5. Verify the installation

```bash
uv run pytest
uv run --locked python -c "import fastapi, uvicorn, sqlalchemy, alembic, pydantic_settings, psycopg; print('Runtime imports OK')"
```

### Optional: activate the virtual environment

Activation is unnecessary when using `uv run`, but you can activate the environment for an interactive Bash or Zsh session:

```bash
source .venv/bin/activate
python --version
deactivate
```

Activation changes the current shell's command lookup; it does not synchronize dependencies. Continue to use uv for dependency management.

## Environment profiles

Settings are defined in `app/core/config.py` with pydantic-settings. The `APP_ENV` variable selects the profile, and values are read from environment variables and an optional local `.env` file. Real environment variables take precedence over `.env`.

| Profile         | Database   | Behavior                                                                                     |
| --------------- | ---------- | -------------------------------------------------------------------------------------------- |
| `dev` (default) | SQLite     | Local development; default URL `sqlite:///./dev.db`                                          |
| `test`          | SQLite     | Automated tests; default URL `sqlite:///./test.db`. PostgreSQL integration tests are planned |
| `prod`          | PostgreSQL | Requires `DATABASE_URL`; startup fails if it is missing                                      |

`DATABASE_URL` overrides the default database in any profile. Use the `postgresql+psycopg://` scheme for PostgreSQL:

```text
postgresql+psycopg://user:password@localhost:5432/books
```

Switching `APP_ENV` changes the database without code changes:

```bash
APP_ENV=test uv run fastapi dev app/main.py
APP_ENV=prod DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/books uv run fastapi dev app/main.py
```

An invalid `APP_ENV` value is rejected at startup. `.env.example` documents the available variables. Never commit credentials or your real `.env`.

## Tests and code quality

```bash
uv run pytest
uv run pytest --cov=app --cov-report=term-missing
uv run ruff check .
uv run ruff format --check .
uv run mypy app
```

To apply formatting during development:

```bash
uv run ruff format .
```

### Make shortcuts

| Command          | Action                             |
| ---------------- | ---------------------------------- |
| `make run`       | Start the development server       |
| `make test`      | Run the tests                      |
| `make lint`      | Run Ruff checks                    |
| `make typecheck` | Run mypy                           |
| `make check`     | Lint, type-check, and test         |
| `make migrate`   | Apply database migrations          |
| `make seed`      | Load deterministic development data |

See [Migrations and seed data](#migrations-and-seed-data) for details.

## Dependency management

Add a runtime dependency:

```bash
uv add package-name
```

Add a development dependency:

```bash
uv add --dev package-name
```

Update dependency resolutions deliberately:

```bash
uv lock --upgrade
uv sync --locked
```

Review dependency updates and run the available checks before committing them. Commit `pyproject.toml`, `uv.lock`, and `.python-version`. Do not commit `.venv`, local secrets, or generated database files.

## Planned architecture

The following layout is a target structure. Directories marked as planned do not exist yet.

```text
app/
  main.py          # FastAPI application factory
  core/            # Settings (done); database setup, IDs, errors, logging (planned)
  models/          # SQLAlchemy models (planned)
  schemas/         # Pydantic request and response schemas (planned)
  repositories/    # Persistence operations (planned)
  services/        # Business rules and use cases (planned)
  api/             # Versioned routers
  seed/            # Development seed data (planned)
tests/
alembic/           # Migrations (planned)
```

The intended dependency flow is routers → services → repositories. Models represent persistence, and schemas define the API boundary. Concrete conventions will evolve as implementation proceeds.

## Domain design

| Entity       | Planned attributes                                                  |
| ------------ | ------------------------------------------------------------------- |
| Book         | ID, title, ISBN, publication year, price, description, publisher ID |
| Author       | ID, name, biography, birth year                                     |
| Publisher    | ID, name, country, established year                                 |
| Category     | ID, name, description                                               |
| BookAuthor   | Book ID and author ID                                               |
| BookCategory | Book ID and category ID                                             |

Relationships:

- A publisher can have many books; the implementation plan allows a book to have no publisher.
- Books and authors have a many-to-many relationship through `BookAuthor`.
- Books and categories have a many-to-many relationship through `BookCategory`.
- Association tables use composite primary keys.

The [original system design](https://app.notion.com/p/glinboy/book-management-system-2eb5d93da3318090b159e56dc6c73c22?source=copy_link) uses integer IDs. The implementation roadmap changes entity primary keys and their corresponding foreign keys to UUID v7. Access to the Notion page may require permission.

## Migrations and seed data

Apply migrations and load deterministic development data:

```bash
uv run alembic upgrade head
uv run python -m app.seed
```

Seeding is idempotent: it skips when publishers, authors, categories, or books already exist. To replace existing data:

```bash
uv run python -m app.seed --reset
```

The data set is generated from a fixed random seed, so every run produces the same values. Pass `--seed N` to generate a different data set.

Set `SEED_ON_STARTUP=true` to seed automatically when the application starts. Startup seeding is guarded: it never runs when `APP_ENV=prod`.

## Clean-checkout verification

From a separate clone of the committed branch:

```bash
uv sync --locked
uv run pytest
git status --short
```

Tests should pass and `git status` should show no tracked changes. Create a separate environment on each machine rather than copying `.venv` between machines.

## Roadmap

| Milestone           | Scope                                                           |
| ------------------- | --------------------------------------------------------------- |
| M1: Skeleton and DB | Project foundation, database infrastructure, models, migrations |
| M2: Working API     | Shared API infrastructure and entity CRUD                       |
| M3: Quality and DX  | Seed data, tests, linting, formatting, typing                   |
| M4: Ship            | Docker and GitHub Actions                                       |

See the repository issues for acceptance criteria and the current implementation order.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md) first.

Work in small, issue-focused changes:

1. Review the issue and its acceptance criteria.
2. Create a focused branch.
3. Implement the change and appropriate tests.
4. Run the available checks.
5. Review the diff, including configuration and lockfile changes.
6. Update documentation when behavior changes.

Keep completed capabilities distinct from planned ones. Update this README as application commands, profiles, migrations, and tests become available.

## License

This project is licensed under the [MIT License](LICENSE).
