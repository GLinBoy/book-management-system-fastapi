import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.models.book import Book
from app.models.publisher import Publisher
from app.repositories.base import Repository

SEARCH_COLUMNS: tuple[InstrumentedAttribute[Any], ...] = (Publisher.name,)

SORTABLE: dict[str, InstrumentedAttribute[Any]] = {
    "name": Publisher.name,
    "country": Publisher.country,
    "established_year": Publisher.established_year,
    "created_at": Publisher.created_at,
}


class PublisherRepository(Repository[Publisher]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Publisher)

    def has_books(self, publisher_id: uuid.UUID) -> bool:
        statement = (
            select(1)
            .select_from(Book)
            .where(Book.publisher_id == publisher_id)
            .limit(1)
        )
        return self.session.execute(statement).first() is not None
