import uuid

import pytest

from app.core.errors import ConflictError, NotFoundError
from app.core.pagination import PageParams
from app.models import Author, Book
from app.schemas.author import AuthorCreate, AuthorUpdate
from app.services.author import AuthorService


@pytest.fixture
def service(session):
    return AuthorService(session)


def seed(session, *authors):
    session.add_all(authors)
    session.flush()
    return authors


def test_create_and_get(service):
    author = service.create(
        AuthorCreate(name="Ursula K. Le Guin", biography="Wrote Earthsea.")
    )

    assert author.id is not None
    assert service.get(author.id) is author


def test_get_missing_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.get(uuid.uuid4())


def test_update_full_payload(service):
    author = service.create(AuthorCreate(name="Ursula K. Le Guin"))

    updated = service.update(
        author.id,
        AuthorUpdate(
            name="Ursula Le Guin",
            biography="Wrote Earthsea.",
            birth_year=1929,
        ),
    )

    assert updated.name == "Ursula Le Guin"
    assert updated.biography == "Wrote Earthsea."
    assert updated.birth_year == 1929


def test_update_partial_payload_keeps_other_fields(service):
    author = service.create(
        AuthorCreate(
            name="Ursula K. Le Guin",
            biography="Wrote Earthsea.",
            birth_year=1929,
        )
    )

    updated = service.update(author.id, AuthorUpdate(birth_year=1930))

    assert updated.name == "Ursula K. Le Guin"
    assert updated.biography == "Wrote Earthsea."
    assert updated.birth_year == 1930


def test_update_without_changes_is_a_noop(service):
    author = service.create(AuthorCreate(name="Ursula K. Le Guin"))

    updated = service.update(author.id, AuthorUpdate())

    assert updated is author


def test_delete(service):
    author = service.create(AuthorCreate(name="Ursula K. Le Guin"))

    service.delete(author.id)

    with pytest.raises(NotFoundError):
        service.get(author.id)


def test_delete_author_with_books_raises_conflict(service, session):
    author = service.create(AuthorCreate(name="Ursula K. Le Guin"))
    book = Book(title="A Wizard of Earthsea")
    book.authors.append(author)
    session.add(book)
    session.flush()

    with pytest.raises(ConflictError, match="still has books"):
        service.delete(author.id)


def test_list_search_matches_name(service, session):
    seed(
        session,
        Author(name="Ursula K. Le Guin", biography="Wrote Earthsea."),
        Author(name="Frank Herbert", biography="Wrote Dune."),
    )

    assert [a.name for a in service.list(q="ursula").items] == ["Ursula K. Le Guin"]


def test_list_search_matches_biography(service, session):
    seed(
        session,
        Author(name="Ursula K. Le Guin", biography="Wrote Earthsea."),
        Author(name="Frank Herbert", biography="Wrote Dune."),
    )

    assert [a.name for a in service.list(q="dune").items] == ["Frank Herbert"]


def test_list_birth_year_range(service, session):
    seed(
        session,
        Author(name="Ursula K. Le Guin", birth_year=1929),
        Author(name="Frank Herbert", birth_year=1920),
        Author(name="Octavia E. Butler", birth_year=1947),
    )

    authors = service.list(birth_year_min=1925, birth_year_max=1935).items

    assert [a.name for a in authors] == ["Ursula K. Le Guin"]


def test_list_sorting_and_pagination(service, session):
    seed(session, *(Author(name=name) for name in ["A", "B", "C", "D", "E"]))

    page = service.list(
        order_by=[Author.name.desc()],
        page=PageParams(page=2, size=2),
    )

    assert [a.name for a in page.items] == ["C", "B"]
    assert (page.total, page.page, page.size) == (5, 2, 2)
