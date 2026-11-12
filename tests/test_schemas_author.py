import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.author import AuthorCreate, AuthorRead, AuthorUpdate


def test_create_strips_name():
    author = AuthorCreate(name="  Ursula K. Le Guin  ")

    assert author.name == "Ursula K. Le Guin"


def test_create_defaults():
    author = AuthorCreate(name="Ursula K. Le Guin")

    assert author.biography is None
    assert author.birth_year is None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": ""},
        {"name": "   "},
        {"name": "x" * 256},
        {"name": "Ursula", "birth_year": -1},
        {"name": "Ursula", "birth_year": 10000},
    ],
)
def test_create_rejects_invalid_payload(payload):
    with pytest.raises(ValidationError):
        AuthorCreate(**payload)


def test_update_allows_partial_payload():
    update = AuthorUpdate(biography="Wrote Earthsea.")

    assert update.name is None
    assert update.model_dump(exclude_unset=True) == {"biography": "Wrote Earthsea."}


def test_update_rejects_explicit_null_name():
    with pytest.raises(ValidationError, match="name cannot be null"):
        AuthorUpdate(name=None)


def test_update_allows_clearing_optional_fields():
    update = AuthorUpdate(biography=None, birth_year=None)

    assert update.model_dump(exclude_unset=True) == {
        "biography": None,
        "birth_year": None,
    }


def test_read_from_orm_attributes():
    now = datetime.now(UTC)
    row = SimpleNamespace(
        id=uuid.uuid4(),
        name="Ursula K. Le Guin",
        biography="Wrote Earthsea.",
        birth_year=1929,
        created_at=now,
        updated_at=now,
    )

    author = AuthorRead.model_validate(row)

    assert author.id == row.id
    assert author.name == "Ursula K. Le Guin"
    assert author.biography == "Wrote Earthsea."
    assert author.birth_year == 1929
