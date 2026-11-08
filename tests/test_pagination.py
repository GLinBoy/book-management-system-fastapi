import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.pagination import Page, Pagination, paginate
from app.core.config import Settings
from app.core.database import create_db_engine
from app.models import Base, Publisher


@pytest.fixture
def session(tmp_path):
    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'p.db'}")
    engine = create_db_engine(settings)
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        s.add_all(Publisher(name=f"P{i:02d}") for i in range(25))
        s.commit()
        yield s
    engine.dispose()


@pytest.fixture
def client(session):
    app = FastAPI()

    @app.get("/publishers", response_model=Page[str])
    def list_publishers(params: Pagination):
        stmt = select(Publisher).order_by(Publisher.name)
        rows, total = paginate(session, stmt, params)
        return Page.create([r.name for r in rows], total, params)

    return TestClient(app)


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
    from app.api.pagination import PaginationParams

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
