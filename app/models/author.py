from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.associations import book_authors
from app.models.base import Base, TimestampMixin
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.book import Book


class Author(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "authors"

    name: Mapped[str] = mapped_column(String(255))
    biography: Mapped[str | None] = mapped_column(Text)
    birth_year: Mapped[int | None]
    books: Mapped[list[Book]] = relationship(
        secondary=book_authors, back_populates="authors"
    )
