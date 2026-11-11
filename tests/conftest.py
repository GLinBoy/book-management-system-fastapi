import pytest
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import create_db_engine
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
