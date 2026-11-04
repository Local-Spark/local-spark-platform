"""The proposal's new reference snapshot is write-once; legacy rows remain null."""

import json
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.tests.integration.test_editorial_proposals import _business

pytestmark = pytest.mark.integration


async def _insert(admin, seeded, business, value):
    proposal = uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO editorial_proposals
              (id,tenant_id,business_id,actor_id,operation_id,request_hash,context_version,
                reference_generation_snapshot)
              VALUES(:id,:tenant,:business,:actor,:operation,:hash,0,CAST(:snapshot AS jsonb))"""),
            {
                "id": proposal,
                "tenant": seeded["t1"],
                "business": business,
                "actor": seeded["a1"],
                "operation": uuid4(),
                "hash": "a" * 64,
                "snapshot": None if value is None else json.dumps(value),
            },
        )
    return proposal


async def test_reference_snapshot_cannot_be_rewritten_and_legacy_is_not_backfilled(admin, database, seeded):
    business = await _business(admin, seeded)
    empty = {"version": 1, "selected": [], "learnings": []}
    legacy = await _insert(admin, seeded, business, None)
    new = await _insert(admin, seeded, business, empty)
    for proposal, replacement in [(legacy, empty), (new, None)]:
        with pytest.raises(DBAPIError, match="REFERENCE_GENERATION_SNAPSHOT_IMMUTABLE"):
            async with admin.begin() as connection:
                await connection.execute(
                    text(
                        "UPDATE editorial_proposals SET reference_generation_snapshot=CAST(:snapshot AS jsonb) "
                        "WHERE id=:id"
                    ),
                    {"id": proposal, "snapshot": None if replacement is None else json.dumps(replacement)},
                )
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE editorial_proposals SET state='rejected',error_code='EDITORIAL_FACTS_REQUIRED',
              reference_generation_snapshot=reference_generation_snapshot WHERE id=:id"""),
            {"id": new},
        )
    async with database.transaction(seeded["t1"], seeded["a1"]) as session:
        rows = (
            await session.execute(text("SELECT id,reference_generation_snapshot FROM editorial_proposals ORDER BY id"))
        ).all()
        assert dict(rows) == {legacy: None, new: empty}
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM editorial_proposals")) == 0


@pytest.mark.parametrize(
    "value",
    [
        [],
        {},
        {"version": 2, "selected": [], "learnings": []},
        {"version": 1, "selected": {}, "learnings": []},
        {"version": 1, "selected": [], "learnings": None},
    ],
)
async def test_snapshot_storage_rejects_malformed_outer_contract(admin, seeded, value):
    business = await _business(admin, seeded)
    with pytest.raises(DBAPIError, match="check constraint"):
        await _insert(admin, seeded, business, value)
