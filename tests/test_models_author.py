import pytest
from sqlalchemy import Text, create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Author, Base


@pytest.fixture
def engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'models.db'}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def test_table_and_columns(engine):
    insp = inspect(engine)
    assert "authors" in insp.get_table_names()
    columns = {c["name"]: c for c in insp.get_columns("authors")}
    assert {"id", "name", "biography", "birth_year"} <= columns.keys()
    assert columns["name"]["nullable"] is False
    assert columns["biography"]["nullable"] is True
    assert isinstance(columns["biography"]["type"], Text)
    assert columns["birth_year"]["nullable"] is True


def test_create_with_uuid7_and_optional_defaults(engine):
    with Session(engine) as session:
        author = Author(name="Ursula K. Le Guin")
        session.add(author)
        session.commit()
        assert author.id.version == 7
        assert author.biography is None
        assert author.birth_year is None


def test_long_biography_round_trips(engine):
    bio = "x" * 10_000
    with Session(engine) as session:
        author = Author(name="A", biography=bio, birth_year=1929)
        session.add(author)
        session.commit()
        session.refresh(author)
        assert author.biography == bio
        assert author.birth_year == 1929


def test_name_is_required(engine):
    with Session(engine) as session:
        session.add(Author())
        with pytest.raises(IntegrityError):
            session.commit()
