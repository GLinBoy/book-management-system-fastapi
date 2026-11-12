import uuid
from datetime import datetime
from typing import Annotated

from pydantic import Field, StringConstraints, field_validator

from app.schemas.common import ORMModel

PublisherName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
Country = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]


class PublisherSummary(ORMModel):
    id: uuid.UUID
    name: str


class PublisherBase(ORMModel):
    name: PublisherName
    country: Country | None = None
    established_year: int | None = Field(default=None, ge=0, le=9999)


class PublisherCreate(PublisherBase):
    pass


class PublisherUpdate(ORMModel):
    name: PublisherName | None = None
    country: Country | None = None
    established_year: int | None = Field(default=None, ge=0, le=9999)

    @field_validator("name")
    @classmethod
    def _name_must_not_be_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("name cannot be null")
        return value


class PublisherRead(PublisherBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
