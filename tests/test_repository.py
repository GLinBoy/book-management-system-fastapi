import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import create_db_engine
from app.core.pagination import PageParams
from app.models import Base, Category
from app.repositories.base import Repository


@pytest.fixture
def session(tmp_path):
    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'r.db'}")
    engine = create_db_engine(settings)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture
def repo(session):
    return Repository(session, Category)


def seed(repo, names):
    return [repo.create({"name": name}) for name in names]


def test_create_and_get(repo):
    category = repo.create({"name": "Fantasy"})
    assert category.id is not None
    assert repo.get(category.id) is category
    assert repo.get(uuid.uuid4()) is None


def test_create_duplicate_raises_integrity_error(repo):
    repo.create({"name": "Fantasy"})
    with pytest.raises(IntegrityError):
        repo.create({"name": "Fantasy"})


def test_create_rejects_unknown_field(repo):
    with pytest.raises(ValueError, match="nope"):
        repo.create({"name": "x", "nope": 1})


def test_update(repo):
    category = repo.create({"name": "Fantasy"})
    updated = repo.update(category, {"description": "Dragons"})
    assert updated.description == "Dragons"


def test_update_rejects_primary_key_and_unknown_fields(repo):
    category = repo.create({"name": "Fantasy"})
    with pytest.raises(ValueError):
        repo.update(category, {"id": uuid.uuid4()})
    with pytest.raises(ValueError):
        repo.update(category, {"nope": 1})


def test_delete(repo):
    category = repo.create({"name": "Fantasy"})
    repo.delete(category)
    assert repo.get(category.id) is None


def test_list_filters(repo):
    seed(repo, ["a", "b", "c"])
    page = repo.list(filters=[Category.name.in_(["a", "b"])])
    assert page.total == 2
    assert {c.name for c in page.items} == {"a", "b"}


def test_list_sort_and_pagination(repo):
    seed(repo, ["a", "b", "c", "d", "e"])
    page = repo.list(sort=["-name"], page=PageParams(page=2, size=2))
    assert [c.name for c in page.items] == ["c", "b"]
    assert (page.total, page.page, page.size) == (5, 2, 2)


def test_list_defaults_to_first_page(repo):
    seed(repo, ["a", "b"])
    page = repo.list()
    assert page.total == 2
    assert page.page == 1
    assert page.size == 20


def test_list_rejects_unknown_sort_field(repo):
    with pytest.raises(ValueError, match="Unknown sort field"):
        repo.list(sort=["nope"])


@pytest.mark.parametrize("kwargs", [{"page": 0}, {"size": 0}, {"size": 101}])
def test_page_params_validation(kwargs):
    with pytest.raises(ValueError):
        PageParams(**kwargs)
