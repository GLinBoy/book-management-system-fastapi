from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.mixins import UUIDPrimaryKeyMixin


class Author(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "authors"

    name: Mapped[str] = mapped_column(String(255))
    biography: Mapped[str | None] = mapped_column(Text)
    birth_year: Mapped[int | None]
