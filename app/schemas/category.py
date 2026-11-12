import uuid
from datetime import datetime
from typing import Annotated

from pydantic import StringConstraints, field_validator

from app.schemas.common import ORMModel

CategoryName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]


class CategoryBase(ORMModel):
    name: CategoryName
    description: str | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(ORMModel):
    name: CategoryName | None = None
    description: str | None = None

    @field_validator("name")
    @classmethod
    def _name_must_not_be_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("name cannot be null")
        return value


class CategoryRead(CategoryBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
