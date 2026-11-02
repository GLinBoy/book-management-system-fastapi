import pytest
from pydantic import ValidationError

from app.core.config import AppEnv, Settings


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)


def make() -> Settings:
    return Settings(_env_file=None)


def test_dev_defaults_to_sqlite():
    s = make()
    assert s.app_env is AppEnv.DEV
    assert s.effective_database_url == "sqlite:///./dev.db"


def test_test_env_uses_own_sqlite(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    assert make().effective_database_url == "sqlite:///./test.db"


def test_prod_without_url_fails(monkeypatch):
    monkeypatch.setenv("APP_ENV", "prod")
    with pytest.raises(ValidationError):
        make()


def test_prod_with_url(monkeypatch):
    url = "postgresql+psycopg://u:p@localhost:5432/books"
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("DATABASE_URL", url)
    assert make().effective_database_url == url


def test_invalid_env_rejected(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(ValidationError):
        make()
