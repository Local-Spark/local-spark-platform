"""A context variable alone cannot grant continued generation or private review."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.services.editorial_consent_scope import VisualRunScope, admitted_visual_run
from app.services.visual_continuity import admitted_or_preserved


@pytest.mark.parametrize("mismatch", ["absent", "tenant", "business", "actor"])
async def test_ordinary_or_wrong_context_never_gets_a_financial_exception(mismatch):
    tenant, business, actor, source, operation = [uuid4() for _ in range(5)]
    session = Mock(scalar=AsyncMock(return_value=1))
    if mismatch == "absent":
        assert not await admitted_or_preserved(session, tenant, business, actor, source, None)
    else:
        scope = VisualRunScope(
            uuid4() if mismatch == "tenant" else tenant,
            uuid4() if mismatch == "business" else business,
            uuid4() if mismatch == "actor" else actor,
            operation,
            7,
        )
        with admitted_visual_run(scope):
            assert not await admitted_or_preserved(session, tenant, business, actor, source, None)
    session.scalar.assert_not_awaited()


@pytest.mark.parametrize("proof", [None, 1])
async def test_matching_scope_requires_durable_proof_of_the_operation_and_fence(proof):
    tenant, business, actor, source, operation = [uuid4() for _ in range(5)]
    session = Mock(scalar=AsyncMock(return_value=proof))
    with admitted_visual_run(VisualRunScope(tenant, business, actor, operation, 7)):
        assert await admitted_or_preserved(session, tenant, business, actor, source, None) is bool(proof)
    assert session.scalar.await_args.args[1] == {
        "tenant": tenant,
        "business": business,
        "actor": actor,
        "source": source,
        "operation": operation,
        "fence": 7,
    }
    # The exception cannot escape the scoped attempt and authorize another request.
    session.scalar.reset_mock()
    assert not await admitted_or_preserved(session, tenant, business, actor, source, None)
    session.scalar.assert_not_awaited()


@pytest.mark.parametrize("proof", [None, 1])
async def test_private_review_needs_preserved_database_proof_without_an_active_run_scope(proof):
    tenant, business, actor, source, preview = [uuid4() for _ in range(5)]
    session = Mock(scalar=AsyncMock(return_value=proof))
    assert await admitted_or_preserved(session, tenant, business, actor, source, preview) is bool(proof)
    assert session.scalar.await_args.args[1] == {
        "tenant": tenant,
        "business": business,
        "actor": actor,
        "source": source,
        "preview": preview,
    }
