import uuid
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.models import Author, Book, Category, Publisher
from app.schemas.book import BookCreate, BookRead, BookUpdate


def test_create_minimal_defaults():
    book = BookCreate(title="  Dune  ")

    assert book.title == "Dune"
    assert book.isbn is None
    assert book.publication_year is None
    assert book.price is None
    assert book.description is None
    assert book.publisher_id is None
    assert book.author_ids == []
    assert book.category_ids == []


@pytest.mark.parametrize("title", ["", "   ", "x" * 256])
def test_create_rejects_invalid_title(title):
    with pytest.raises(ValidationError):
        BookCreate(title=title)


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [
        ("978-0-441-01359-3", "9780441013593"),
        ("978 0 441 01359 3", "9780441013593"),
        ("0-441-01359-7", "0441013597"),
        ("080442957X", "080442957X"),
        ("0-8044-2957-x", "080442957X"),
    ],
)
def test_create_normalizes_isbn(raw, normalized):
    book = BookCreate(title="Dune", isbn=raw)

    assert book.isbn == normalized


@pytest.mark.parametrize(
    "isbn",
    [
        "123",
        "123456789",
        "12345678901",
        "978044101359X",
        "97804410135934",
        "abcdefghij",
    ],
)
def test_create_rejects_invalid_isbn(isbn):
    with pytest.raises(ValidationError):
        BookCreate(title="Dune", isbn=isbn)


@pytest.mark.parametrize("price", [Decimal("-0.01"), Decimal("1.999")])
def test_create_rejects_invalid_price(price):
    with pytest.raises(ValidationError):
        BookCreate(title="Dune", price=price)


@pytest.mark.parametrize("publication_year", [-1, 10000])
def test_create_rejects_invalid_publication_year(publication_year):
    with pytest.raises(ValidationError):
        BookCreate(title="Dune", publication_year=publication_year)


def test_create_accepts_relation_ids():
    publisher_id = uuid.uuid4()
    author_ids = [uuid.uuid4(), uuid.uuid4()]
    category_ids = [uuid.uuid4()]

    book = BookCreate(
        title="Dune",
        publisher_id=publisher_id,
        author_ids=author_ids,
        category_ids=category_ids,
    )

    assert book.publisher_id == publisher_id
    assert book.author_ids == author_ids
    assert book.category_ids == category_ids


def test_update_allows_partial_payload():
    update = BookUpdate(description="A desert planet.")

    assert update.title is None
    assert update.model_dump(exclude_unset=True) == {"description": "A desert planet."}


def test_update_rejects_explicit_null_title():
    with pytest.raises(ValidationError, match="title cannot be null"):
        BookUpdate(title=None)


@pytest.mark.parametrize("field", ["author_ids", "category_ids"])
def test_update_rejects_explicit_null_relation_lists(field):
    with pytest.raises(ValidationError, match="relation ids cannot be null"):
        BookUpdate(**{field: None})


def test_update_allows_clearing_optional_fields():
    update = BookUpdate(
        isbn=None,
        publication_year=None,
        price=None,
        description=None,
        publisher_id=None,
    )

    assert update.model_dump(exclude_unset=True) == {
        "isbn": None,
        "publication_year": None,
        "price": None,
        "description": None,
        "publisher_id": None,
    }


def test_update_allows_clearing_relations_with_empty_lists():
    update = BookUpdate(author_ids=[], category_ids=[])

    assert update.model_dump(exclude_unset=True) == {
        "author_ids": [],
        "category_ids": [],
    }


def test_read_from_orm_attributes_with_nested_summaries():
    now = datetime.now(UTC)
    publisher = SimpleNamespace(id=uuid.uuid4(), name="Ace")
    author = SimpleNamespace(id=uuid.uuid4(), name="Frank Herbert")
    category = SimpleNamespace(id=uuid.uuid4(), name="Science Fiction")
    row = SimpleNamespace(
        id=uuid.uuid4(),
        title="Dune",
        isbn="9780441013593",
        publication_year=1965,
        price=Decimal("9.99"),
        description="A desert planet.",
        publisher=publisher,
        authors=[author],
        categories=[category],
        created_at=now,
        updated_at=now,
    )

    book = BookRead.model_validate(row)

    assert book.publisher is not None
    assert book.publisher.name == "Ace"
    assert [a.name for a in book.authors] == ["Frank Herbert"]
    assert [c.name for c in book.categories] == ["Science Fiction"]


def test_read_from_orm_with_real_relationships(session):
    publisher = Publisher(name="Ace")
    author = Author(name="Frank Herbert")
    category = Category(name="Science Fiction")
    book = Book(
        title="Dune",
        isbn="9780441013593",
        price=Decimal("9.99"),
        publisher=publisher,
        authors=[author],
        categories=[category],
    )
    session.add(book)
    session.flush()

    read = BookRead.model_validate(book)

    assert read.publisher is not None
    assert read.publisher.id == publisher.id
    assert [a.id for a in read.authors] == [author.id]
    assert [c.id for c in read.categories] == [category.id]
