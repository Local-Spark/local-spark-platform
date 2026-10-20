"""Verify an already-issued JWT; there is no public token issuance endpoint."""

from uuid import UUID

import jwt

from app.core.config import Settings


def decode_actor(token: str, settings: Settings) -> UUID:
    claims = jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=["HS256"],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
        options={"require": ["exp", "iat", "sub", "iss", "aud"]},
    )
    try:
        return UUID(claims["sub"])
    except (ValueError, TypeError, AttributeError) as exc:
        raise jwt.InvalidTokenError("Invalid subject") from exc
