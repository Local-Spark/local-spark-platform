"""Deferred media changes execute only validated owner commands."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.auth import AuthError
from app.services.brand_kits import BrandKitService
from app.services.business_collection import BusinessCollectionService
from app.services.visual_pending_media import apply_kit_pending_in_session, apply_photo_pending_in_session


async def test_apply_kit_requires_known_kind_and_owner(monkeypatch):
    session = object()
    tenant, business, actor, operation = (uuid4() for _ in range(4))
    owner, apply = AsyncMock(), AsyncMock()
    monkeypatch.setattr(BrandKitService, "_owner", owner)
    monkeypatch.setattr(BrandKitService, "_confirm_in_session", apply)
    with pytest.raises(AuthError, match="VISUAL_PENDING_KIND_INVALID"):
        await apply_kit_pending_in_session(session, tenant, business, actor, "other", {})
    owner.assert_not_awaited()
    await apply_kit_pending_in_session(
        session, tenant, business, actor, "kit_confirm", {"operation_id": str(operation), "expected_version": 1}
    )
    owner.assert_awaited_once_with(session, tenant, business, actor)
    assert apply.await_args.args[-1].operation_id == operation


async def test_apply_photo_update_delete_and_unknown_kind(monkeypatch):
    session = object()
    tenant, business, actor, photo, operation = (uuid4() for _ in range(5))
    owner, update, delete = AsyncMock(), AsyncMock(), AsyncMock()
    monkeypatch.setattr("app.services.visual_pending_media.require_catalog_owner", owner)
    monkeypatch.setattr(BusinessCollectionService, "_update_in_session", update)
    monkeypatch.setattr(BusinessCollectionService, "_delete_in_session", delete)
    payload = {
        "photo_id": str(photo),
        "body": {
            "operation_id": str(operation),
            "expected_version": 1,
            "title": "Produto",
            "item_id": str(uuid4()),
            "status": "active",
        },
    }
    await apply_photo_pending_in_session(session, tenant, business, actor, "photo_update", payload)
    assert update.await_args.args[-2] == photo
    await apply_photo_pending_in_session(
        session,
        tenant,
        business,
        actor,
        "photo_delete",
        {
            "photo_id": str(photo),
            "operation_id": str(operation),
            "expected_version": 1,
        },
    )
    delete.assert_awaited_once_with(session, tenant, business, actor, photo, operation, 1)
    with pytest.raises(AuthError, match="VISUAL_PENDING_KIND_INVALID"):
        await apply_photo_pending_in_session(session, tenant, business, actor, "other", {})
    assert owner.await_count == 3
