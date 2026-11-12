import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, Session
from sqlalchemy.sql.elements import ColumnElement

from app.core.pagination import Page, PageParams
from app.models.associations import book_categories
from app.models.book import Book
from app.models.category import Category
from app.repositories.base import Repository

SEARCH_COLUMNS: tuple[InstrumentedAttribute[Any], ...] = (
    Category.name,
    Category.description,
)

SORTABLE: dict[str, InstrumentedAttribute[Any]] = {
    "name": Category.name,
    "created_at": Category.created_at,
}


class CategoryRepository(Repository[Category]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Category)

    def has_books(self, category_id: uuid.UUID) -> bool:
        statement = (
            select(1)
            .select_from(book_categories)
            .where(book_categories.c.category_id == category_id)
            .limit(1)
        )
        return self.session.execute(statement).first() is not None

    def list_books(
        self,
        category_id: uuid.UUID,
        *,
        order_by: Sequence[ColumnElement[Any]] = (),
        page: PageParams | None = None,
    ) -> Page[Book]:
        filters = [Book.categories.any(Category.id == category_id)]
        books: Repository[Book] = Repository(self.session, Book)
        return books.list(filters=filters, order_by=order_by, page=page)
