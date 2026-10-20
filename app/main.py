"""Application factory with versioned routers, lifespan and safe JSON diagnostics."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app import __version__
from app.api.v1.api import api_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, request_id, request_id_context
from app.db.session import Database
from app.services.business import AccessDenied, IdempotencyConflict

logger = logging.getLogger("local_spark.api")


def create_app(settings: Settings | None = None, database: Database | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.database = database or Database(settings)
        try:
            yield
        finally:
            if database is None:
                await application.state.database.close()

    application = FastAPI(
        title=settings.project_name,
        version=__version__,
        lifespan=lifespan,
        openapi_url="/api/v1/openapi.json",
        docs_url="/docs" if settings.environment in {"testing", "development"} else None,
        redoc_url=None,
    )
    application.state.settings = settings
    application.include_router(api_router)

    @application.middleware("http")
    async def diagnostics(request: Request, call_next):  # type: ignore[no-untyped-def]
        correlation = request_id(request.headers.get("X-Request-ID"))
        token = request_id_context.set(correlation)
        start = perf_counter()
        try:
            try:
                response = await call_next(request)
            except Exception:
                logger.error("http.request.failed", extra={"error_code": "INTERNAL_ERROR"}, exc_info=True)
                response = JSONResponse(
                    status_code=500, content={"error_code": "INTERNAL_ERROR", "request_id": correlation}
                )
            response.headers["X-Request-ID"] = correlation
            logger.info(
                "http.request.completed",
                extra={
                    "status_code": response.status_code,
                    "duration_ms": round((perf_counter() - start) * 1000),
                },
            )
            return response
        finally:
            request_id_context.reset(token)

    @application.exception_handler(AccessDenied)
    async def access_denied(request: Request, exc: AccessDenied) -> JSONResponse:
        return JSONResponse(status_code=403, content={"error_code": "ACCESS_DENIED"})

    @application.exception_handler(IdempotencyConflict)
    async def conflict(request: Request, exc: IdempotencyConflict) -> JSONResponse:
        return JSONResponse(status_code=409, content={"error_code": "IDEMPOTENCY_CONFLICT"})

    @application.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse("/docs" if settings.environment in {"testing", "development"} else "/health/live")

    @application.get("/health/live", tags=["health"])
    async def live() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @application.get("/health/ready", tags=["health"])
    async def ready(request: Request) -> JSONResponse:
        try:
            healthy = await request.app.state.database.ready()
        except Exception:
            healthy = False
        return JSONResponse(
            status_code=200 if healthy else 503, content={"status": "ready" if healthy else "not_ready"}
        )

    return application
