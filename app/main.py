import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.v1.router import router as v1_router
from app.core.config import AppEnv, Settings, get_settings
from app.core.database import get_session_factory
from app.core.errors import register_exception_handlers
from app.core.logging_config import configure_logging
from app.core.middleware import RequestIdMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    _seed_on_startup(get_settings())
    yield


def _seed_on_startup(settings: Settings) -> None:
    if not settings.seed_on_startup:
        return
    if settings.app_env is AppEnv.PROD:
        logger.warning("SEED_ON_STARTUP is ignored when APP_ENV=prod")
        return
    # Faker is a development dependency, so import the seed module only when it runs.
    from app.seed import seed_database

    with get_session_factory()() as session:
        summary = seed_database(session)
    if summary.skipped:
        logger.info("Startup seed skipped: data already exists")
    else:
        logger.info(
            "Startup seed inserted %d publishers, %d authors, %d categories, %d books",
            summary.publishers,
            summary.authors,
            summary.categories,
            summary.books,
        )


def create_app() -> FastAPI:
    configure_logging(get_settings().log_level)
    application = FastAPI(
        title="Book Management System API",
        version="0.1.0",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "publishers", "description": "Manage publishers."},
            {"name": "authors", "description": "Manage authors."},
            {"name": "categories", "description": "Manage categories."},
            {"name": "books", "description": "Manage books."},
        ],
    )
    application.add_middleware(RequestIdMiddleware)
    register_exception_handlers(application)
    application.include_router(health_router)
    application.include_router(v1_router)
    return application


app = create_app()
