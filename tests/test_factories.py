from decimal import Decimal

from tests.factories import (
    create_author,
    create_book,
    create_category,
    create_publisher,
)


def test_factories_persist_with_defaults(session):
    publisher = create_publisher(session)
    author = create_author(session)
    category = create_category(session)
    book = create_book(session)

    assert publisher.id is not None
    assert author.id is not None
    assert category.id is not None
    assert book.id is not None


def test_overrides_take_precedence(session):
    publisher = create_publisher(
        session, name="Ace", country="US", established_year=1953
    )
    book = create_book(
        session, title="Dune", isbn="9780441013593", price=Decimal("9.99")
    )

    assert (publisher.name, publisher.country, publisher.established_year) == (
        "Ace",
        "US",
        1953,
    )
    assert (book.title, book.isbn, book.price) == (
        "Dune",
        "9780441013593",
        Decimal("9.99"),
    )


def test_book_links_are_wired(session):
    publisher = create_publisher(session)
    authors = [create_author(session) for _ in range(2)]
    categories = [create_category(session) for _ in range(2)]

    book = create_book(
        session, publisher=publisher, authors=authors, categories=categories
    )

    assert book.publisher is publisher
    assert book.authors == authors
    assert book.categories == categories


def test_generated_isbns_are_unique(session):
    isbns = [create_book(session).isbn for _ in range(5)]

    assert len(set(isbns)) == 5
