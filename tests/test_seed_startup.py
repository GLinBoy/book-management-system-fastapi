import logging

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.main import create_app
from app.models import Book


def _count(engine, model) -> int:
    with Session(engine) as session:
        return session.scalar(select(func.count()).select_from(model)) or 0


def _make_app(engine, monkeypatch, **settings):
    config = Settings(_env_file=None, database_url="sqlite://", **settings)
    monkeypatch.setattr("app.main.get_settings", lambda: config)
    monkeypatch.setattr(
        "app.main.get_session_factory", lambda: sessionmaker(bind=engine)
    )
    return create_app()


def test_startup_seeds_when_enabled(engine, monkeypatch):
    application = _make_app(engine, monkeypatch, seed_on_startup=True)

    with TestClient(application) as client:
        assert client.get("/health").status_code == 200

    assert _count(engine, Book) == 300


def test_startup_does_not_seed_by_default(engine, monkeypatch):
    application = _make_app(engine, monkeypatch)

    with TestClient(application):
        pass

    assert _count(engine, Book) == 0


def test_startup_skips_when_data_exists(engine, monkeypatch, caplog):
    with Session(engine) as session:
        session.add(Book(title="Existing"))
        session.commit()
    application = _make_app(engine, monkeypatch, seed_on_startup=True)

    with caplog.at_level(logging.INFO, logger="app.main"), TestClient(application):
        pass

    assert _count(engine, Book) == 1
    assert "skipped" in caplog.text


def test_startup_never_seeds_in_prod(engine, monkeypatch, caplog):
    application = _make_app(engine, monkeypatch, app_env="prod", seed_on_startup=True)

    with (
        caplog.at_level(logging.WARNING, logger="app.main"),
        TestClient(application) as client,
    ):
        assert client.get("/health").status_code == 200

    assert _count(engine, Book) == 0
    assert "SEED_ON_STARTUP" in caplog.text
