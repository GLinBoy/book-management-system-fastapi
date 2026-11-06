import pytest
from sqlalchemy import Text, create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base, Category


@pytest.fixture
def engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'models.db'}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def test_table_and_columns(engine):
    insp = inspect(engine)
    assert "categories" in insp.get_table_names()
    columns = {c["name"]: c for c in insp.get_columns("categories")}
    assert {"id", "name", "description"} <= columns.keys()
    assert columns["name"]["nullable"] is False
    assert columns["description"]["nullable"] is True
    assert isinstance(columns["description"]["type"], Text)


def test_name_has_named_unique_constraint(engine):
    constraints = inspect(engine).get_unique_constraints("categories")
    assert any(
        c["name"] == "uq_categories_name" and c["column_names"] == ["name"]
        for c in constraints
    )


def test_create_with_uuid7_and_optional_description(engine):
    with Session(engine) as session:
        category = Category(name="Fantasy")
        session.add(category)
        session.commit()
        assert category.id.version == 7
        assert category.description is None


def test_name_must_be_unique(engine):
    with Session(engine) as session:
        session.add(Category(name="Fantasy"))
        session.commit()
        session.add(Category(name="Fantasy"))
        with pytest.raises(IntegrityError):
            session.commit()


def test_name_is_required(engine):
    with Session(engine) as session:
        session.add(Category())
        with pytest.raises(IntegrityError):
            session.commit()
