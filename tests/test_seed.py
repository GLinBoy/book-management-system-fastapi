from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.core.database import create_db_engine
from app.models import Author, Base, Book, Category, Publisher
from app.models.associations import book_authors, book_categories
from app.seed import SeedData, SeedSummary, generate_seed_data, seed_database


def _fingerprint(data: SeedData) -> tuple[object, ...]:
    return (
        [
            (publisher.name, publisher.country, publisher.established_year)
            for publisher in data.publishers
        ],
        [(author.name, author.birth_year) for author in data.authors],
        [(category.name, category.description) for category in data.categories],
        [
            (
                book.title,
                book.isbn,
                book.publication_year,
                book.price,
                book.publisher.name if book.publisher else None,
                sorted(author.name for author in book.authors),
                sorted(category.name for category in book.categories),
            )
            for book in data.books
        ],
    )


def _count(session: Session, model: type) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def test_generate_seed_data_has_expected_counts():
    data = generate_seed_data()

    assert len(data.publishers) == 20
    assert len(data.authors) == 50
    assert len(data.categories) == 15
    assert len(data.books) == 300


def test_generate_seed_data_is_deterministic():
    assert _fingerprint(generate_seed_data(seed=7)) == _fingerprint(
        generate_seed_data(seed=7)
    )


def test_generate_seed_data_varies_with_the_seed():
    assert _fingerprint(generate_seed_data(seed=1)) != _fingerprint(
        generate_seed_data(seed=2)
    )


def test_books_are_linked_to_generated_entities():
    data = generate_seed_data()

    assert all(book.title for book in data.books)
    assert all(
        book.isbn and book.isbn.isdigit() and len(book.isbn) == 13
        for book in data.books
    )
    assert all(
        book.price is not None and book.price > Decimal(0) for book in data.books
    )
    assert all(book.publication_year for book in data.books)

    for book in data.books:
        assert book.publisher is None or book.publisher in data.publishers
        assert 1 <= len(book.authors) <= 3
        assert 1 <= len(book.categories) <= 3
        assert all(author in data.authors for author in book.authors)
        assert all(category in data.categories for category in book.categories)
        assert len({id(author) for author in book.authors}) == len(book.authors)
        assert len({id(category) for category in book.categories}) == len(
            book.categories
        )


def test_generated_isbns_are_unique():
    data = generate_seed_data()

    isbns = [book.isbn for book in data.books]
    assert len(set(isbns)) == len(isbns)


def test_seed_database_inserts_data(session):
    summary = seed_database(session)

    assert summary == SeedSummary(
        skipped=False,
        publishers=20,
        authors=50,
        categories=15,
        books=300,
    )
    assert _count(session, Publisher) == 20
    assert _count(session, Author) == 50
    assert _count(session, Category) == 15
    assert _count(session, Book) == 300


def test_seed_database_commits_changes(tmp_path):
    # A file-backed database is needed here: the shared in-memory fixture
    # cannot expose committed changes to a second connection.
    settings = Settings(
        _env_file=None, database_url=f"sqlite:///{tmp_path / 'commit.db'}"
    )
    engine = create_db_engine(settings)
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            seed_database(session)

        with Session(engine) as other:
            assert other.scalar(select(func.count()).select_from(Book)) == 300
    finally:
        engine.dispose()


def test_seeded_books_have_links(session):
    seed_database(session)

    books = session.scalars(
        select(Book).options(
            selectinload(Book.authors),
            selectinload(Book.categories),
        )
    ).all()
    assert len(books) == 300
    for book in books:
        assert 1 <= len(book.authors) <= 3
        assert 1 <= len(book.categories) <= 3
    assert _count(session, book_authors) >= 300
    assert _count(session, book_categories) >= 300


def test_seed_database_skips_when_data_exists(session):
    session.add(Author(name="Existing Author"))
    session.commit()

    summary = seed_database(session)

    assert summary.skipped is True
    assert summary.authors == 1
    assert _count(session, Publisher) == 0
    assert _count(session, Book) == 0


def test_seed_database_skips_again_on_second_run(session):
    first = seed_database(session)
    second = seed_database(session)

    assert first.skipped is False
    assert second.skipped is True
    assert second.books == 300
    assert _count(session, Book) == 300


def test_seed_database_reset_replaces_existing_data(session):
    seed_database(session)
    old_publisher_id = session.scalar(select(Publisher.id).limit(1))
    assert old_publisher_id is not None

    summary = seed_database(session, reset=True)

    assert summary.skipped is False
    assert session.get(Publisher, old_publisher_id) is None
    assert _count(session, Publisher) == 20
    assert _count(session, Author) == 50
    assert _count(session, Category) == 15
    assert _count(session, Book) == 300


def test_seed_database_reset_works_on_empty_database(session):
    summary = seed_database(session, reset=True)

    assert summary.skipped is False
    assert _count(session, Book) == 300


def test_seed_database_reset_keeps_links_consistent(session):
    seed_database(session)
    before = (_count(session, book_authors), _count(session, book_categories))

    seed_database(session, reset=True)

    after = (_count(session, book_authors), _count(session, book_categories))
    assert after == before
