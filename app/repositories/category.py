import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.models.associations import book_categories
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
