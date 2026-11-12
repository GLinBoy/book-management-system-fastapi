import uuid
from decimal import Decimal

import pytest

from app.models import Author, Book

BASE = "/api/v1/authors"


def create_author(client, **overrides):
    payload = {
        "name": "Ursula K. Le Guin",
        "biography": "Wrote Earthsea.",
        "birth_year": 1929,
    }
    payload.update(overrides)
    return client.post(BASE, json=payload)


def seed(session, *authors):
    session.add_all(authors)
    session.commit()
    return authors


def test_create_returns_created_author(client):
    response = create_author(client)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Ursula K. Le Guin"
    assert body["biography"] == "Wrote Earthsea."
    assert body["birth_year"] == 1929
    assert uuid.UUID(body["id"])
    assert body["created_at"]
    assert body["updated_at"]


def test_create_strips_and_applies_defaults(client):
    response = client.post(BASE, json={"name": "  Ursula K. Le Guin  "})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Ursula K. Le Guin"
    assert body["biography"] is None
    assert body["birth_year"] is None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": ""},
        {"name": "   "},
        {"name": "x" * 256},
        {"name": "Ursula", "birth_year": -1},
        {"name": "Ursula", "birth_year": 10000},
    ],
)
def test_create_rejects_invalid_payload(client, payload):
    response = client.post(BASE, json=payload)

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_get_author(client):
    created = create_author(client).json()

    response = client.get(f"{BASE}/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_missing_author_returns_404(client):
    response = client.get(f"{BASE}/{uuid.uuid4()}")

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "not_found"
    assert "not found" in body["message"]


def test_get_invalid_uuid_returns_422(client):
    response = client.get(f"{BASE}/not-a-uuid")

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_list_is_paginated_and_sorted_by_name(client, session):
    seed(session, *(Author(name=f"A{i:02d}") for i in range(25)))

    body = client.get(BASE, params={"page": 2, "size": 10}).json()

    assert body["total"] == 25
    assert body["pages"] == 3
    assert (body["page"], body["size"]) == (2, 10)
    assert len(body["items"]) == 10
    assert body["items"][0]["name"] == "A10"


def test_list_search_matches_name(client, session):
    seed(session, Author(name="Ursula K. Le Guin"), Author(name="Frank Herbert"))

    body = client.get(BASE, params={"q": "ursula"}).json()

    assert [author["name"] for author in body["items"]] == ["Ursula K. Le Guin"]


def test_list_search_matches_biography(client, session):
    seed(
        session,
        Author(name="Ursula K. Le Guin", biography="Wrote Earthsea."),
        Author(name="Frank Herbert", biography="Wrote Dune."),
    )

    body = client.get(BASE, params={"q": "dune"}).json()

    assert [author["name"] for author in body["items"]] == ["Frank Herbert"]


def test_list_birth_year_range(client, session):
    seed(
        session,
        Author(name="Ursula K. Le Guin", birth_year=1929),
        Author(name="Frank Herbert", birth_year=1920),
        Author(name="Octavia E. Butler", birth_year=1947),
    )

    body = client.get(
        BASE,
        params={"birth_year_min": 1925, "birth_year_max": 1935},
    ).json()

    assert [author["name"] for author in body["items"]] == ["Ursula K. Le Guin"]


def test_list_sorting(client, session):
    seed(
        session,
        Author(name="A", birth_year=1900),
        Author(name="C", birth_year=1950),
        Author(name="B", birth_year=1920),
    )

    body = client.get(BASE, params={"sort": "-birth_year"}).json()

    assert [author["name"] for author in body["items"]] == ["C", "B", "A"]


def test_list_unknown_sort_returns_422(client):
    response = client.get(BASE, params={"sort": "bogus"})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["details"][0]["loc"] == ["query", "sort"]


def test_list_combines_search_filter_sort_and_pagination(client, session):
    seed(
        session,
        Author(name="Ursula K. Le Guin", biography="Earthsea", birth_year=1929),
        Author(name="Frank Herbert", biography="Dune", birth_year=1920),
        Author(name="Brian Herbert", biography="Dune", birth_year=1952),
    )

    body = client.get(
        BASE,
        params={"q": "dune", "birth_year_min": 1930, "sort": "-name", "size": 1},
    ).json()

    assert body["total"] == 1
    assert body["pages"] == 1
    assert body["items"][0]["name"] == "Brian Herbert"


def test_put_replaces_all_fields(client):
    created = create_author(client).json()

    response = client.put(f"{BASE}/{created['id']}", json={"name": "New Name"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New Name"
    assert body["biography"] is None
    assert body["birth_year"] is None


def test_put_requires_name(client):
    created = create_author(client).json()

    response = client.put(f"{BASE}/{created['id']}", json={"birth_year": 1929})

    assert response.status_code == 422


def test_patch_updates_only_provided_fields(client):
    created = create_author(client).json()

    response = client.patch(f"{BASE}/{created['id']}", json={"birth_year": 1930})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Ursula K. Le Guin"
    assert body["biography"] == "Wrote Earthsea."
    assert body["birth_year"] == 1930


def test_patch_can_clear_optional_fields(client):
    created = create_author(client).json()

    body = client.patch(
        f"{BASE}/{created['id']}",
        json={"biography": None, "birth_year": None},
    ).json()

    assert body["biography"] is None
    assert body["birth_year"] is None


def test_patch_rejects_null_name(client):
    created = create_author(client).json()

    response = client.patch(f"{BASE}/{created['id']}", json={"name": None})

    assert response.status_code == 422


def test_update_missing_author_returns_404(client):
    missing = uuid.uuid4()

    assert client.put(f"{BASE}/{missing}", json={"name": "X"}).status_code == 404
    assert client.patch(f"{BASE}/{missing}", json={"name": "X"}).status_code == 404


def test_delete_author(client):
    created = create_author(client).json()

    response = client.delete(f"{BASE}/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"{BASE}/{created['id']}").status_code == 404


def test_delete_missing_author_returns_404(client):
    assert client.delete(f"{BASE}/{uuid.uuid4()}").status_code == 404


def test_delete_author_with_books_returns_409(client, session):
    created = create_author(client).json()
    author = session.get(Author, uuid.UUID(created["id"]))
    book = Book(title="A Wizard of Earthsea")
    book.authors.append(author)
    session.add(book)
    session.commit()

    response = client.delete(f"{BASE}/{created['id']}")

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "conflict"
    assert "still has books" in body["message"]
    assert client.get(f"{BASE}/{created['id']}").status_code == 200


def test_list_author_books_is_paginated(client, session):
    created = create_author(client).json()
    author = session.get(Author, uuid.UUID(created["id"]))
    session.add_all(
        Book(title=f"Book {index:02d}", authors=[author]) for index in range(5)
    )
    session.commit()

    body = client.get(
        f"{BASE}/{created['id']}/books",
        params={"page": 2, "size": 2},
    ).json()

    assert body["total"] == 5
    assert body["pages"] == 3
    assert (body["page"], body["size"]) == (2, 2)
    assert [book["title"] for book in body["items"]] == ["Book 02", "Book 03"]


def test_list_author_books_only_returns_that_authors_books(client, session):
    created = create_author(client).json()
    author = session.get(Author, uuid.UUID(created["id"]))
    other_author = Author(name="Someone Else")
    book = Book(
        title="Dune",
        isbn="9780441013593",
        publication_year=1965,
        price=Decimal("9.99"),
    )
    book.authors.append(author)
    other_book = Book(title="Other Book")
    other_book.authors.append(other_author)
    session.add_all([book, other_book])
    session.commit()

    body = client.get(f"{BASE}/{created['id']}/books").json()

    assert body["total"] == 1
    assert body["items"][0]["title"] == "Dune"
    assert body["items"][0]["isbn"] == "9780441013593"
    assert body["items"][0]["publication_year"] == 1965
    assert Decimal(str(body["items"][0]["price"])) == Decimal("9.99")


def test_list_books_for_missing_author_returns_404(client):
    response = client.get(f"{BASE}/{uuid.uuid4()}/books")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_list_author_books_is_empty_for_author_without_books(client):
    created = create_author(client).json()

    body = client.get(f"{BASE}/{created['id']}/books").json()

    assert body["total"] == 0
    assert body["pages"] == 0
    assert body["items"] == []


def test_openapi_documents_author_endpoints(client):
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/authors" in paths
    assert "/api/v1/authors/{author_id}" in paths
    assert "/api/v1/authors/{author_id}/books" in paths
    assert {"get", "post"} <= set(paths["/api/v1/authors"])
    assert {"get", "put", "patch", "delete"} <= set(
        paths["/api/v1/authors/{author_id}"]
    )
    assert "404" in paths["/api/v1/authors/{author_id}"]["get"]["responses"]
    assert "409" in paths["/api/v1/authors/{author_id}"]["delete"]["responses"]
