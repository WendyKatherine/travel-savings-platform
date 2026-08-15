"""FastAPI application factory.

Exposes the module-level ``app`` instance that uvicorn loads
(``app.interface.api.app:app``). Tests call create_app() to build
fresh instances and override dependencies.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.exceptions import DomainError
from app.infrastructure.config.settings import get_settings
from app.infrastructure.observability.logging import configure_logging
from app.interface.api.routers import goals, health


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(debug=settings.debug)

    app = FastAPI(title=settings.app_name, version="0.1.0", debug=settings.debug)

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        """Map intentional domain rejections to HTTP 400.

        Business-rule violations are the client's fault, but they stay
        distinct from FastAPI's 422 schema validation. Anything else
        (e.g. a stray ValueError from a bug) keeps bubbling up as 500.
        """
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    app.include_router(health.router)
    app.include_router(goals.router)

    return app


app = create_app()
