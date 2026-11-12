import uuid
from decimal import Decimal

import pytest

from app.models import Book, Category

BASE = "/api/v1/categories"


def create_category(client, **overrides):
    payload = {
        "name": "Science Fiction",
        "description": "Speculative fiction.",
    }
    payload.update(overrides)
    return client.post(BASE, json=payload)


def seed(session, *categories):
    session.add_all(categories)
    session.commit()
    return categories


def test_create_returns_created_category(client):
    response = create_category(client)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Science Fiction"
    assert body["description"] == "Speculative fiction."
    assert uuid.UUID(body["id"])
    assert body["created_at"]
    assert body["updated_at"]


def test_create_strips_and_applies_defaults(client):
    response = client.post(BASE, json={"name": "  History  "})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "History"
    assert body["description"] is None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": ""},
        {"name": "   "},
        {"name": "x" * 101},
    ],
)
def test_create_rejects_invalid_payload(client, payload):
    response = client.post(BASE, json=payload)

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_create_duplicate_name_returns_409(client):
    create_category(client)

    response = create_category(client)

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "conflict"


def test_get_category(client):
    created = create_category(client).json()

    response = client.get(f"{BASE}/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_missing_category_returns_404(client):
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
    seed(session, *(Category(name=f"C{i:02d}") for i in range(25)))

    body = client.get(BASE, params={"page": 2, "size": 10}).json()

    assert body["total"] == 25
    assert body["pages"] == 3
    assert (body["page"], body["size"]) == (2, 10)
    assert len(body["items"]) == 10
    assert body["items"][0]["name"] == "C10"


def test_list_search_matches_name(client, session):
    seed(session, Category(name="Science Fiction"), Category(name="History"))

    body = client.get(BASE, params={"q": "science"}).json()

    assert [category["name"] for category in body["items"]] == ["Science Fiction"]


def test_list_search_matches_description(client, session):
    seed(
        session,
        Category(name="Science Fiction", description="Speculative fiction."),
        Category(name="History", description="Non-fiction."),
    )

    body = client.get(BASE, params={"q": "non-fiction"}).json()

    assert [category["name"] for category in body["items"]] == ["History"]


def test_list_sorting(client, session):
    seed(session, Category(name="A"), Category(name="C"), Category(name="B"))

    body = client.get(BASE, params={"sort": "-name"}).json()

    assert [category["name"] for category in body["items"]] == ["C", "B", "A"]


def test_list_unknown_sort_returns_422(client):
    response = client.get(BASE, params={"sort": "bogus"})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["details"][0]["loc"] == ["query", "sort"]


def test_list_combines_search_sort_and_pagination(client, session):
    seed(
        session,
        Category(name="Science Fiction", description="Speculative fiction."),
        Category(name="Fantasy", description="Speculative fiction."),
        Category(name="History", description="Non-fiction."),
    )

    body = client.get(
        BASE,
        params={"q": "speculative", "sort": "-name", "size": 1},
    ).json()

    assert body["total"] == 2
    assert body["pages"] == 2
    assert body["items"][0]["name"] == "Science Fiction"


def test_put_replaces_all_fields(client):
    created = create_category(client).json()

    response = client.put(f"{BASE}/{created['id']}", json={"name": "New Name"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New Name"
    assert body["description"] is None


def test_put_requires_name(client):
    created = create_category(client).json()

    response = client.put(f"{BASE}/{created['id']}", json={"description": "x"})

    assert response.status_code == 422


def test_put_duplicate_name_returns_409(client):
    create_category(client, name="History")
    created = create_category(client, name="Science Fiction").json()

    response = client.put(f"{BASE}/{created['id']}", json={"name": "History"})

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


def test_patch_updates_only_provided_fields(client):
    created = create_category(client).json()

    response = client.patch(f"{BASE}/{created['id']}", json={"name": "Sci-Fi"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Sci-Fi"
    assert body["description"] == "Speculative fiction."


def test_patch_can_clear_description(client):
    created = create_category(client).json()

    body = client.patch(f"{BASE}/{created['id']}", json={"description": None}).json()

    assert body["description"] is None


def test_patch_rejects_null_name(client):
    created = create_category(client).json()

    response = client.patch(f"{BASE}/{created['id']}", json={"name": None})

    assert response.status_code == 422


def test_patch_duplicate_name_returns_409(client):
    create_category(client, name="History")
    created = create_category(client, name="Science Fiction").json()

    response = client.patch(f"{BASE}/{created['id']}", json={"name": "History"})

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


def test_update_missing_category_returns_404(client):
    missing = uuid.uuid4()

    assert client.put(f"{BASE}/{missing}", json={"name": "X"}).status_code == 404
    assert client.patch(f"{BASE}/{missing}", json={"name": "X"}).status_code == 404


def test_delete_category(client):
    created = create_category(client).json()

    response = client.delete(f"{BASE}/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"{BASE}/{created['id']}").status_code == 404


def test_delete_missing_category_returns_404(client):
    assert client.delete(f"{BASE}/{uuid.uuid4()}").status_code == 404


def test_delete_category_with_books_returns_409(client, session):
    created = create_category(client).json()
    category = session.get(Category, uuid.UUID(created["id"]))
    book = Book(title="Dune")
    book.categories.append(category)
    session.add(book)
    session.commit()

    response = client.delete(f"{BASE}/{created['id']}")

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "conflict"
    assert "still has books" in body["message"]
    assert client.get(f"{BASE}/{created['id']}").status_code == 200


def test_list_category_books_is_paginated(client, session):
    created = create_category(client).json()
    category = session.get(Category, uuid.UUID(created["id"]))
    session.add_all(
        Book(title=f"Book {index:02d}", categories=[category]) for index in range(5)
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


def test_list_category_books_only_returns_that_categories_books(client, session):
    created = create_category(client).json()
    category = session.get(Category, uuid.UUID(created["id"]))
    other_category = Category(name="History")
    book = Book(
        title="Dune",
        isbn="9780441013593",
        publication_year=1965,
        price=Decimal("9.99"),
    )
    book.categories.append(category)
    other_book = Book(title="Other Book")
    other_book.categories.append(other_category)
    session.add_all([book, other_book])
    session.commit()

    body = client.get(f"{BASE}/{created['id']}/books").json()

    assert body["total"] == 1
    assert body["items"][0]["title"] == "Dune"
    assert body["items"][0]["isbn"] == "9780441013593"
    assert body["items"][0]["publication_year"] == 1965
    assert Decimal(str(body["items"][0]["price"])) == Decimal("9.99")


def test_list_books_for_missing_category_returns_404(client):
    response = client.get(f"{BASE}/{uuid.uuid4()}/books")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_list_category_books_is_empty_for_category_without_books(client):
    created = create_category(client).json()

    body = client.get(f"{BASE}/{created['id']}/books").json()

    assert body["total"] == 0
    assert body["pages"] == 0
    assert body["items"] == []


def test_openapi_documents_category_endpoints(client):
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/categories" in paths
    assert "/api/v1/categories/{category_id}" in paths
    assert "/api/v1/categories/{category_id}/books" in paths
    assert {"get", "post"} <= set(paths["/api/v1/categories"])
    assert {"get", "put", "patch", "delete"} <= set(
        paths["/api/v1/categories/{category_id}"]
    )
    assert "404" in paths["/api/v1/categories/{category_id}"]["get"]["responses"]
    assert "409" in paths["/api/v1/categories/{category_id}"]["delete"]["responses"]
    assert "409" in paths["/api/v1/categories"]["post"]["responses"]
