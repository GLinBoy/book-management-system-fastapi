import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate


def test_create_strips_name():
    category = CategoryCreate(name="  Science Fiction  ")

    assert category.name == "Science Fiction"


def test_create_defaults():
    category = CategoryCreate(name="Science Fiction")

    assert category.description is None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": ""},
        {"name": "   "},
        {"name": "x" * 101},
    ],
)
def test_create_rejects_invalid_payload(payload):
    with pytest.raises(ValidationError):
        CategoryCreate(**payload)


def test_update_allows_partial_payload():
    update = CategoryUpdate(description="Speculative fiction.")

    assert update.name is None
    assert update.model_dump(exclude_unset=True) == {
        "description": "Speculative fiction."
    }


def test_update_rejects_explicit_null_name():
    with pytest.raises(ValidationError, match="name cannot be null"):
        CategoryUpdate(name=None)


def test_update_allows_clearing_description():
    update = CategoryUpdate(description=None)

    assert update.model_dump(exclude_unset=True) == {"description": None}


def test_read_from_orm_attributes():
    now = datetime.now(UTC)
    row = SimpleNamespace(
        id=uuid.uuid4(),
        name="Science Fiction",
        description="Speculative fiction.",
        created_at=now,
        updated_at=now,
    )

    category = CategoryRead.model_validate(row)

    assert category.id == row.id
    assert category.name == "Science Fiction"
    assert category.description == "Speculative fiction."
