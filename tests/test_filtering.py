from typing import Annotated, Any

import pytest
from fastapi import Depends, FastAPI, Query
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.api.filtering import (
    SearchQuery,
    apply_eq,
    apply_in,
    apply_range,
    apply_search,
    escape_like,
)
from app.api.pagination import Page, Pagination, paginate
from app.api.sorting import sort_dependency
from app.models import Publisher

SEARCH_COLUMNS = [Publisher.name, Publisher.country]


@pytest.fixture
def seeded_session(session):
    session.add_all(
        [
            Publisher(name="Penguin Books", country="UK", established_year=1935),
            Publisher(name="O'Reilly Media", country="US", established_year=1978),
            Publisher(name="Ace", country="US", established_year=1953),
            Publisher(name="Tor", country="US", established_year=1980),
            Publisher(name="100% Pulp", country="DE", established_year=None),
        ]
    )
    session.flush()
    return session


def names(session: Session, stmt) -> set[str]:
    return {p.name for p in session.scalars(stmt)}


BASE = select(Publisher)


def test_escape_like():
    assert escape_like(r"50%_\x") == r"50\%\_\\x"


def test_search_is_case_insensitive(seeded_session):
    stmt = apply_search(BASE, "PENGUIN", SEARCH_COLUMNS)
    assert names(seeded_session, stmt) == {"Penguin Books"}


def test_search_spans_multiple_columns(seeded_session):
    stmt = apply_search(BASE, "uk", SEARCH_COLUMNS)
    assert names(seeded_session, stmt) == {"Penguin Books"}
    assert len(names(seeded_session, apply_search(BASE, "us", SEARCH_COLUMNS))) == 3


def test_search_escapes_wildcards(seeded_session):
    stmt = apply_search(BASE, "%", SEARCH_COLUMNS)
    assert names(seeded_session, stmt) == {"100% Pulp"}
    assert names(seeded_session, apply_search(BASE, "_", SEARCH_COLUMNS)) == set()


@pytest.mark.parametrize("q", [None, "", "   "])
def test_blank_search_means_no_filter(seeded_session, q):
    stmt = apply_search(BASE, q, SEARCH_COLUMNS)
    assert len(names(seeded_session, stmt)) == 5


def test_exact_filter(seeded_session):
    stmt = apply_eq(BASE, Publisher.country, "US")
    assert names(seeded_session, stmt) == {"O'Reilly Media", "Ace", "Tor"}
    assert len(names(seeded_session, apply_eq(BASE, Publisher.country, None))) == 5


def test_range_filter(seeded_session):
    year = Publisher.established_year
    assert names(seeded_session, apply_range(BASE, year, minimum=1950)) == {
        "O'Reilly Media",
        "Ace",
        "Tor",
    }
    assert names(seeded_session, apply_range(BASE, year, maximum=1950)) == {
        "Penguin Books"
    }
    assert names(seeded_session, apply_range(BASE, year, 1950, 1979)) == {
        "O'Reilly Media",
        "Ace",
    }
    assert len(names(seeded_session, apply_range(BASE, year))) == 5


def test_in_filter(seeded_session):
    stmt = apply_in(BASE, Publisher.country, ["UK", "DE"])
    assert names(seeded_session, stmt) == {"Penguin Books", "100% Pulp"}
    assert len(names(seeded_session, apply_in(BASE, Publisher.country, None))) == 5
    assert len(names(seeded_session, apply_in(BASE, Publisher.country, []))) == 5


@pytest.fixture
def client(seeded_session):
    sort = sort_dependency(
        {"name": Publisher.name}, default="name", tiebreaker=Publisher.id
    )
    app = FastAPI()

    @app.get("/publishers", response_model=Page[str])
    def list_publishers(
        orders: Annotated[list[ColumnElement[Any]], Depends(sort)],
        params: Pagination,
        q: SearchQuery = None,
        country: Annotated[list[str] | None, Query()] = None,
        min_year: int | None = None,
        max_year: int | None = None,
    ):
        stmt = select(Publisher)
        stmt = apply_search(stmt, q, SEARCH_COLUMNS)
        stmt = apply_in(stmt, Publisher.country, country)
        stmt = apply_range(stmt, Publisher.established_year, min_year, max_year)
        rows, total = paginate(seeded_session, stmt.order_by(*orders), params)
        return Page.create([r.name for r in rows], total, params)

    return TestClient(app)


def test_filters_sorting_and_pagination_together(client):
    body = client.get(
        "/publishers",
        params={"country": "US", "min_year": 1960, "sort": "-name", "size": 1},
    ).json()
    assert body["total"] == 2
    assert body["pages"] == 2
    assert body["items"] == ["Tor"]


def test_repeated_query_param_builds_in_filter(client):
    body = client.get("/publishers", params=[("country", "UK"), ("country", "DE")])
    assert body.json()["items"] == ["100% Pulp", "Penguin Books"]


def test_q_over_http(client):
    body = client.get("/publishers", params={"q": "reilly"}).json()
    assert body["items"] == ["O'Reilly Media"]
