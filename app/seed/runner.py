"""Apply deterministic development data to the database."""

from dataclasses import dataclass

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import Author, Book, Category, Publisher
from app.models.associations import book_authors, book_categories
from app.models.base import Base
from app.seed.data import DEFAULT_SEED, generate_seed_data

_DELETE_ORDER = (Book, Author, Category, Publisher)


@dataclass(frozen=True)
class SeedSummary:
    """Catalog row counts after a seed attempt."""

    skipped: bool
    publishers: int
    authors: int
    categories: int
    books: int


def seed_database(
    session: Session,
    *,
    reset: bool = False,
    seed: int = DEFAULT_SEED,
) -> SeedSummary:
    """Seed development data, skipping when the catalog is not empty.

    Without ``reset``, seeding is skipped if any publishers, authors,
    categories, or books already exist. With ``reset=True``, existing catalog
    rows are deleted before seeding. The change is committed on success and
    rolled back on failure.
    """
    if not reset and _has_data(session):
        return _summary(session, skipped=True)

    try:
        if reset:
            _clear(session)
        data = generate_seed_data(seed)
        session.add_all(
            [*data.publishers, *data.authors, *data.categories, *data.books]
        )
        session.commit()
    except Exception:
        session.rollback()
        raise

    return _summary(session, skipped=False)


def _has_data(session: Session) -> bool:
    return any(_count(session, model) > 0 for model in _DELETE_ORDER)


def _clear(session: Session) -> None:
    session.execute(delete(book_authors))
    session.execute(delete(book_categories))
    for model in _DELETE_ORDER:
        session.execute(delete(model))


def _summary(session: Session, *, skipped: bool) -> SeedSummary:
    return SeedSummary(
        skipped=skipped,
        publishers=_count(session, Publisher),
        authors=_count(session, Author),
        categories=_count(session, Category),
        books=_count(session, Book),
    )


def _count(session: Session, model: type[Base]) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0
