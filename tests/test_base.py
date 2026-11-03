import time

from sqlalchemy import ForeignKey, String, UniqueConstraint, create_engine
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.models.base import NAMING_CONVENTION, Base, TimestampMixin
from app.models.mixins import UUIDPrimaryKeyMixin


class _Parent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "t15_parent"
    name: Mapped[str] = mapped_column(String(50))
    code: Mapped[str] = mapped_column(String(10))
    __table_args__ = (UniqueConstraint("code"),)


class _Child(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "t15_child"
    parent_id: Mapped[object] = mapped_column(ForeignKey("t15_parent.id"))


def test_naming_convention_keys() -> None:
    assert set(NAMING_CONVENTION) == {"ix", "uq", "ck", "fk", "pk"}


def test_constraint_names_follow_convention() -> None:
    parent = Base.metadata.tables["t15_parent"]
    child = Base.metadata.tables["t15_child"]
    assert parent.primary_key.name == "pk_t15_parent"
    uq_names = {c.name for c in parent.constraints if isinstance(c, UniqueConstraint)}
    assert uq_names == {"uq_t15_parent_code"}
    fk_names = {fk.constraint.name for fk in child.foreign_keys if fk.constraint}
    assert fk_names == {"fk_t15_child_parent_id_t15_parent"}


def test_timestamps_set_on_insert_and_updated_on_change() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        obj = _Parent(name="a", code="x")
        session.add(obj)
        session.commit()
        session.refresh(obj)
        assert obj.created_at is not None
        assert obj.updated_at is not None
        first_updated = obj.updated_at

        time.sleep(1.1)  # SQLite CURRENT_TIMESTAMP has 1 s resolution
        obj.name = "b"
        session.commit()
        session.refresh(obj)
        assert obj.updated_at > first_updated
        assert obj.created_at <= first_updated
