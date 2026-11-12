import uuid
from datetime import datetime
from typing import Annotated

from pydantic import Field, StringConstraints, field_validator

from app.schemas.common import ORMModel

AuthorName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]


class AuthorSummary(ORMModel):
    id: uuid.UUID
    name: str


class AuthorBase(ORMModel):
    name: AuthorName
    biography: str | None = None
    birth_year: int | None = Field(default=None, ge=0, le=9999)


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(ORMModel):
    name: AuthorName | None = None
    biography: str | None = None
    birth_year: int | None = Field(default=None, ge=0, le=9999)

    @field_validator("name")
    @classmethod
    def _name_must_not_be_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("name cannot be null")
        return value


class AuthorRead(AuthorBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
