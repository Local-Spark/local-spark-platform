from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import DBAPIError

from app.schemas.reference_own_review import OwnBusinessReviewConfirm
from app.services.auth import AuthError
from app.services.reference_own_review import _CODES, ReferenceOwnReviewService


class Database:
    def __init__(self, value):
        self.value = value
        self.calls = []

    @asynccontextmanager
    async def transaction(self, tenant, actor):
        self.calls.append((tenant, actor))
        yield self

    async def scalar(self, sql, values):
        self.calls.append((str(sql), values))
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


@pytest.mark.parametrize("value", ["", " ", " place", "place ", "x" * 2049, "\ud800"])
def test_invalid_identity_cannot_be_confirmed(value):
    with pytest.raises(ValidationError):
        OwnBusinessReviewConfirm(operation_id=uuid4(), place_id=value)


def test_explicit_none_and_identifier_are_valid():
    for value in (None, "place-123"):
        assert OwnBusinessReviewConfirm(operation_id=uuid4(), place_id=value).place_id == value
    with pytest.raises(ValidationError):
        OwnBusinessReviewConfirm(operation_id=uuid4())
    with pytest.raises(ValidationError):
        OwnBusinessReviewConfirm(operation_id=uuid4(), place_id=None, name="not-stored")


@pytest.mark.parametrize("method", ["read", "confirm"])
@pytest.mark.parametrize("code,status", list(_CODES.items()) + [("PRIVATE_DETAIL", 503)])
async def test_service_translates_only_allowlisted_failures(method, code, status):
    db = Database(DBAPIError(None, None, Exception(code + " private-details")))
    service = ReferenceOwnReviewService(db)
    args = [uuid4() for _ in range(4)]
    if method == "confirm":
        args.append(OwnBusinessReviewConfirm(operation_id=uuid4(), place_id=None))
    with pytest.raises(AuthError) as error:
        await getattr(service, method)(*args)
    assert error.value.status == status
    assert "private-details" not in str(error.value)


async def test_service_preserves_scope_and_exact_selection():
    tenant, business, actor, search, operation = [uuid4() for _ in range(5)]
    db = Database({"search_id": str(search), "status": "resolved"})
    service = ReferenceOwnReviewService(db)
    assert (await service.read(tenant, business, actor, search)).search_id == search
    await service.confirm(
        tenant, business, actor, search, OwnBusinessReviewConfirm(operation_id=operation, place_id=None)
    )
    assert db.calls[0] == db.calls[2] == (tenant, actor)
    assert db.calls[3][1] == {"business": business, "search": search, "operation": operation, "place": None}
