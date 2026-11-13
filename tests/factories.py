"""Factories for building test data.

Each factory adds an instance to the session, flushes it so primary keys are
available, and returns it. Pass keyword arguments to override any default.
"""

import itertools
from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models import Author, Book, Category, Publisher

_counter = itertools.count(1)


def unique_isbn() -> str:
    return f"978{next(_counter):010d}"


def create_publisher(session: Session, **overrides: Any) -> Publisher:
    data: dict[str, Any] = {
        "name": f"Publisher {next(_counter)}",
        "country": "United States",
        "established_year": 1950,
    }
    publisher = Publisher(**(data | overrides))
    session.add(publisher)
    session.flush()
    return publisher


def create_author(session: Session, **overrides: Any) -> Author:
    data: dict[str, Any] = {
        "name": f"Author {next(_counter)}",
        "biography": "A test author.",
        "birth_year": 1920,
    }
    author = Author(**(data | overrides))
    session.add(author)
    session.flush()
    return author


def create_category(session: Session, **overrides: Any) -> Category:
    data: dict[str, Any] = {
        "name": f"Category {next(_counter)}",
        "description": "A test category.",
    }
    category = Category(**(data | overrides))
    session.add(category)
    session.flush()
    return category


def create_book(
    session: Session,
    *,
    publisher: Publisher | None = None,
    authors: Sequence[Author] = (),
    categories: Sequence[Category] = (),
    **overrides: Any,
) -> Book:
    data: dict[str, Any] = {
        "title": f"Book {next(_counter)}",
        "isbn": unique_isbn(),
        "publication_year": 1965,
        "price": Decimal("9.99"),
        "description": "A test book.",
        "publisher": publisher,
        "authors": list(authors),
        "categories": list(categories),
    }
    book = Book(**(data | overrides))
    session.add(book)
    session.flush()
    return book
