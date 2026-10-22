"""Application factory with versioned routers, lifespan and safe JSON diagnostics."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse

from app import __version__
from app.adapters.meta_whatsapp import MetaWebhookError
from app.adapters.twilio_verify import TwilioVerify
from app.api.v1.api import api_router
from app.api.v1.auth import auth_router
from app.api.v1.billing import billing_router
from app.api.v1.onboarding import onboarding_router
from app.api.v1.phone_verification import phone_router
from app.api.v1.reference import reference_router
from app.api.v1.staff import staff_router
from app.api.v1.whatsapp import whatsapp_router
from app.api.v1.whatsapp_link import whatsapp_link_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, request_id, request_id_context
from app.db.session import Database
from app.services.auth import AuthError, AuthService
from app.services.billing import BillingError
from app.services.business import AccessDenied, IdempotencyConflict

logger = logging.getLogger("local_spark.api")


def create_app(
    settings: Settings | None = None,
    database: Database | None = None,
    auth_database: Database | None = None,
    billing_database: Database | None = None,
    meta_database: Database | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.database = database or Database(settings)
        application.state.auth_database = auth_database or Database(settings, auth=True)
        application.state.identity_verifier = AuthService(settings, application.state.auth_database)
        application.state.phone_provider = TwilioVerify(settings)
        application.state.billing_database = billing_database or (
            Database(settings, billing=True) if settings.billing_database_url else None
        )
        application.state.meta_database = meta_database or (
            Database(settings, meta=True) if settings.meta_webhook_mode == "cloud" else None
        )
        try:
            yield
        finally:
            if database is None:
                await application.state.database.close()
            if auth_database is None:
                await application.state.auth_database.close()
            if billing_database is None and application.state.billing_database is not None:
                await application.state.billing_database.close()
            if meta_database is None and application.state.meta_database is not None:
                await application.state.meta_database.close()
            await application.state.phone_provider.close()

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
    application.include_router(onboarding_router)
    application.include_router(auth_router)
    application.include_router(reference_router)
    application.include_router(billing_router)
    application.include_router(staff_router)
    application.include_router(phone_router)
    application.include_router(whatsapp_router)
    application.include_router(whatsapp_link_router)

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
            response.headers["Cache-Control"] = "no-store"
            response.headers["Referrer-Policy"] = "no-referrer"
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

    @application.exception_handler(AuthError)
    async def auth_error(request: Request, exc: AuthError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status, content={"error_code": exc.code}, headers={"Cache-Control": "no-store"}
        )

    @application.exception_handler(BillingError)
    async def billing_error(request: Request, exc: BillingError) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content={"error_code": exc.code})

    @application.exception_handler(MetaWebhookError)
    async def meta_error(request: Request, exc: MetaWebhookError) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content={"error_code": exc.code})

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "VALIDATION_ERROR",
                "detail": [
                    {"loc": list(error["loc"]), "type": error["type"], "msg": error["msg"]} for error in exc.errors()
                ],
            },
        )

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
            healthy = await request.app.state.database.ready() and await request.app.state.auth_database.ready()
            if healthy and settings.billing_mode != "disabled":
                healthy = await request.app.state.billing_database.ready()
            if healthy and settings.meta_webhook_mode != "disabled":
                healthy = await request.app.state.meta_database.ready()
        except Exception:
            healthy = False
        return JSONResponse(
            status_code=200 if healthy else 503, content={"status": "ready" if healthy else "not_ready"}
        )

    return application
