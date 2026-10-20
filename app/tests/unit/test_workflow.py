from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.workflows.contracts import BusinessEvent
from app.workflows.foundation import BusinessCreatedWorkflow


@pytest.mark.parametrize("result", ["recorded", "duplicate", None])
async def test_workflow_activity_result_contract(monkeypatch, result):
    event = BusinessEvent(**{field: str(uuid4()) for field in BusinessEvent.__dataclass_fields__})
    execute = AsyncMock(return_value=result)
    monkeypatch.setattr("app.workflows.foundation.workflow.execute_activity", execute)
    if result is None:
        with pytest.raises(TypeError, match="invalid result"):
            await BusinessCreatedWorkflow().run(event)
    else:
        assert await BusinessCreatedWorkflow().run(event) == result
    execute.assert_awaited_once()
