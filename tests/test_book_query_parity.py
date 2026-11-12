import uuid

from sqlalchemy import select
from sqlalchemy.dialects import postgresql, sqlite

from app.api.sorting import parse_sort
from app.models import Author, Book, Category
from app.repositories.book import SEARCH_COLUMNS, SORTABLE
from app.repositories.query import search_filter


def build_statement():
    filters = [
        search_filter("dune", SEARCH_COLUMNS),
        Book.publisher_id == uuid.uuid4(),
        Book.authors.any(Author.id == uuid.uuid4()),
        Book.categories.any(Category.id == uuid.uuid4()),
        Book.publication_year >= 1900,
        Book.price >= 0,
    ]
    return (
        select(Book)
        .where(*(clause for clause in filters if clause is not None))
        .order_by(
            *parse_sort(
                "price,-publication_year,title",
                SORTABLE,
                nulls_last=True,
            )
        )
    )


def compile_for(dialect):
    return str(build_statement().compile(dialect=dialect()))


def test_book_query_uses_portable_constructs_on_sqlite_and_postgres():
    statements = [
        compile_for(sqlite.dialect),
        compile_for(postgresql.dialect),
    ]

    for statement in statements:
        assert "NULLS LAST" in statement
        assert "EXISTS" in statement.upper()
