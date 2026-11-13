import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Publisher


def test_table_and_columns(engine):
    insp = inspect(engine)
    assert "publishers" in insp.get_table_names()
    columns = {c["name"]: c for c in insp.get_columns("publishers")}
    assert {"id", "name", "country", "established_year"} <= columns.keys()
    assert columns["name"]["nullable"] is False
    assert columns["country"]["nullable"] is True
    assert columns["established_year"]["nullable"] is True


def test_create_with_uuid7_and_optional_defaults(engine):
    with Session(engine) as session:
        publisher = Publisher(name="O'Reilly")
        session.add(publisher)
        session.commit()
        assert publisher.id.version == 7
        assert publisher.country is None
        assert publisher.established_year is None
        assert publisher.created_at is not None


def test_name_is_required(engine):
    with Session(engine) as session:
        session.add(Publisher())
        with pytest.raises(IntegrityError):
            session.commit()
