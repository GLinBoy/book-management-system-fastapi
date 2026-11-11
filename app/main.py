from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging_config import configure_logging
from app.core.middleware import RequestIdMiddleware


def create_app() -> FastAPI:
    configure_logging(get_settings().log_level)
    application = FastAPI(
        title="Book Management System API",
        version="0.1.0",
        openapi_tags=[
            {"name": "publishers", "description": "Manage publishers."},
        ],
    )
    application.add_middleware(RequestIdMiddleware)
    register_exception_handlers(application)
    application.include_router(health_router)
    application.include_router(v1_router)
    return application


app = create_app()
