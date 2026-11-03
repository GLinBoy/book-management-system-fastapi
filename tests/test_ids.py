import uuid

from sqlalchemy import Engine, String, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.core.ids import new_uuid7
from app.models.mixins import UUIDPrimaryKeyMixin


class _Base(DeclarativeBase):
    pass


class _Thing(UUIDPrimaryKeyMixin, _Base):
    __tablename__ = "thing"
    name: Mapped[str] = mapped_column(String(50))


def _sqlite_engine() -> Engine:
    engine = create_engine("sqlite://")
    _Base.metadata.create_all(engine)
    return engine


def test_new_uuid7_has_version_7() -> None:
    value = new_uuid7()
    assert isinstance(value, uuid.UUID)
    assert value.version == 7


def test_new_uuid7_is_time_ordered() -> None:
    ids = [new_uuid7() for _ in range(1000)]
    timestamps = [i.int >> 80 for i in ids]  # top 48 bits = unix ms
    assert timestamps == sorted(timestamps)
    assert len(set(ids)) == len(ids)


def test_mixin_generates_id_and_roundtrips_on_sqlite() -> None:
    engine = _sqlite_engine()
    with Session(engine) as session:
        thing = _Thing(name="a")
        session.add(thing)
        session.commit()
        generated = thing.id
        assert generated.version == 7

    with Session(engine) as session:
        loaded = session.get(_Thing, generated)
        assert loaded is not None
        assert loaded.id == generated

    with engine.connect() as conn:
        raw = conn.execute(text("SELECT id FROM thing")).scalar_one()
    assert raw == generated.hex  # stored as 32 hex chars
    assert len(raw) == 32
