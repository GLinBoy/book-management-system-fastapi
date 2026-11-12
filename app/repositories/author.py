import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, Session
from sqlalchemy.sql.elements import ColumnElement

from app.core.pagination import Page, PageParams
from app.models.associations import book_authors
from app.models.author import Author
from app.models.book import Book
from app.repositories.base import Repository

SEARCH_COLUMNS: tuple[InstrumentedAttribute[Any], ...] = (
    Author.name,
    Author.biography,
)

SORTABLE: dict[str, InstrumentedAttribute[Any]] = {
    "name": Author.name,
    "birth_year": Author.birth_year,
    "created_at": Author.created_at,
}


class AuthorRepository(Repository[Author]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Author)

    def has_books(self, author_id: uuid.UUID) -> bool:
        statement = (
            select(1)
            .select_from(book_authors)
            .where(book_authors.c.author_id == author_id)
            .limit(1)
        )
        return self.session.execute(statement).first() is not None

    def list_books(
        self,
        author_id: uuid.UUID,
        *,
        order_by: Sequence[ColumnElement[Any]] = (),
        page: PageParams | None = None,
    ) -> Page[Book]:
        filters = [Book.authors.any(Author.id == author_id)]
        books: Repository[Book] = Repository(self.session, Book)
        return books.list(filters=filters, order_by=order_by, page=page)
