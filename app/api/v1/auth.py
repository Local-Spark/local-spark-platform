"""HTTP adapter for native auth. Cookies are never returned as JSON or logged."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from app.schemas.auth import ActionInput, EmailInput, LoginInput, MFAInput, RegisterInput, ResetInput
from app.services.auth import AuthError, AuthService


def service(request: Request) -> AuthService:
    return request.app.state.identity_verifier  # type: ignore[no-any-return]


Service = Annotated[AuthService, Depends(service)]


def origin_guard(request: Request) -> None:
    if request.headers.get("origin") not in request.app.state.settings.auth_origins:
        raise AuthError("ORIGIN_REJECTED", 403)


auth_router = APIRouter(prefix="/api/v1/auth", tags=["authentication"], dependencies=[Depends(origin_guard)])
GENERIC = {"message": "Se o cadastro permitir, você receberá um e-mail com os próximos passos."}
PATH = "/"


def cookie_names(request: Request) -> tuple[str, str]:
    prefix = "__Host-" if request.app.state.settings.public_web_url.startswith("https://") else ""
    return f"{prefix}spark-refresh", f"{prefix}spark-csrf"


def reply(request: Request, data: dict[str, Any]) -> JSONResponse:
    refresh, csrf = data.pop("_refresh", None), data.pop("_csrf", None)
    response = JSONResponse(data, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})
    if refresh:
        refresh_name, csrf_name = cookie_names(request)
        secure = request.app.state.settings.public_web_url.startswith("https://")
        response.set_cookie(
            refresh_name, refresh, httponly=True, secure=secure, samesite="lax", path=PATH, max_age=2592000
        )
        response.set_cookie(csrf_name, csrf, httponly=False, secure=secure, samesite="lax", path=PATH, max_age=2592000)
    return response


def refresh_credentials(request: Request) -> tuple[str, str]:
    refresh_name, csrf_name = cookie_names(request)
    raw, csrf = request.cookies.get(refresh_name), request.cookies.get(csrf_name)
    if not raw:
        raise AuthError("INVALID_SESSION")
    if not csrf or request.headers.get("x-csrf-token") != csrf:
        raise AuthError("CSRF_FAILED", 403)
    return raw, csrf


async def throttle(request: Request, auth: AuthService, operation: str, identifier: str) -> None:
    await auth.throttle(operation, request.client.host if request.client else "unknown", identifier)


@auth_router.post("/register", status_code=202)
async def register(payload: RegisterInput, request: Request, auth: Service) -> dict[str, str]:
    await throttle(request, auth, "register", str(payload.email))
    await auth.register(str(payload.email), payload.display_name, payload.password.get_secret_value())
    return GENERIC


@auth_router.post("/login")
async def login(payload: LoginInput, request: Request, auth: Service) -> JSONResponse:
    await throttle(request, auth, "login", str(payload.email))
    return reply(request, await auth.login(str(payload.email), payload.password.get_secret_value()))


@auth_router.post("/mfa/verify")
async def verify_mfa(payload: MFAInput, request: Request, auth: Service) -> JSONResponse:
    await throttle(request, auth, "mfa", payload.token.get_secret_value())
    return reply(request, await auth.verify_mfa(payload.token.get_secret_value(), payload.code.get_secret_value()))


@auth_router.post("/refresh")
async def refresh(request: Request, auth: Service) -> JSONResponse:
    raw, csrf = refresh_credentials(request)
    return reply(request, await auth.refresh(raw, csrf))


@auth_router.post("/logout", status_code=204)
async def logout(request: Request, auth: Service) -> Response:
    raw, csrf = refresh_credentials(request)
    await auth.logout(raw, csrf)
    response = Response(status_code=204)
    for name in cookie_names(request):
        response.delete_cookie(
            name,
            path=PATH,
            secure=request.app.state.settings.public_web_url.startswith("https://"),
            httponly=name.endswith("refresh"),
            samesite="lax",
        )
    return response


@auth_router.post("/verification-request", status_code=202)
async def verification_request(payload: EmailInput, request: Request, auth: Service) -> dict[str, str]:
    await throttle(request, auth, "verify", str(payload.email))
    await auth.request_action(str(payload.email), "verify")
    return GENERIC


@auth_router.post("/password-reset-request", status_code=202)
async def password_reset_request(payload: EmailInput, request: Request, auth: Service) -> dict[str, str]:
    await throttle(request, auth, "reset", str(payload.email))
    await auth.request_action(str(payload.email), "reset")
    return GENERIC


@auth_router.post("/verify-email")
async def verify_email(payload: ActionInput, request: Request, auth: Service) -> dict[str, str]:
    await throttle(request, auth, "action", payload.token.get_secret_value())
    await auth.consume_action(payload.token.get_secret_value(), "verify")
    return {"message": "E-mail confirmado. Entre na sua conta para continuar."}


@auth_router.post("/reset-password")
async def reset_password(payload: ResetInput, request: Request, auth: Service) -> dict[str, str]:
    await throttle(request, auth, "action", payload.token.get_secret_value())
    await auth.consume_action(payload.token.get_secret_value(), "reset", payload.password.get_secret_value())
    return {"message": "Senha atualizada. Entre novamente."}
