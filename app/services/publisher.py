import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.core.errors import ConflictError, NotFoundError
from app.core.pagination import Page, PageParams
from app.models.publisher import Publisher
from app.repositories.publisher import SEARCH_COLUMNS, PublisherRepository
from app.repositories.query import eq_filter, range_filters, search_filter
from app.schemas.publisher import PublisherCreate, PublisherUpdate


class PublisherService:
    def __init__(self, session: Session) -> None:
        self.repository = PublisherRepository(session)

    def list(
        self,
        *,
        q: str | None = None,
        country: str | None = None,
        established_year_min: int | None = None,
        established_year_max: int | None = None,
        order_by: Sequence[ColumnElement[Any]] = (),
        page: PageParams | None = None,
    ) -> Page[Publisher]:
        filters: list[ColumnElement[bool]] = []

        search = search_filter(q, SEARCH_COLUMNS)
        if search is not None:
            filters.append(search)

        country_filter = eq_filter(Publisher.country, country)
        if country_filter is not None:
            filters.append(country_filter)

        filters.extend(
            range_filters(
                Publisher.established_year,
                established_year_min,
                established_year_max,
            )
        )

        return self.repository.list(
            filters=filters,
            order_by=order_by,
            page=page,
        )

    def get(self, publisher_id: uuid.UUID) -> Publisher:
        publisher = self.repository.get(publisher_id)
        if publisher is None:
            raise NotFoundError(f"Publisher {publisher_id} not found")
        return publisher

    def create(self, data: PublisherCreate) -> Publisher:
        return self.repository.create(data.model_dump())

    def update(self, publisher_id: uuid.UUID, data: PublisherUpdate) -> Publisher:
        publisher = self.get(publisher_id)
        changes = data.model_dump(exclude_unset=True)
        if changes:
            self.repository.update(publisher, changes)
        return publisher

    def delete(self, publisher_id: uuid.UUID) -> None:
        publisher = self.get(publisher_id)
        if self.repository.has_books(publisher_id):
            raise ConflictError("Cannot delete a publisher that still has books")
        self.repository.delete(publisher)
