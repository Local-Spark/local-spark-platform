"""Durable provider run identities; raw responses never enter database or events."""

import json
from uuid import UUID

from sqlalchemy import text

from app.adapters.apify_place_contacts import SubmittedPlaceContacts
from app.db.session import Database
from app.services.reference_contacts_budget_guard import ContactsGuardContext, ContactsGuardError


def run_metadata(run: SubmittedPlaceContacts) -> dict[str, str]:
    return {
        "run_id": run.run_id,
        "dataset_id": run.dataset_id,
        "key_value_store_id": run.key_value_store_id,
        "request_queue_id": run.request_queue_id,
        "build_id": run.build_id,
        "build_number": run.build_number,
        "provider_actor_id": run.provider_actor_id,
    }


def _check(context: ContactsGuardContext, run: SubmittedPlaceContacts) -> None:
    if (
        run.submission_id != context.effect
        or run.place_id != context.place_id
        or run.build_number != context.build
        or run.provider_actor_id != context.provider_actor_id
    ):
        raise ContactsGuardError("CONTACTS_RUN_BINDING_INVALID")


async def record_contacts_run(
    database: Database, context: ContactsGuardContext, token: UUID, run: SubmittedPlaceContacts
) -> None:
    _check(context, run)
    async with database.transaction(context.tenant, context.actor) as session:
        await session.scalar(
            text("SELECT public.reference_contacts_record_run(:business,:effect,:token,CAST(:metadata AS jsonb))"),
            {
                "business": context.business,
                "effect": context.effect,
                "token": token,
                "metadata": json.dumps(run_metadata(run)),
            },
        )


async def load_contacts_run(
    database: Database, context: ContactsGuardContext
) -> tuple[SubmittedPlaceContacts, UUID] | None:
    async with database.transaction(context.tenant, context.actor) as session:
        data = await session.scalar(
            text("SELECT public.reference_contacts_load_run(:business,:effect)"),
            {"business": context.business, "effect": context.effect},
        )
    if data is None:
        return None
    run = SubmittedPlaceContacts(context.effect, context.place_id, **data["metadata"])
    _check(context, run)
    return run, UUID(data["executor_token"])


async def record_contacts_cost(
    database: Database, context: ContactsGuardContext, token: UUID, run: SubmittedPlaceContacts, cost: int
) -> None:
    _check(context, run)
    if type(cost) is not int or not 0 <= cost <= 1_000_000_000_000:
        raise ContactsGuardError("CONTACTS_RECEIPT_INVALID")
    async with database.transaction(context.tenant, context.actor) as session:
        await session.scalar(
            text("SELECT public.reference_contacts_record_cost(:business,:effect,:token,:run,:cost)"),
            {"business": context.business, "effect": context.effect, "token": token, "run": run.run_id, "cost": cost},
        )
