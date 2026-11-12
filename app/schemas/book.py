import re
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BeforeValidator, Field, StringConstraints, field_validator

from app.schemas.author import AuthorSummary
from app.schemas.category import CategorySummary
from app.schemas.common import ORMModel
from app.schemas.publisher import PublisherSummary

BookTitle = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]

ISBN_PATTERN = re.compile(r"(?:\d{9}[\dX]|\d{13})")


def normalize_isbn(value: object) -> object:
    if not isinstance(value, str):
        return value
    normalized = re.sub(r"[\s-]", "", value).upper()
    if not ISBN_PATTERN.fullmatch(normalized):
        raise ValueError("ISBN must be 10 or 13 digits (ISBN-10 may end with X)")
    return normalized


ISBN = Annotated[str, BeforeValidator(normalize_isbn)]


class BookSummary(ORMModel):
    id: uuid.UUID
    title: str
    isbn: str | None
    publication_year: int | None
    price: Decimal | None


class BookBase(ORMModel):
    title: BookTitle
    isbn: ISBN | None = None
    publication_year: int | None = Field(default=None, ge=0, le=9999)
    price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
    )
    description: str | None = None
    publisher_id: uuid.UUID | None = None
    author_ids: list[uuid.UUID] = Field(default_factory=list)
    category_ids: list[uuid.UUID] = Field(default_factory=list)


class BookCreate(BookBase):
    pass


class BookUpdate(ORMModel):
    title: BookTitle | None = None
    isbn: ISBN | None = None
    publication_year: int | None = Field(default=None, ge=0, le=9999)
    price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
    )
    description: str | None = None
    publisher_id: uuid.UUID | None = None
    author_ids: list[uuid.UUID] | None = None
    category_ids: list[uuid.UUID] | None = None

    @field_validator("title")
    @classmethod
    def _title_must_not_be_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("title cannot be null")
        return value

    @field_validator("author_ids", "category_ids")
    @classmethod
    def _relations_must_not_be_null(
        cls, value: list[uuid.UUID] | None
    ) -> list[uuid.UUID] | None:
        if value is None:
            raise ValueError("relation ids cannot be null")
        return value


class BookAuthorsUpdate(ORMModel):
    author_ids: list[uuid.UUID]


class BookCategoriesUpdate(ORMModel):
    category_ids: list[uuid.UUID]


class BookRead(ORMModel):
    id: uuid.UUID
    title: str
    isbn: str | None
    publication_year: int | None
    price: Decimal | None
    description: str | None
    publisher: PublisherSummary | None
    authors: list[AuthorSummary]
    categories: list[CategorySummary]
    created_at: datetime
    updated_at: datetime
