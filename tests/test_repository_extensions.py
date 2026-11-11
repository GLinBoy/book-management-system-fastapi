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
