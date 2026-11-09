import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    application = create_app()
    router = APIRouter(prefix="/_errors")

    @router.get("/not-found")
    def raise_not_found() -> None:
        raise NotFoundError("Book 42 not found")

    @router.get("/conflict")
    def raise_conflict() -> None:
        raise ConflictError("ISBN already exists")

    @router.get("/integrity")
    def raise_integrity() -> None:
        raise IntegrityError(
            "INSERT INTO books ...", {}, Exception("UNIQUE failed: books.isbn")
        )

    @router.get("/items/{item_id}")
    def get_item(item_id: int) -> dict[str, int]:
        return {"id": item_id}

    application.include_router(router)
    return TestClient(application)


def test_not_found_error(client):
    response = client.get("/_errors/not-found")
    assert response.status_code == 404
    assert response.json() == {
        "code": "not_found",
        "message": "Book 42 not found",
        "details": None,
    }


def test_conflict_error(client):
    response = client.get("/_errors/conflict")
    assert response.status_code == 409
    assert response.json()["code"] == "conflict"
    assert response.json()["message"] == "ISBN already exists"


def test_integrity_error_is_409_without_leaking_internals(client):
    response = client.get("/_errors/integrity")
    assert response.status_code == 409
    assert response.json()["code"] == "conflict"
    assert "books" not in response.text
    assert "INSERT" not in response.text


def test_validation_error_is_422_with_details(client):
    response = client.get("/_errors/items/abc")
    body = response.json()
    assert response.status_code == 422
    assert body["code"] == "validation_error"
    assert body["details"][0]["loc"] == ["path", "item_id"]


def test_unknown_route_uses_same_body(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert set(response.json()) == {"code", "message", "details"}
    assert response.json()["code"] == "not_found"


def test_method_not_allowed_keeps_allow_header(client):
    response = client.post("/_errors/not-found")
    assert response.status_code == 405
    assert response.json()["code"] == "method_not_allowed"
    assert "GET" in response.headers["allow"]
