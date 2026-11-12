import uuid
from decimal import Decimal

import pytest

from app.models import Author, Book, Category, Publisher

BASE = "/api/v1/books"


def seed_relations(session):
    publisher = Publisher(name="Ace", country="US", established_year=1953)
    authors = [
        Author(name="Frank Herbert", biography="Wrote Dune.", birth_year=1920),
        Author(name="Brian Herbert", birth_year=1952),
    ]
    categories = [Category(name="Science Fiction"), Category(name="Adventure")]
    session.add_all([publisher, *authors, *categories])
    session.commit()
    return publisher, authors, categories


def seed_catalog(session):
    publisher_a = Publisher(name="Ace")
    publisher_b = Publisher(name="Tor")
    author_a = Author(name="Frank Herbert")
    author_b = Author(name="Ursula K. Le Guin")
    category_a = Category(name="Science Fiction")
    category_b = Category(name="Fantasy")
    session.add_all(
        [
            Book(
                title="Dune",
                isbn="9780441013593",
                description="Desert planet",
                publication_year=1965,
                price=Decimal("9.99"),
                publisher=publisher_a,
                authors=[author_a],
                categories=[category_a],
            ),
            Book(
                title="Dune Messiah",
                isbn="9780593098233",
                description="Sequel to Dune",
                publication_year=1969,
                price=Decimal("12.50"),
                publisher=publisher_a,
                authors=[author_a],
                categories=[category_a],
            ),
            Book(
                title="A Wizard of Earthsea",
                isbn="9780547773742",
                description="Sea and magic",
                publication_year=1968,
                price=Decimal("7.99"),
                publisher=publisher_b,
                authors=[author_b],
                categories=[category_b],
            ),
            Book(
                title="The Left Hand of Darkness",
                isbn="9780441478125",
                description="Ice planet",
                publication_year=1969,
                price=None,
                publisher=publisher_b,
                authors=[author_b],
                categories=[category_b],
            ),
        ]
    )
    session.commit()
    return publisher_a, publisher_b, author_a, author_b, category_a, category_b


def titles(response):
    return [book["title"] for book in response.json()["items"]]


def book_payload(publisher, authors, categories, **overrides):
    payload = {
        "title": "Dune",
        "isbn": "978-0-441-01359-3",
        "publication_year": 1965,
        "price": "9.99",
        "description": "A desert planet.",
        "publisher_id": str(publisher.id),
        "author_ids": [str(author.id) for author in authors],
        "category_ids": [str(category.id) for category in categories],
    }
    payload.update(overrides)
    return payload


def test_create_minimal_book(client):
    response = client.post(BASE, json={"title": "Dune"})

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Dune"
    assert body["isbn"] is None
    assert body["publisher"] is None
    assert body["authors"] == []
    assert body["categories"] == []


def test_create_book_with_relations(client, session):
    publisher, authors, categories = seed_relations(session)

    response = client.post(BASE, json=book_payload(publisher, authors, categories))

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Dune"
    assert body["isbn"] == "9780441013593"
    assert body["publisher"]["name"] == "Ace"
    assert [author["name"] for author in body["authors"]] == [
        "Frank Herbert",
        "Brian Herbert",
    ]
    assert [category["name"] for category in body["categories"]] == [
        "Science Fiction",
        "Adventure",
    ]


