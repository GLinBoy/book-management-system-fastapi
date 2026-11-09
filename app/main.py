from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging_config import configure_logging
from app.core.middleware import RequestIdMiddleware


def create_app() -> FastAPI:
    configure_logging(get_settings().log_level)
    application = FastAPI()
    application.add_middleware(RequestIdMiddleware)
    register_exception_handlers(application)
    application.include_router(health_router)
    return application


app = create_app()
