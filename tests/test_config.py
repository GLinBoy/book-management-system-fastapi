import pytest
from pydantic import ValidationError

from app.core.config import AppEnv, Settings


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in (
        "APP_ENV",
        "DATABASE_URL",
        "SEED_ON_STARTUP",
        "LOG_LEVEL",
        "DB_POOL_SIZE",
        "DB_MAX_OVERFLOW",
        "DB_POOL_TIMEOUT",
        "DB_POOL_PRE_PING",
    ):
        monkeypatch.delenv(name, raising=False)


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


def test_seed_on_startup_defaults_off():
    assert make().seed_on_startup is False


def test_seed_on_startup_from_env(monkeypatch):
    monkeypatch.setenv("SEED_ON_STARTUP", "true")
    assert make().seed_on_startup is True


def test_database_url_overrides_profile_defaults(monkeypatch):
    url = "sqlite:///custom.db"
    monkeypatch.setenv("DATABASE_URL", url)
    assert make().effective_database_url == url

    monkeypatch.setenv("APP_ENV", "test")
    assert make().effective_database_url == url


def test_log_level_is_uppercased(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "debug")
    assert make().log_level == "DEBUG"


def test_invalid_log_level_rejected(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "verbose")
    with pytest.raises(ValidationError):
        make()


def test_pool_settings_from_env(monkeypatch):
    monkeypatch.setenv("DB_POOL_SIZE", "7")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "3")
    monkeypatch.setenv("DB_POOL_TIMEOUT", "5")
    monkeypatch.setenv("DB_POOL_PRE_PING", "false")

    s = make()
    assert s.db_pool_size == 7
    assert s.db_max_overflow == 3
    assert s.db_pool_timeout == 5
    assert s.db_pool_pre_ping is False