@pytest.mark.parametrize("isbn", ["123", "978044101359X"])
def test_create_rejects_invalid_isbn(client, isbn):
    response = client.post(BASE, json={"title": "Dune", "isbn": isbn})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_create_rejects_negative_price(client):
    response = client.post(BASE, json={"title": "Dune", "price": "-0.01"})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_create_rejects_missing_referenced_entities(client):
    missing_publisher = uuid.uuid4()
    missing_author = uuid.uuid4()
    missing_category = uuid.uuid4()

    response = client.post(
        BASE,
        json={
            "title": "Dune",
            "publisher_id": str(missing_publisher),
            "author_ids": [str(missing_author)],
            "category_ids": [str(missing_category)],
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "unprocessable_entity"
    assert {tuple(detail["loc"]) for detail in body["details"]} == {
        ("body", "publisher_id"),
        ("body", "author_ids"),
        ("body", "category_ids"),
    }


def test_create_duplicate_isbn_returns_409(client):
    client.post(BASE, json={"title": "Dune", "isbn": "9780441013593"})

    response = client.post(
        BASE,
        json={"title": "Dune Messiah", "isbn": "9780441013593"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


def test_get_book(client, session):
    publisher, authors, categories = seed_relations(session)
    created = client.post(
        BASE, json=book_payload(publisher, authors, categories)
    ).json()

    response = client.get(f"{BASE}/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["publisher"]["id"] == str(publisher.id)
    assert len(body["authors"]) == 2


def test_get_missing_book_returns_404(client):
    response = client.get(f"{BASE}/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_get_invalid_uuid_returns_422(client):
    response = client.get(f"{BASE}/not-a-uuid")

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_list_is_paginated_and_sorted_by_title(client, session):
    session.add_all(Book(title=f"Book {index:02d}") for index in range(5))
    session.commit()

    body = client.get(BASE, params={"page": 2, "size": 2}).json()

    assert body["total"] == 5
    assert body["pages"] == 3
    assert (body["page"], body["size"]) == (2, 2)
    assert [book["title"] for book in body["items"]] == ["Book 02", "Book 03"]


def test_list_eager_loads_relations(client, session):
    publisher, authors, categories = seed_relations(session)
    client.post(BASE, json=book_payload(publisher, authors, categories))

    body = client.get(BASE).json()

    assert body["total"] == 1
    assert body["items"][0]["publisher"]["name"] == "Ace"
    assert len(body["items"][0]["authors"]) == 2
    assert len(body["items"][0]["categories"]) == 2


def test_put_replaces_all_fields_and_clears_relations(client, session):
    publisher, authors, categories = seed_relations(session)
    created = client.post(
        BASE, json=book_payload(publisher, authors, categories)
    ).json()

    response = client.put(f"{BASE}/{created['id']}", json={"title": "New Title"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "New Title"
    assert body["isbn"] is None
    assert body["publication_year"] is None
    assert body["price"] is None
    assert body["description"] is None
    assert body["publisher"] is None
    assert body["authors"] == []
    assert body["categories"] == []


def test_put_replaces_relations(client, session):
    publisher, authors, categories = seed_relations(session)
    created = client.post(
        BASE, json=book_payload(publisher, authors, categories)
    ).json()
    replacement_author = Author(name="Kevin J. Anderson")
    session.add(replacement_author)
    session.commit()

    response = client.put(
        f"{BASE}/{created['id']}",
        json={
            "title": "Dune",
            "publisher_id": str(publisher.id),
            "author_ids": [str(replacement_author.id)],
            "category_ids": [str(categories[0].id)],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert [author["name"] for author in body["authors"]] == ["Kevin J. Anderson"]
    assert [category["name"] for category in body["categories"]] == ["Science Fiction"]


def test_put_requires_title(client, session):
    publisher, authors, categories = seed_relations(session)
    created = client.post(
        BASE, json=book_payload(publisher, authors, categories)
    ).json()

    response = client.put(f"{BASE}/{created['id']}", json={"price": "1.00"})

    assert response.status_code == 422


def test_patch_updates_only_provided_fields(client, session):
    publisher, authors, categories = seed_relations(session)
    created = client.post(
        BASE, json=book_payload(publisher, authors, categories)
    ).json()

    response = client.patch(
        f"{BASE}/{created['id']}",
        json={"title": "Dune (1965)"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Dune (1965)"
    assert body["publisher"]["name"] == "Ace"
    assert len(body["authors"]) == 2
    assert len(body["categories"]) == 2
    assert Decimal(str(body["price"])) == Decimal("9.99")


def test_patch_can_clear_optional_fields_and_relations(client, session):
    publisher, authors, categories = seed_relations(session)
    created = client.post(
        BASE, json=book_payload(publisher, authors, categories)
    ).json()

    body = client.patch(
        f"{BASE}/{created['id']}",
        json={
            "publisher_id": None,
            "author_ids": [],
            "category_ids": [],
            "isbn": None,
            "price": None,
        },
    ).json()

    assert body["publisher"] is None
    assert body["authors"] == []
    assert body["categories"] == []
    assert body["isbn"] is None
    assert body["price"] is None


def test_patch_replaces_relations(client, session):
    publisher, authors, categories = seed_relations(session)
    created = client.post(
        BASE, json=book_payload(publisher, authors, categories)
    ).json()

    body = client.patch(
        f"{BASE}/{created['id']}",
        json={"author_ids": [str(authors[1].id)]},
    ).json()

    assert [author["name"] for author in body["authors"]] == ["Brian Herbert"]
    assert len(body["categories"]) == 2


def test_patch_rejects_missing_relations(client, session):
    publisher, authors, categories = seed_relations(session)
    created = client.post(
        BASE, json=book_payload(publisher, authors, categories)
    ).json()

    response = client.patch(
        f"{BASE}/{created['id']}",
        json={"author_ids": [str(uuid.uuid4())]},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "unprocessable_entity"
    assert body["details"][0]["loc"] == ["body", "author_ids"]


def test_patch_rejects_null_title(client, session):
    publisher, authors, categories = seed_relations(session)
    created = client.post(
        BASE, json=book_payload(publisher, authors, categories)
    ).json()

    response = client.patch(f"{BASE}/{created['id']}", json={"title": None})

    assert response.status_code == 422


def test_patch_duplicate_isbn_returns_409(client):
    first = client.post(BASE, json={"title": "Dune", "isbn": "9780441013593"}).json()
    second = client.post(
        BASE, json={"title": "Dune Messiah", "isbn": "9780593098233"}
    ).json()

    response = client.patch(
        f"{BASE}/{second['id']}",
        json={"isbn": first["isbn"]},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


def test_update_missing_book_returns_404(client):
    missing = uuid.uuid4()

    assert client.put(f"{BASE}/{missing}", json={"title": "X"}).status_code == 404
    assert client.patch(f"{BASE}/{missing}", json={"title": "X"}).status_code == 404


def test_delete_book(client, session):
    publisher, authors, categories = seed_relations(session)
    created = client.post(
        BASE, json=book_payload(publisher, authors, categories)
    ).json()

    response = client.delete(f"{BASE}/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"{BASE}/{created['id']}").status_code == 404


def test_delete_missing_book_returns_404(client):
    assert client.delete(f"{BASE}/{uuid.uuid4()}").status_code == 404


def test_openapi_documents_book_endpoints(client):
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/books" in paths
    assert "/api/v1/books/{book_id}" in paths
    assert {"get", "post"} <= set(paths["/api/v1/books"])
    assert {"get", "put", "patch", "delete"} <= set(paths["/api/v1/books/{book_id}"])
    assert "409" in paths["/api/v1/books"]["post"]["responses"]
    assert "422" in paths["/api/v1/books"]["post"]["responses"]
    assert "404" in paths["/api/v1/books/{book_id}"]["get"]["responses"]
    assert "409" in paths["/api/v1/books/{book_id}"]["patch"]["responses"]


def test_list_search_matches_title(client, session):
    seed_catalog(session)

    assert titles(client.get(BASE, params={"q": "dune"})) == [
        "Dune",
        "Dune Messiah",
    ]


def test_list_search_matches_isbn(client, session):
    seed_catalog(session)

    assert titles(client.get(BASE, params={"q": "9780593098233"})) == ["Dune Messiah"]


def test_list_search_matches_description(client, session):
    seed_catalog(session)

    assert titles(client.get(BASE, params={"q": "planet"})) == [
        "Dune",
        "The Left Hand of Darkness",
    ]


def test_list_filters_by_publisher(client, session):
    publisher_a, *_ = seed_catalog(session)

    body = client.get(BASE, params={"publisher_id": str(publisher_a.id)}).json()

    assert [book["title"] for book in body["items"]] == ["Dune", "Dune Messiah"]


def test_list_filters_by_author(client, session):
    _, _, _, author_b, _, _ = seed_catalog(session)

    body = client.get(BASE, params={"author_id": str(author_b.id)}).json()

    assert [book["title"] for book in body["items"]] == [
        "A Wizard of Earthsea",
        "The Left Hand of Darkness",
    ]


def test_list_filters_by_category(client, session):
    _, _, _, _, category_a, _ = seed_catalog(session)

    body = client.get(BASE, params={"category_id": str(category_a.id)}).json()

    assert [book["title"] for book in body["items"]] == ["Dune", "Dune Messiah"]


def test_list_filters_by_publication_year_range(client, session):
    seed_catalog(session)

    body = client.get(
        BASE,
        params={"publication_year_min": 1968, "publication_year_max": 1969},
    ).json()

    assert [book["title"] for book in body["items"]] == [
        "A Wizard of Earthsea",
        "Dune Messiah",
        "The Left Hand of Darkness",
    ]


def test_list_filters_by_price_range(client, session):
    seed_catalog(session)

    body = client.get(
        BASE,
        params={"price_min": "8.00", "price_max": "13.00"},
    ).json()

    assert [book["title"] for book in body["items"]] == ["Dune", "Dune Messiah"]


def test_list_price_filter_excludes_null_prices(client, session):
    seed_catalog(session)

    body = client.get(BASE, params={"price_min": "0.00"}).json()

    assert "The Left Hand of Darkness" not in [book["title"] for book in body["items"]]


def test_list_sort_by_price_puts_nulls_last(client, session):
    seed_catalog(session)

    assert titles(client.get(BASE, params={"sort": "price"})) == [
        "A Wizard of Earthsea",
        "Dune",
        "Dune Messiah",
        "The Left Hand of Darkness",
    ]


def test_list_sort_by_price_descending_puts_nulls_last(client, session):
    seed_catalog(session)

    assert titles(client.get(BASE, params={"sort": "-price"})) == [
        "Dune Messiah",
        "Dune",
        "A Wizard of Earthsea",
        "The Left Hand of Darkness",
    ]


def test_list_sort_by_publication_year_with_title_tiebreak(client, session):
    seed_catalog(session)

    body = client.get(
        BASE,
        params={"sort": "-publication_year,title"},
    ).json()

    assert [book["title"] for book in body["items"]] == [
        "Dune Messiah",
        "The Left Hand of Darkness",
        "A Wizard of Earthsea",
        "Dune",
    ]


def test_list_combines_search_filters_sort_and_pagination(client, session):
    publisher_a, *_ = seed_catalog(session)

    body = client.get(
        BASE,
        params={
            "q": "dune",
            "publisher_id": str(publisher_a.id),
            "publication_year_min": 1966,
            "sort": "-title",
            "size": 1,
        },
    ).json()

    assert body["total"] == 1
    assert body["pages"] == 1
    assert body["items"][0]["title"] == "Dune Messiah"


def test_list_unknown_sort_returns_422(client):
    response = client.get(BASE, params={"sort": "bogus"})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["details"][0]["loc"] == ["query", "sort"]


def test_list_rejects_negative_price_filter(client):
    response = client.get(BASE, params={"price_min": "-0.01"})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_list_unknown_author_filter_returns_empty_page(client):
    body = client.get(BASE, params={"author_id": str(uuid.uuid4())}).json()

    assert body["total"] == 0
    assert body["items"] == []
