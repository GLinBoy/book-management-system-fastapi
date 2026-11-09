import uuid
from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import ColumnElement, func, inspect, select
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.models.base import Base


class Repository[ModelT: Base]:
    def __init__(self, session: Session, model: type[ModelT]) -> None:
        self.session = session
        self.model = model
        mapper = inspect(model)
        self._primary_keys = list(mapper.primary_key)
        self._sortable = {attr.key for attr in mapper.column_attrs}
        pk_names = {column.key for column in mapper.primary_key}
        self._writable = {attr.key for attr in mapper.attrs} - pk_names

    def get(self, id: uuid.UUID) -> ModelT | None:
        return self.session.get(self.model, id)

    def list(
        self,
        *,
        filters: Sequence[ColumnElement[bool]] = (),
        sort: Sequence[str] = (),
        page: PageParams | None = None,
    ) -> Page[ModelT]:
        page = page or PageParams()
        total = self.session.execute(
            select(func.count()).select_from(self.model).where(*filters)
        ).scalar_one()
        statement = (
            select(self.model)
            .where(*filters)
            .order_by(*self._order_by(sort))
            .offset(page.offset)
            .limit(page.size)
        )
        items = self.session.scalars(statement).all()
        return Page(items=items, total=total, page=page.page, size=page.size)

    def create(self, data: Mapping[str, Any]) -> ModelT:
        self._check_fields(data)
        instance = self.model(**data)
        self.session.add(instance)
        self.session.flush()
        self.session.refresh(instance)
        return instance

    def update(self, instance: ModelT, data: Mapping[str, Any]) -> ModelT:
        self._check_fields(data)
        for key, value in data.items():
            setattr(instance, key, value)
        self.session.flush()
        self.session.refresh(instance)
        return instance

    def delete(self, instance: ModelT) -> None:
        self.session.delete(instance)
        self.session.flush()

    def _check_fields(self, data: Mapping[str, Any]) -> None:
        unknown = set(data) - self._writable
        if unknown:
            raise ValueError(f"Unknown or read-only fields: {sorted(unknown)}")

    def _order_by(self, sort: Sequence[str]) -> Sequence[Any]:
        clauses: list[Any] = []
        for field in sort:
            descending = field.startswith("-")
            name = field[1:] if field[:1] in ("-", "+") else field
            if name not in self._sortable:
                raise ValueError(f"Unknown sort field: {name}")
            column = getattr(self.model, name)
            clauses.append(column.desc() if descending else column.asc())
        clauses.extend(self._primary_keys)
        return clauses
