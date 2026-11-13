import threading

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import database
from app.core.config import Settings
from app.core.database import create_db_engine, get_db


def sqlite_settings(tmp_path) -> Settings:
    return Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 't.db'}")


def test_sqlite_foreign_keys_enabled(tmp_path):
    engine = create_db_engine(sqlite_settings(tmp_path))
    with engine.connect() as conn:
        assert conn.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1


def test_postgres_uses_pool_settings():
    settings = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://u:p@localhost:5432/db",
        db_pool_size=7,
    )
    engine = create_db_engine(settings)
    assert engine.pool.size() == 7


def test_memory_sqlite_uses_static_pool():
    engine = create_db_engine(Settings(_env_file=None, database_url="sqlite://"))
    try:
        assert isinstance(engine.pool, StaticPool)
    finally:
        engine.dispose()


def test_memory_sqlite_is_shared_across_threads():
    engine = create_db_engine(Settings(_env_file=None, database_url="sqlite://"))
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE t (id INTEGER)"))
            conn.execute(text("INSERT INTO t VALUES (1)"))

        counts: list[int] = []

        def read_count() -> None:
            with engine.connect() as conn:
                counts.append(conn.execute(text("SELECT COUNT(*) FROM t")).scalar_one())

        thread = threading.Thread(target=read_count)
        thread.start()
        thread.join()

        assert counts == [1]
    finally:
        engine.dispose()


@pytest.fixture
def patched_factory(tmp_path, monkeypatch):
    engine = create_db_engine(sqlite_settings(tmp_path))
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE t (id INTEGER)"))
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(database, "get_session_factory", lambda: factory)
    return engine


def count(engine) -> int:
    with engine.connect() as conn:
        return conn.execute(text("SELECT COUNT(*) FROM t")).scalar_one()


def test_get_db_commits_on_success(patched_factory):
    gen = get_db()
    session = next(gen)
    session.execute(text("INSERT INTO t VALUES (1)"))
    with pytest.raises(StopIteration):
        next(gen)
    assert count(patched_factory) == 1


def test_get_db_rolls_back_on_error(patched_factory):
    gen = get_db()
    session = next(gen)
    session.execute(text("INSERT INTO t VALUES (1)"))
    with pytest.raises(RuntimeError):
        gen.throw(RuntimeError("boom"))
    assert count(patched_factory) == 0
