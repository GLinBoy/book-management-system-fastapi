import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.models.associations import book_authors
from app.models.author import Author
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
