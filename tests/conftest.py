import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import create_db_engine, get_db
from app.main import create_app
from app.models import Base

DEFAULT_TEST_DATABASE_URL = "sqlite://"


def _database_url() -> str:
    """Database for the shared fixtures; TEST_DATABASE_URL switches dialect."""
    return os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)


@pytest.fixture
def engine() -> Iterator[Engine]:
    """Database engine shared by every connection in a test.

    In-memory SQLite by default. Set TEST_DATABASE_URL to run the suite
    against another database, such as PostgreSQL. The schema is recreated
    for every test so the target database must be dedicated to testing.
    """
    settings = Settings(_env_file=None, database_url=_database_url())
    engine = create_db_engine(settings)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    """Session inside a transaction that is rolled back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    application = create_app()

    def override_get_db() -> Iterator[Session]:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

    application.dependency_overrides[get_db] = override_get_db
    with TestClient(application) as client:
        yield client
    application.dependency_overrides.clear()
