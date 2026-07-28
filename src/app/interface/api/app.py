"""FastAPI application factory."""

from fastapi import FastAPI

from app.infrastructure.config.settings import get_settings
from app.infrastructure.observability.logging import configure_logging
from app.interface.api.routers import health


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(debug=settings.debug)

    app = FastAPI(title=settings.app_name, version="0.1.0", debug=settings.debug)
    app.include_router(health.router)
    return app


app = create_app()
