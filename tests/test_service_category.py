import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.core.pagination import PageParams
from app.models import Book, Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.category import CategoryService


@pytest.fixture
def service(session):
    return CategoryService(session)


def seed(session, *categories):
    session.add_all(categories)
    session.flush()
    return categories


def test_create_and_get(service):
    category = service.create(
        CategoryCreate(name="Science Fiction", description="Speculative fiction.")
    )

    assert category.id is not None
    assert service.get(category.id) is category


def test_get_missing_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.get(uuid.uuid4())


def test_create_duplicate_name_raises_integrity_error(service):
    service.create(CategoryCreate(name="Science Fiction"))

    with pytest.raises(IntegrityError):
        service.create(CategoryCreate(name="Science Fiction"))


def test_update_full_payload(service):
    category = service.create(CategoryCreate(name="Science Fiction"))

    updated = service.update(
        category.id,
        CategoryUpdate(
            name="Speculative Fiction",
            description="Speculative fiction.",
        ),
    )

    assert updated.name == "Speculative Fiction"
    assert updated.description == "Speculative fiction."


def test_update_partial_payload_keeps_other_fields(service):
    category = service.create(
        CategoryCreate(name="Science Fiction", description="Speculative fiction.")
    )

    updated = service.update(category.id, CategoryUpdate(name="Sci-Fi"))

    assert updated.name == "Sci-Fi"
    assert updated.description == "Speculative fiction."


def test_update_without_changes_is_a_noop(service):
    category = service.create(CategoryCreate(name="Science Fiction"))

    updated = service.update(category.id, CategoryUpdate())

    assert updated is category


def test_delete(service):
    category = service.create(CategoryCreate(name="Science Fiction"))

    service.delete(category.id)

    with pytest.raises(NotFoundError):
        service.get(category.id)


def test_delete_category_with_books_raises_conflict(service, session):
    category = service.create(CategoryCreate(name="Science Fiction"))
    book = Book(title="Dune")
    book.categories.append(category)
    session.add(book)
    session.flush()

    with pytest.raises(ConflictError, match="still has books"):
        service.delete(category.id)


def test_list_search_matches_name(service, session):
    seed(
        session,
        Category(name="Science Fiction", description="Speculative fiction."),
        Category(name="History", description="Non-fiction."),
    )

    assert [c.name for c in service.list(q="science").items] == ["Science Fiction"]


def test_list_search_matches_description(service, session):
    seed(
        session,
        Category(name="Science Fiction", description="Speculative fiction."),
        Category(name="History", description="Non-fiction."),
    )

    assert [c.name for c in service.list(q="non-fiction").items] == ["History"]


def test_list_sorting_and_pagination(service, session):
    seed(session, *(Category(name=name) for name in ["A", "B", "C", "D", "E"]))

    page = service.list(
        order_by=[Category.name.desc()],
        page=PageParams(page=2, size=2),
    )

    assert [c.name for c in page.items] == ["C", "B"]
    assert (page.total, page.page, page.size) == (5, 2, 2)
