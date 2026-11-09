import logging
import re

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.core.logging_config import request_id_ctx
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    application = create_app()
    router = APIRouter()

    @router.get("/_ctx")
    def read_context() -> dict[str, str | None]:
        return {"request_id": request_id_ctx.get()}

    application.include_router(router)
    return TestClient(application)


def test_generates_request_id(client):
    response = client.get("/_ctx")
    assert re.fullmatch(r"[0-9a-f]{32}", response.headers["x-request-id"])


def test_echoes_valid_incoming_request_id(client):
    response = client.get("/_ctx", headers={"X-Request-ID": "abc-123.DEF_4"})
    assert response.headers["x-request-id"] == "abc-123.DEF_4"


@pytest.mark.parametrize("value", ["bad id!", "x" * 65])
def test_replaces_invalid_incoming_request_id(client, value):
    response = client.get("/_ctx", headers={"X-Request-ID": value})
    assert response.headers["x-request-id"] != value
    assert re.fullmatch(r"[0-9a-f]{32}", response.headers["x-request-id"])


def test_request_id_visible_inside_handler(client):
    response = client.get("/_ctx", headers={"X-Request-ID": "trace-1"})
    assert response.json() == {"request_id": "trace-1"}


def test_error_responses_include_request_id(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert "x-request-id" in response.headers


def test_access_log_line(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.access"):
        client.get("/_ctx?secret=1")
    messages = [r.getMessage() for r in caplog.records if r.name == "app.access"]
    assert any("GET /_ctx -> 200" in m for m in messages)
    assert not any("secret" in m for m in messages)


def test_log_level_is_normalized():
    assert Settings(_env_file=None, log_level="debug").log_level == "DEBUG"


def test_invalid_log_level_is_rejected():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, log_level="loud")
