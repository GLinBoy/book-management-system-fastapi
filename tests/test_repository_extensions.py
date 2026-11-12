import uuid

from app.models import Category
from app.repositories.base import Repository


def test_count_and_exists(session):
    session.add_all([Category(name="Fantasy"), Category(name="Science")])
    session.flush()
    repo = Repository(session, Category)

    assert repo.count() == 2
    assert repo.count(filters=[Category.name == "Fantasy"]) == 1
    assert repo.exists(filters=[Category.name == "Fantasy"]) is True
    assert repo.exists(filters=[Category.name == "Missing"]) is False


def test_get_many(session):
    categories = [Category(name="Fantasy"), Category(name="Science")]
    session.add_all(categories)
    session.flush()
    repo = Repository(session, Category)

    found = repo.get_many([categories[0].id, uuid.uuid4()])

    assert [category.id for category in found] == [categories[0].id]
    assert repo.get_many([]) == []
