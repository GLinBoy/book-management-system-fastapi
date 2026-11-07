import pytest
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import create_db_engine
from app.models import (
    Author,
    Base,
    Book,
    Category,
    book_authors,
    book_categories,
)


@pytest.fixture
def engine(tmp_path):
    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'a.db'}")
    engine = create_db_engine(settings)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def count(session: Session, table) -> int:
    return session.execute(select(func.count()).select_from(table)).scalar_one()


def seed(session: Session) -> Book:
    book = Book(title="Good Omens")
    book.authors.extend([Author(name="Terry Pratchett"), Author(name="Neil Gaiman")])
    book.categories.append(Category(name="Fantasy"))
    session.add(book)
    session.commit()
    return book


def test_composite_primary_keys(engine):
    insp = inspect(engine)
    pk = insp.get_pk_constraint("book_authors")
    assert set(pk["constrained_columns"]) == {"book_id", "author_id"}
    pk = insp.get_pk_constraint("book_categories")
    assert set(pk["constrained_columns"]) == {"book_id", "category_id"}


def test_relationships_work_in_both_directions(engine):
    with Session(engine) as session:
        book = seed(session)
        assert len(book.authors) == 2
        assert book.authors[0].books == [book]
        assert book.categories[0].books == [book]
        assert count(session, book_authors) == 2
        assert count(session, book_categories) == 1


def test_duplicate_link_is_rejected(engine):
    with Session(engine) as session:
        book = seed(session)
        author = book.authors[0]
        with pytest.raises(IntegrityError):
            session.execute(
                book_authors.insert().values(book_id=book.id, author_id=author.id)
            )


def test_deleting_book_removes_links_but_keeps_authors(engine):
    with Session(engine) as session:
        book = seed(session)
        session.delete(book)
        session.commit()
        assert count(session, book_authors) == 0
        assert count(session, book_categories) == 0
        assert count(session, Author.__table__) == 2
        assert count(session, Category.__table__) == 1


def test_deleting_author_removes_link_but_keeps_book(engine):
    with Session(engine) as session:
        book = seed(session)
        session.delete(book.authors[0])
        session.commit()
        assert count(session, book_authors) == 1
        assert count(session, Book.__table__) == 1
