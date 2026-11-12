import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import (
    InstrumentedAttribute,
    Session,
    joinedload,
    selectinload,
)

from app.models.book import Book
from app.repositories.base import Repository

SEARCH_COLUMNS: tuple[InstrumentedAttribute[Any], ...] = (
    Book.title,
    Book.isbn,
    Book.description,
)

SORTABLE: dict[str, InstrumentedAttribute[Any]] = {
    "title": Book.title,
    "price": Book.price,
    "publication_year": Book.publication_year,
    "created_at": Book.created_at,
}

EAGER_OPTIONS = (
    joinedload(Book.publisher),
    selectinload(Book.authors),
    selectinload(Book.categories),
)


class BookRepository(Repository[Book]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Book)

    def get_with_relations(self, book_id: uuid.UUID) -> Book | None:
        statement = (
            select(Book)
            .options(*EAGER_OPTIONS)
            .where(Book.id == book_id)
            .execution_options(populate_existing=True)
        )
        return self.session.scalars(statement).one_or_none()
