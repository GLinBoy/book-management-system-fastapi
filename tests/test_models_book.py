from decimal import Decimal

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Book, Publisher


def test_columns_and_indexes(engine):
    insp = inspect(engine)
    columns = {c["name"]: c for c in insp.get_columns("books")}
    assert columns["title"]["nullable"] is False
    assert columns["publisher_id"]["nullable"] is True
    indexes = {i["name"]: i for i in insp.get_indexes("books")}
    assert {
        "ix_books_title",
        "ix_books_isbn",
        "ix_books_publisher_id",
    } <= indexes.keys()
    assert indexes["ix_books_isbn"]["unique"]


def test_foreign_key_is_named(engine):
    fks = inspect(engine).get_foreign_keys("books")
    assert any(
        fk["name"] == "fk_books_publisher_id_publishers"
        and fk["referred_table"] == "publishers"
        for fk in fks
    )


def test_create_book_with_defaults(engine):
    with Session(engine) as session:
        book = Book(title="Dune", isbn="9780441013593", price=Decimal("9.99"))
        session.add(book)
        session.commit()
        session.refresh(book)
        assert book.id.version == 7
        assert book.price == Decimal("9.99")
        assert book.publisher_id is None


def test_title_is_required(engine):
    with Session(engine) as session:
        session.add(Book())
        with pytest.raises(IntegrityError):
            session.commit()


def test_isbn_must_be_unique(engine):
    with Session(engine) as session:
        session.add(Book(title="A", isbn="9780441013593"))
        session.commit()
        session.add(Book(title="B", isbn="9780441013593"))
        with pytest.raises(IntegrityError):
            session.commit()


def test_unknown_publisher_is_rejected(engine):
    import uuid

    with Session(engine) as session:
        session.add(Book(title="A", publisher_id=uuid.uuid4()))
        with pytest.raises(IntegrityError):
            session.commit()


def test_deleting_publisher_with_books_is_restricted(engine):
    with Session(engine) as session:
        publisher = Publisher(name="Ace")
        session.add(publisher)
        session.flush()
        session.add(Book(title="Dune", publisher_id=publisher.id))
        session.commit()

        session.delete(publisher)
        with pytest.raises(IntegrityError):
            session.commit()
