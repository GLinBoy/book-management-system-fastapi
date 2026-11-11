import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.publisher import PublisherCreate, PublisherRead, PublisherUpdate


def test_create_strips_whitespace():
    publisher = PublisherCreate(name="  Ace  ", country=" US ")

    assert publisher.name == "Ace"
    assert publisher.country == "US"


def test_create_defaults():
    publisher = PublisherCreate(name="Ace")

    assert publisher.country is None
    assert publisher.established_year is None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": ""},
        {"name": "   "},
        {"name": "x" * 256},
        {"name": "Ace", "country": "x" * 101},
        {"name": "Ace", "established_year": -1},
        {"name": "Ace", "established_year": 10000},
    ],
)
def test_create_rejects_invalid_payload(payload):
    with pytest.raises(ValidationError):
        PublisherCreate(**payload)


def test_update_allows_partial_payload():
    update = PublisherUpdate(country="UK")

    assert update.name is None
    assert update.model_dump(exclude_unset=True) == {"country": "UK"}


def test_update_rejects_explicit_null_name():
    with pytest.raises(ValidationError, match="name cannot be null"):
        PublisherUpdate(name=None)


def test_update_allows_clearing_optional_fields():
    update = PublisherUpdate(country=None, established_year=None)

    assert update.model_dump(exclude_unset=True) == {
        "country": None,
        "established_year": None,
    }


def test_read_from_orm_attributes():
    now = datetime.now(UTC)
    row = SimpleNamespace(
        id=uuid.uuid4(),
        name="Ace",
        country="US",
        established_year=1953,
        created_at=now,
        updated_at=now,
    )

    publisher = PublisherRead.model_validate(row)

    assert publisher.id == row.id
    assert publisher.name == "Ace"
    assert publisher.established_year == 1953
