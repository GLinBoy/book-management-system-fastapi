import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import create_db_engine, get_db
from app.main import create_app
from app.models import Base


@pytest.fixture
def engine(tmp_path):
    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 't.db'}")
    engine = create_db_engine(settings)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(session):
    application = create_app()

    def override_get_db():
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
