import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.core.errors import ConflictError, NotFoundError
from app.core.pagination import Page, PageParams
from app.models.author import Author
from app.models.book import Book
from app.repositories.author import SEARCH_COLUMNS, AuthorRepository
from app.repositories.query import range_filters, search_filter
from app.schemas.author import AuthorCreate, AuthorUpdate


class AuthorService:
    def __init__(self, session: Session) -> None:
        self.repository = AuthorRepository(session)

    def list(
        self,
        *,
        q: str | None = None,
        birth_year_min: int | None = None,
        birth_year_max: int | None = None,
        order_by: Sequence[ColumnElement[Any]] = (),
        page: PageParams | None = None,
    ) -> Page[Author]:
        filters: list[ColumnElement[bool]] = []

        search = search_filter(q, SEARCH_COLUMNS)
        if search is not None:
            filters.append(search)

        filters.extend(
            range_filters(
                Author.birth_year,
                birth_year_min,
                birth_year_max,
            )
        )

        return self.repository.list(
            filters=filters,
            order_by=order_by,
            page=page,
        )

    def list_books(
        self,
        author_id: uuid.UUID,
        *,
        page: PageParams | None = None,
    ) -> Page[Book]:
        self.get(author_id)
        return self.repository.list_books(
            author_id,
            order_by=[Book.title.asc(), Book.id.asc()],
            page=page,
        )

    def get(self, author_id: uuid.UUID) -> Author:
        author = self.repository.get(author_id)
        if author is None:
            raise NotFoundError(f"Author {author_id} not found")
        return author

    def create(self, data: AuthorCreate) -> Author:
        return self.repository.create(data.model_dump())

    def update(self, author_id: uuid.UUID, data: AuthorUpdate) -> Author:
        author = self.get(author_id)
        changes = data.model_dump(exclude_unset=True)
        if changes:
            self.repository.update(author, changes)
        return author

    def delete(self, author_id: uuid.UUID) -> None:
        author = self.get(author_id)
        if self.repository.has_books(author_id):
            raise ConflictError("Cannot delete an author that still has books")
        self.repository.delete(author)
