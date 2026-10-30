"""Exact private traces are exposed only through authenticated, non-cacheable routes."""

from unittest.mock import AsyncMock
from uuid import uuid4

from app.services.editorial_proposals import EditorialProposalService
from app.services.visual_request_trace import VisualRequestTraceService
from app.tests.unit.test_core import access_token


def test_visual_trace_endpoint_requires_identity_and_disables_caching(client, settings, monkeypatch):
    tenant, business, actor, preview = (uuid4() for _ in range(4))
    read = AsyncMock(return_value={"trace_status": "prepared", "request": {"prompt": "fictício"}})
    monkeypatch.setattr(VisualRequestTraceService, "read", read)
    path = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews/{preview}/request-trace"
    assert client.get(path).status_code == 401
    read.assert_not_awaited()
    response = client.get(path, headers={"Authorization": f"Bearer {access_token(settings, actor)}"})
    assert response.status_code == 200 and response.json()["request"]["prompt"] == "fictício"
    assert response.headers["cache-control"] == "no-store"
    read.assert_awaited_once_with(tenant, business, actor, preview)


def test_editorial_trace_endpoint_requires_identity_and_disables_caching(client, settings, monkeypatch):
    tenant, business, actor, proposal = (uuid4() for _ in range(4))
    read = AsyncMock(return_value={"trace_status": "prepared", "request": {"body": "fictício"}})
    monkeypatch.setattr(EditorialProposalService, "get_request_trace", read)
    path = f"/api/v1/organizations/{tenant}/businesses/{business}/editorial-proposals/{proposal}/request-trace"
    assert client.get(path).status_code == 401
    read.assert_not_awaited()
    response = client.get(path, headers={"Authorization": f"Bearer {access_token(settings, actor)}"})
    assert response.status_code == 200 and response.json()["request"]["body"] == "fictício"
    assert response.headers["cache-control"] == "no-store"
    read.assert_awaited_once_with(tenant, business, actor, proposal)
