import uuid

import pytest

from app.core.errors import ConflictError, NotFoundError
from app.core.pagination import PageParams
from app.models import Book, Publisher
from app.schemas.publisher import PublisherCreate, PublisherUpdate
from app.services.publisher import PublisherService


@pytest.fixture
def service(session):
    return PublisherService(session)


def seed(session, *publishers):
    session.add_all(publishers)
    session.flush()
    return publishers


def test_create_and_get(service):
    publisher = service.create(PublisherCreate(name="Ace", country="US"))

    assert publisher.id is not None
    assert service.get(publisher.id) is publisher


def test_get_missing_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.get(uuid.uuid4())


def test_update_full_payload(service):
    publisher = service.create(PublisherCreate(name="Ace", country="US"))

    updated = service.update(
        publisher.id,
        PublisherUpdate(name="Ace Books", country="UK", established_year=1953),
    )

    assert updated.name == "Ace Books"
    assert updated.country == "UK"
    assert updated.established_year == 1953


def test_update_partial_payload_keeps_other_fields(service):
    publisher = service.create(
        PublisherCreate(name="Ace", country="US", established_year=1953)
    )

    updated = service.update(publisher.id, PublisherUpdate(country="UK"))

    assert updated.name == "Ace"
    assert updated.country == "UK"
    assert updated.established_year == 1953


def test_update_without_changes_is_a_noop(service):
    publisher = service.create(PublisherCreate(name="Ace"))

    updated = service.update(publisher.id, PublisherUpdate())

    assert updated is publisher


def test_delete(service):
    publisher = service.create(PublisherCreate(name="Ace"))

    service.delete(publisher.id)

    with pytest.raises(NotFoundError):
        service.get(publisher.id)


def test_delete_publisher_with_books_raises_conflict(service, session):
    publisher = service.create(PublisherCreate(name="Ace"))
    session.add(Book(title="Dune", publisher_id=publisher.id))
    session.flush()

    with pytest.raises(ConflictError, match="still has books"):
        service.delete(publisher.id)


def test_list_search_and_filters(service, session):
    seed(
        session,
        Publisher(name="Penguin Books", country="UK", established_year=1935),
        Publisher(name="Ace", country="US", established_year=1953),
        Publisher(name="Tor", country="US", established_year=1980),
    )

    assert [p.name for p in service.list(q="penguin").items] == ["Penguin Books"]
    assert [p.name for p in service.list(country="US").items] == ["Ace", "Tor"]
    assert [
        p.name
        for p in service.list(
            established_year_min=1950, established_year_max=1970
        ).items
    ] == ["Ace"]


def test_list_sorting_and_pagination(service, session):
    seed(session, *(Publisher(name=name) for name in ["A", "B", "C", "D", "E"]))

    page = service.list(
        order_by=[Publisher.name.desc()],
        page=PageParams(page=2, size=2),
    )

    assert [p.name for p in page.items] == ["C", "B"]
    assert (page.total, page.page, page.size) == (5, 2, 2)
