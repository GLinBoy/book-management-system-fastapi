"""Command-line interface for seeding the development database."""

import argparse
from collections.abc import Sequence

from app.core.database import get_session_factory
from app.seed import DEFAULT_SEED, seed_database
from app.seed.runner import SeedSummary


def main(argv: Sequence[str] | None = None) -> int:
    """Seed the database and return the process exit code."""
    args = _parse_args(argv)
    with get_session_factory()() as session:
        summary = seed_database(session, reset=args.reset, seed=args.seed)
    print(_format_summary(summary))
    return 0


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m app.seed",
        description="Seed the database with deterministic development data.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="delete existing catalog data before seeding",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"random seed for data generation (default: {DEFAULT_SEED})",
    )
    return parser.parse_args(argv)


def _format_summary(summary: SeedSummary) -> str:
    if summary.skipped:
        return "Seed skipped: data already exists; use --reset to replace it."
    return (
        f"Seeded {summary.publishers} publishers, {summary.authors} authors, "
        f"{summary.categories} categories, {summary.books} books."
    )
