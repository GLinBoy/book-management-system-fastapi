import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.pagination import Page, Pagination, PaginationParams, paginate
from app.core.pagination import PageParams
from app.models import Publisher


@pytest.fixture
def seeded_session(session):
    session.add_all(Publisher(name=f"P{i:02d}") for i in range(25))
    session.flush()
    return session


@pytest.fixture
def client(seeded_session):
    app = FastAPI()

    @app.get("/publishers", response_model=Page[str])
    def list_publishers(params: Pagination):
        stmt = select(Publisher).order_by(Publisher.name)
        rows, total = paginate(seeded_session, stmt, params)
        return Page.create([r.name for r in rows], total, params)

    return TestClient(app)


def test_page_params_defaults():
    params = PageParams()
    assert (params.page, params.size) == (1, 20)
    assert params.offset == 0


@pytest.mark.parametrize(("page", "size"), [(1, 1), (2, 20), (3, 100)])
def test_page_params_offset(page, size):
    assert PageParams(page=page, size=size).offset == (page - 1) * size


@pytest.mark.parametrize(
    "kwargs", [{"page": 0}, {"page": -1}, {"size": 0}, {"size": 101}]
)
def test_page_params_rejects_invalid_values(kwargs):
    with pytest.raises(ValueError):
        PageParams(**kwargs)


def test_pagination_params_defaults_and_offset():
    assert (PaginationParams().page, PaginationParams().size) == (1, 20)
    assert PaginationParams(page=3, size=10).offset == 20


@pytest.mark.parametrize(
    ("total", "size", "pages"),
    [(0, 20, 0), (1, 20, 1), (20, 20, 1), (21, 20, 2), (100, 10, 10)],
)
def test_page_create_pages(total, size, pages):
    page = Page[int].create([], total=total, params=PaginationParams(size=size))
    assert page.pages == pages
    assert (page.total, page.page, page.size) == (total, 1, size)


def test_paginate_returns_requested_page(seeded_session):
    stmt = select(Publisher).order_by(Publisher.name)
    rows, total = paginate(seeded_session, stmt, PaginationParams(page=2, size=10))

    assert total == 25
    assert [r.name for r in rows] == [f"P{i:02d}" for i in range(10, 20)]


def test_first_page(client):
    body = client.get("/publishers", params={"page": 1, "size": 10}).json()
    assert body["total"] == 25
    assert body["pages"] == 3
    assert (body["page"], body["size"]) == (1, 10)
    assert body["items"][0] == "P00"
    assert len(body["items"]) == 10


def test_last_page_is_partial(client):
    body = client.get("/publishers", params={"page": 3, "size": 10}).json()
    assert len(body["items"]) == 5
    assert body["items"][-1] == "P24"


def test_page_past_the_end_is_empty(client):
    body = client.get("/publishers", params={"page": 9, "size": 10}).json()
    assert body["items"] == []
    assert body["total"] == 25


def test_defaults(client):
    body = client.get("/publishers").json()
    assert (body["page"], body["size"]) == (1, 20)
    assert body["pages"] == 2


def test_empty_result_has_zero_pages(session):
    stmt = select(Publisher).where(Publisher.name == "nobody")
    rows, total = paginate(session, stmt, PaginationParams(page=1, size=10))
    page = Page[str].create([], total, PaginationParams(page=1, size=10))
    assert rows == []
    assert page.pages == 0


@pytest.mark.parametrize(
    "params",
    [{"page": 0}, {"size": 0}, {"size": 101}, {"page": "x"}],
)
def test_invalid_params_return_422(client, params):
    assert client.get("/publishers", params=params).status_code == 422
