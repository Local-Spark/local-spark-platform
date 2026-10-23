"""Deterministic windows group concurrent material without crossing boundaries."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.services.whatsapp_routing import material_group


def test_same_sender_business_and_window_share_group_even_when_out_of_order():
    tenant, business = uuid4(), uuid4()
    beginning = datetime(2026, 10, 23, 12, 0, tzinfo=UTC)
    later = beginning + timedelta(minutes=9, seconds=59)
    assert material_group(tenant, business, "sender", later) == material_group(tenant, business, "sender", beginning)


def test_group_changes_at_time_and_identity_boundaries():
    tenant, business = uuid4(), uuid4()
    instant = datetime(2026, 10, 23, 12, 10, tzinfo=UTC)
    first = material_group(tenant, business, "sender", instant)
    assert first != material_group(tenant, business, "sender", instant - timedelta(microseconds=1))
    assert first != material_group(uuid4(), business, "sender", instant)
    assert first != material_group(tenant, uuid4(), "sender", instant)
    assert first != material_group(tenant, business, "different", instant)
