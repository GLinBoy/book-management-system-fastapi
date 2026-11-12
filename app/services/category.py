import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.core.errors import ConflictError, NotFoundError
from app.core.pagination import Page, PageParams
from app.models.book import Book
from app.models.category import Category
from app.repositories.category import SEARCH_COLUMNS, CategoryRepository
from app.repositories.query import search_filter
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, session: Session) -> None:
        self.repository = CategoryRepository(session)

    def list(
        self,
        *,
        q: str | None = None,
        order_by: Sequence[ColumnElement[Any]] = (),
        page: PageParams | None = None,
    ) -> Page[Category]:
        filters: list[ColumnElement[bool]] = []

        search = search_filter(q, SEARCH_COLUMNS)
        if search is not None:
            filters.append(search)

        return self.repository.list(
            filters=filters,
            order_by=order_by,
            page=page,
        )

    def list_books(
        self,
        category_id: uuid.UUID,
        *,
        page: PageParams | None = None,
    ) -> Page[Book]:
        self.get(category_id)
        return self.repository.list_books(
            category_id,
            order_by=[Book.title.asc(), Book.id.asc()],
            page=page,
        )

    def get(self, category_id: uuid.UUID) -> Category:
        category = self.repository.get(category_id)
        if category is None:
            raise NotFoundError(f"Category {category_id} not found")
        return category

    def create(self, data: CategoryCreate) -> Category:
        return self.repository.create(data.model_dump())

    def update(self, category_id: uuid.UUID, data: CategoryUpdate) -> Category:
        category = self.get(category_id)
        changes = data.model_dump(exclude_unset=True)
        if changes:
            self.repository.update(category, changes)
        return category

    def delete(self, category_id: uuid.UUID) -> None:
        category = self.get(category_id)
        if self.repository.has_books(category_id):
            raise ConflictError("Cannot delete a category that still has books")
        self.repository.delete(category)
