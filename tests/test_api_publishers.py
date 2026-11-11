import uuid

import pytest

from app.models import Book, Publisher

BASE = "/api/v1/publishers"


def create_publisher(client, **overrides):
    payload = {"name": "Ace", "country": "US", "established_year": 1953}
    payload.update(overrides)
    return client.post(BASE, json=payload)


def seed(session, *publishers):
    session.add_all(publishers)
    session.commit()
    return publishers


def test_create_returns_created_publisher(client):
    response = create_publisher(client)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Ace"
    assert body["country"] == "US"
    assert body["established_year"] == 1953
    assert uuid.UUID(body["id"])
    assert body["created_at"]
    assert body["updated_at"]


def test_create_strips_and_applies_defaults(client):
    response = client.post(BASE, json={"name": "  Ace  "})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Ace"
    assert body["country"] is None
    assert body["established_year"] is None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": ""},
        {"name": "   "},
        {"name": "Ace", "country": "x" * 101},
        {"name": "Ace", "established_year": -1},
        {"name": "Ace", "established_year": 10000},
    ],
)
def test_create_rejects_invalid_payload(client, payload):
    response = client.post(BASE, json=payload)

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_get_publisher(client):
    created = create_publisher(client).json()

    response = client.get(f"{BASE}/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_missing_publisher_returns_404(client):
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
    seed(session, *(Publisher(name=f"P{i:02d}") for i in range(25)))

    body = client.get(BASE, params={"page": 2, "size": 10}).json()

    assert body["total"] == 25
    assert body["pages"] == 3
    assert (body["page"], body["size"]) == (2, 10)
    assert len(body["items"]) == 10
    assert body["items"][0]["name"] == "P10"


def test_list_search(client, session):
    seed(session, Publisher(name="Penguin Books"), Publisher(name="Ace"))

    body = client.get(BASE, params={"q": "penguin"}).json()

    assert [publisher["name"] for publisher in body["items"]] == ["Penguin Books"]


def test_list_country_and_year_range(client, session):
    seed(
        session,
        Publisher(name="Penguin", country="UK", established_year=1935),
        Publisher(name="Ace", country="US", established_year=1953),
        Publisher(name="Tor", country="US", established_year=1980),
    )

    body = client.get(
        BASE,
        params={
            "country": "US",
            "established_year_min": 1950,
            "established_year_max": 1970,
        },
    ).json()

    assert [publisher["name"] for publisher in body["items"]] == ["Ace"]


def test_list_sorting(client, session):
    seed(session, Publisher(name="A"), Publisher(name="C"), Publisher(name="B"))

    body = client.get(BASE, params={"sort": "-name"}).json()

    assert [publisher["name"] for publisher in body["items"]] == ["C", "B", "A"]


def test_list_unknown_sort_returns_422(client):
    response = client.get(BASE, params={"sort": "bogus"})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["details"][0]["loc"] == ["query", "sort"]


def test_list_combines_filters_sort_and_pagination(client, session):
    seed(
        session,
        Publisher(name="Ace", country="US", established_year=1953),
        Publisher(name="Tor", country="US", established_year=1980),
        Publisher(name="Penguin", country="UK", established_year=1935),
    )

    body = client.get(
        BASE,
        params={"country": "US", "sort": "-established_year", "size": 1},
    ).json()

    assert body["total"] == 2
    assert body["pages"] == 2
    assert body["items"][0]["name"] == "Tor"


def test_put_replaces_all_fields(client):
    created = create_publisher(client).json()

    response = client.put(f"{BASE}/{created['id']}", json={"name": "New Name"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New Name"
    assert body["country"] is None
    assert body["established_year"] is None


def test_put_requires_name(client):
    created = create_publisher(client).json()

    response = client.put(f"{BASE}/{created['id']}", json={"country": "UK"})

    assert response.status_code == 422


def test_patch_updates_only_provided_fields(client):
    created = create_publisher(client).json()

    response = client.patch(f"{BASE}/{created['id']}", json={"country": "UK"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Ace"
    assert body["country"] == "UK"
    assert body["established_year"] == 1953


def test_patch_can_clear_optional_fields(client):
    created = create_publisher(client).json()

    body = client.patch(
        f"{BASE}/{created['id']}",
        json={"country": None, "established_year": None},
    ).json()

    assert body["country"] is None
    assert body["established_year"] is None


def test_patch_rejects_null_name(client):
    created = create_publisher(client).json()

    response = client.patch(f"{BASE}/{created['id']}", json={"name": None})

    assert response.status_code == 422


def test_update_missing_publisher_returns_404(client):
    missing = uuid.uuid4()

    assert client.put(f"{BASE}/{missing}", json={"name": "X"}).status_code == 404
    assert client.patch(f"{BASE}/{missing}", json={"name": "X"}).status_code == 404


def test_delete_publisher(client):
    created = create_publisher(client).json()

    response = client.delete(f"{BASE}/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"{BASE}/{created['id']}").status_code == 404


def test_delete_missing_publisher_returns_404(client):
    assert client.delete(f"{BASE}/{uuid.uuid4()}").status_code == 404


def test_delete_publisher_with_books_returns_409(client, session):
    created = create_publisher(client).json()
    session.add(Book(title="Dune", publisher_id=uuid.UUID(created["id"])))
    session.commit()

    response = client.delete(f"{BASE}/{created['id']}")

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "conflict"
    assert "still has books" in body["message"]
    assert client.get(f"{BASE}/{created['id']}").status_code == 200


def test_openapi_documents_publisher_endpoints(client):
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]

    assert "/api/v1/publishers" in paths
    assert "/api/v1/publishers/{publisher_id}" in paths
    assert {"get", "post"} <= set(paths["/api/v1/publishers"])
    assert {"get", "put", "patch", "delete"} <= set(
        paths["/api/v1/publishers/{publisher_id}"]
    )
    assert "404" in paths["/api/v1/publishers/{publisher_id}"]["get"]["responses"]
    assert "409" in paths["/api/v1/publishers/{publisher_id}"]["delete"]["responses"]


def test_health_still_available(client):
    assert client.get("/health").json() == {"status": "ok"}
