# Contributing

Thanks for your interest! This is a learning project, and contributions of all
sizes are welcome. Please read the [Code of Conduct](CODE_OF_CONDUCT.md) first.

## Getting set up

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Clone the repository and run `uv sync --locked`.
3. Copy `.env.example` to `.env` (optional; `dev` is the default profile).

See the [README](README.md) for details and the profile explanation.

## Workflow

1. Pick an issue, or open one to discuss your idea first.
2. Create a focused branch, for example `feature/10-env-based-config`.
3. Keep the change small and limited to one issue.
4. Add or update tests for behavior changes.
5. Run the checks below until they all pass.
6. Open a pull request against `main` that references the issue (`Closes #N`).

## Checks before pushing

    uv run ruff check .
    uv run ruff format --check .
    uv run mypy app
    uv run pytest

If a Makefile exists, `make check` runs the same steps.

## Style

- Format and lint with Ruff; do not hand-format around it.
- Add type hints to new code; mypy must pass.
- Never commit secrets, `.env`, or database files such as `dev.db`.
- Commit `pyproject.toml` and `uv.lock` together when dependencies change.

## Pull requests

Describe what changed and why, link the issue, and mention anything you were
unsure about. Reviews are friendly; expect questions and small change requests.

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
