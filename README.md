# Book Management System — FastAPI

A learning project for building a book catalog REST API with Python and FastAPI, with an emphasis on maintainable architecture, relational modeling, testing, and reproducible development environments.

## Project status

Early development: project initialization and dependency management.

The repository currently contains the uv project configuration, dependency lockfile, Python version selection, and Git ignore rules. The application, database layer, endpoints, migrations, and tests are planned work, not completed features.

See [GitHub issues](https://github.com/GLinBoy/book-management-system-fastapi/issues) for implementation progress.

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

| Area | Technology |
| --- | --- |
| Python baseline | Python 3.14+ |
| Project and dependency management | uv |
| API framework | FastAPI, synchronous request/database workflow |
| ASGI server | Uvicorn |
| Database access | SQLAlchemy |
| Database migrations | Alembic |
| Settings | pydantic-settings |
| PostgreSQL driver | Psycopg |
| Testing | pytest, pytest-cov, HTTPX |
| Linting and formatting | Ruff |
| Static type checking | mypy |
| Development data | Faker |

Direct dependencies are declared in `pyproject.toml`; resolved dependency versions are recorded in `uv.lock`.

## Prerequisites

- Git
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- A compatible Python interpreter; uv can install one if needed

The development workflow targets Linux, including Manjaro and Arch Linux under WSL 2. On WSL, keep the checkout inside the Linux filesystem, for example `~/projects`, rather than `/mnt/c`.

PostgreSQL and Docker are not required for the current initialization checkpoint.

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/GLinBoy/book-management-system-fastapi.git
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

### 3. Verify the installation

```bash
uv run --locked python --version
uv run --locked python -c "import sys; print(sys.executable)"
uv run --locked python -c "import fastapi, uvicorn, sqlalchemy, alembic, pydantic_settings, psycopg; print('Runtime imports OK')"
```

The executable path should point inside this checkout's `.venv`. These are environment smoke checks, not application tests.

### Optional: activate the virtual environment

Activation is unnecessary when using `uv run`, but you can activate the environment for an interactive Bash or Zsh session:

```bash
source .venv/bin/activate
python --version
deactivate
```

Activation changes the current shell's command lookup; it does not synchronize dependencies. Continue to use uv for dependency management.

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

The following layout is a target structure, not the current repository tree:

```text
app/
  main.py          # FastAPI application factory
  core/            # Settings, database setup, IDs, errors, logging
  models/          # SQLAlchemy models
  schemas/         # Pydantic request and response schemas
  repositories/    # Persistence operations
  services/        # Business rules and use cases
  api/             # Versioned routers
  seed/            # Development seed data
tests/
alembic/
```

The intended dependency flow is routers → services → repositories. Models represent persistence, and schemas define the API boundary. Concrete conventions will evolve as implementation proceeds.

## Domain design

| Entity | Planned attributes |
| --- | --- |
| Book | ID, title, ISBN, publication year, price, description, publisher ID |
| Author | ID, name, biography, birth year |
| Publisher | ID, name, country, established year |
| Category | ID, name, description |
| BookAuthor | Book ID and author ID |
| BookCategory | Book ID and category ID |

Relationships:

- A publisher can have many books; the implementation plan allows a book to have no publisher.
- Books and authors have a many-to-many relationship through `BookAuthor`.
- Books and categories have a many-to-many relationship through `BookCategory`.
- Association tables use composite primary keys.

The [original system design](https://app.notion.com/p/glinboy/book-management-system-2eb5d93da3318090b159e56dc6c73c22?source=copy_link) uses integer IDs. The implementation roadmap changes entity primary keys and their corresponding foreign keys to UUID v7. Access to the Notion page may require permission.

## Planned environment profiles

Profile support has not been implemented yet. The intended behavior is:

| Profile | Database | Behavior |
| --- | --- | --- |
| `dev` | SQLite | Local development; default URL `sqlite:///./dev.db` |
| `test` | SQLite | Isolated automated tests; PostgreSQL integration tests will also be added |
| `prod` | PostgreSQL | Requires `DATABASE_URL`; missing configuration must fail at startup |

`APP_ENV` will select `dev`, `test`, or `prod`. Settings will use pydantic-settings with local `.env` support. A tracked `.env.example` will document configuration when this feature is implemented. Never commit credentials in `.env`.

## Running the application — future step

There is no runnable application at the initialization checkpoint.

Once `app/main.py` provides the planned `create_app()` factory, the intended development command is:

```bash
uv run uvicorn app.main:create_app --factory --reload
```

Expected local URLs after the application and routes are implemented:

- OpenAPI UI: http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/health
- API prefix: `/api/v1`

These URLs are planned interfaces, not currently available endpoints.

## Tests and code quality

The tools are declared as development dependencies. Test files and project-specific tool configuration are still to be added.

Once the corresponding files and configuration exist:

```bash
uv run pytest
uv run pytest --cov=app --cov-report=term-missing
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests
```

To apply formatting during development:

```bash
uv run ruff format .
```

At the initialization checkpoint, pytest may report that no tests were collected, and commands targeting `app` or `tests` cannot succeed until those directories exist. Installing a tool does not mean its checks have been configured or passed.

## Migrations and seed data — future steps

After Alembic configuration and migration files exist:

```bash
uv run alembic upgrade head
```

After the seed module is implemented:

```bash
uv run python -m app.seed
```

Development seeding must not run automatically in production. Both commands depend on future implementation and are not part of the initial environment verification.

## Clean-checkout verification

From a separate clone of the committed branch:

```bash
uv sync --locked
uv run --locked python -c "import fastapi, sqlalchemy, psycopg; print('Clean-checkout imports OK')"
git status --short
```

Successful dependency installation and imports, with no tracked changes, are the initialization acceptance check. Run application tests as well once they exist. Create a separate environment on each machine rather than copying `.venv` between machines.

## Roadmap

| Milestone | Scope |
| --- | --- |
| M1: Skeleton and DB | Project foundation, database infrastructure, models, migrations |
| M2: Working API | Shared API infrastructure and entity CRUD |
| M3: Quality and DX | Seed data, tests, linting, formatting, typing |
| M4: Ship | Docker and GitHub Actions |

See the repository issues for acceptance criteria and the current implementation order.

## Development approach

Work in small, issue-focused changes:

1. Review the issue and its acceptance criteria.
2. Create a focused branch.
3. Implement the change and appropriate tests.
4. Run the available checks.
5. Review the diff, including configuration and lockfile changes.
6. Update documentation when behavior changes.

Keep completed capabilities distinct from planned ones. Update this README as application commands, profiles, migrations, and tests become available.

