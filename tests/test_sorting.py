from typing import Annotated, Any

import pytest
from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.sql.elements import ColumnElement

from app.api.pagination import Page, Pagination, paginate
from app.api.sorting import parse_sort, sort_dependency
from app.models import Publisher

ALLOWED = {"name": Publisher.name, "country": Publisher.country}


def sql(orders):
    return [str(o) for o in orders]


def test_parse_ascending_and_descending():
    orders = parse_sort("name,-country", ALLOWED)
    assert sql(orders) == ["publishers.name ASC", "publishers.country DESC"]


def test_duplicate_fields_are_ignored():
    assert len(parse_sort("name,-name,name", ALLOWED)) == 1


def test_nulls_last_option():
    orders = parse_sort("name,-country", ALLOWED, nulls_last=True)

    assert sql(orders) == [
        "publishers.name ASC NULLS LAST",
        "publishers.country DESC NULLS LAST",
    ]


def test_empty_tokens_are_skipped():
    assert len(parse_sort(" name , ,", ALLOWED)) == 1


@pytest.mark.parametrize("raw", ["bogus", "-bogus", "name,id"])
def test_unknown_field_raises(raw):
    with pytest.raises(RequestValidationError):
        parse_sort(raw, ALLOWED)


@pytest.fixture
def client(session):
    session.add_all(
        [
            Publisher(name="A", country="US"),
            Publisher(name="B", country="DE"),
            Publisher(name="C", country="US"),
            Publisher(name="D", country="DE"),
        ]
    )
    session.flush()

    sort = sort_dependency(ALLOWED, default="name", tiebreaker=Publisher.id)
    app = FastAPI()

    @app.get("/publishers", response_model=Page[str])
    def list_publishers(
        orders: Annotated[list[ColumnElement[Any]], Depends(sort)],
        params: Pagination,
    ):
        stmt = select(Publisher).order_by(*orders)
        rows, total = paginate(session, stmt, params)
        return Page.create([r.name for r in rows], total, params)

    return TestClient(app)


def names(response):
    return response.json()["items"]


def test_default_sort(client):
    assert names(client.get("/publishers")) == ["A", "B", "C", "D"]


def test_descending(client):
    assert names(client.get("/publishers", params={"sort": "-name"})) == [
        "D",
        "C",
        "B",
        "A",
    ]


def test_multiple_fields(client):
    response = client.get("/publishers", params={"sort": "country,-name"})
    assert names(response) == ["D", "B", "C", "A"]


def test_sorting_works_with_pagination(client):
    response = client.get("/publishers", params={"sort": "-name", "page": 2, "size": 3})
    assert names(response) == ["A"]


def test_unknown_field_returns_422(client):
    response = client.get("/publishers", params={"sort": "bogus"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "sort"]
    assert "bogus" in response.json()["detail"][0]["msg"]


def test_id_is_not_sortable_unless_allowed(client):
    assert client.get("/publishers", params={"sort": "id"}).status_code == 422
