from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from app.core.config import get_settings
from app.models import Base

ROOT = Path(__file__).resolve().parent.parent
EXPECTED_TABLES = set(Base.metadata.tables)


def _config() -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    return cfg


def test_single_migration_head() -> None:
    heads = ScriptDirectory.from_config(_config()).get_heads()
    assert len(heads) <= 1


def test_upgrade_head_runs_on_sqlite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # dev URL is sqlite:///./dev.db, so the file lands here
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_ENV", "dev")
    get_settings.cache_clear()
    try:
        command.upgrade(_config(), "head")
    finally:
        get_settings.cache_clear()


def test_initial_migration_round_trip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    url = f"sqlite:///{tmp_path / 'roundtrip.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("APP_ENV", "dev")
    get_settings.cache_clear()
    engine = create_engine(url)
    try:
        command.upgrade(_config(), "head")
        assert EXPECTED_TABLES <= set(inspect(engine).get_table_names())

        command.downgrade(_config(), "base")
        assert EXPECTED_TABLES.isdisjoint(inspect(engine).get_table_names())

        command.upgrade(_config(), "head")
        assert EXPECTED_TABLES <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()
        get_settings.cache_clear()
