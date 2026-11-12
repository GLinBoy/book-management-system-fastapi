import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.associations import book_authors, book_categories
from app.models.base import Base, TimestampMixin
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.author import Author
    from app.models.category import Category
    from app.models.publisher import Publisher


class Book(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "books"

    title: Mapped[str] = mapped_column(String(255), index=True)
    isbn: Mapped[str | None] = mapped_column(String(13), unique=True, index=True)
    publication_year: Mapped[int | None]
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    description: Mapped[str | None] = mapped_column(Text)
    publisher_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("publishers.id", ondelete="RESTRICT"),
        index=True,
    )
    publisher: Mapped[Publisher | None] = relationship()
    authors: Mapped[list[Author]] = relationship(
        secondary=book_authors, back_populates="books"
    )
    categories: Mapped[list[Category]] = relationship(
        secondary=book_categories, back_populates="books"
    )
