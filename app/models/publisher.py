from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.mixins import UUIDPrimaryKeyMixin


class Publisher(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "publishers"

    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(100))
    established_year: Mapped[int | None]
