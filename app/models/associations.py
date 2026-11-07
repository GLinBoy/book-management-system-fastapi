from sqlalchemy import Column, ForeignKey, Table, Uuid

from app.models.base import Base

book_authors = Table(
    "book_authors",
    Base.metadata,
    Column(
        "book_id",
        Uuid,
        ForeignKey("books.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "author_id",
        Uuid,
        ForeignKey("authors.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)

book_categories = Table(
    "book_categories",
    Base.metadata,
    Column(
        "book_id",
        Uuid,
        ForeignKey("books.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "category_id",
        Uuid,
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)
