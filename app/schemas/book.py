import uuid
from decimal import Decimal

from app.schemas.common import ORMModel


class BookSummary(ORMModel):
    id: uuid.UUID
    title: str
    isbn: str | None
    publication_year: int | None
    price: Decimal | None
