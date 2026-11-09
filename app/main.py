from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.errors import register_exception_handlers


def create_app() -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    application.include_router(health_router)
    return application


app = create_app()
