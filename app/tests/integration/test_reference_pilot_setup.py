"""Operational setup on a dedicated test DB preserves lifetime pilot spending."""

from uuid import uuid4

import pytest
from sqlalchemy import text

from scripts.configure_reference_pilot import CAP, PILOT_ID, POLICY_ID, configure, tariffs

pytestmark = pytest.mark.integration


@pytest.fixture
async def pilot_admin(admin):
    async with admin.begin() as connection:
        await connection.execute(
            text("""TRUNCATE reference_cost_reservations,reference_cost_monthly,
          reference_provider_pilots,reference_provider_tariffs,reference_cost_policies CASCADE""")
        )
        await connection.execute(text("INSERT INTO reference_cost_policy_head(singleton) VALUES(true)"))
    yield admin


async def test_configuration_replay_keeps_spending_and_the_single_cap(pilot_admin):
    prices = tariffs("0.14.782", "0.0.839")
    async with pilot_admin.begin() as connection:
        await configure(connection, prices)
        await connection.execute(text("UPDATE reference_provider_pilots SET reserved_usd_micros=12345"))
    async with pilot_admin.begin() as connection:
        await configure(connection, prices)
        pilot = (
            await connection.execute(
                text("SELECT id,cap_usd_micros,reserved_usd_micros,active FROM reference_provider_pilots")
            )
        ).one()
        assert tuple(pilot) == (PILOT_ID, CAP, 12345, True)
        assert await connection.scalar(text("SELECT count(*) FROM reference_cost_policy_activations")) == 1
        assert await connection.scalar(text("SELECT count(*) FROM reference_provider_tariffs WHERE active")) == 5
        assert await connection.scalar(text("SELECT policy_id FROM reference_cost_policy_head")) == POLICY_ID


async def test_different_existing_pilot_is_not_replaced(pilot_admin):
    other = uuid4()
    async with pilot_admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO reference_provider_pilots(id,cap_usd_micros,reserved_usd_micros,active)
          VALUES(:id,1000000,900000,true)"""),
            {"id": other},
        )
    with pytest.raises(ValueError, match="EXISTING_CONFIGURATION"):
        async with pilot_admin.begin() as connection:
            await configure(connection, tariffs("0.14.782", "0.0.839"))
    async with pilot_admin.connect() as connection:
        assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 900000
        assert await connection.scalar(text("SELECT count(*) FROM reference_provider_tariffs")) == 0


async def test_conflicting_tariff_rolls_back_policy_and_pilot_creation(pilot_admin):
    prices = tariffs("0.14.782", "0.0.839")
    async with pilot_admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO reference_provider_tariffs
          (version,provider,field_mask,minimum_reserved_usd_micros,active)
          VALUES(:version,'google',:mask,1,false)"""),
            {"version": prices[0].version, "mask": prices[0].field_mask},
        )
    with pytest.raises(ValueError, match="TARIFF_CONFLICT"):
        async with pilot_admin.begin() as connection:
            await configure(connection, prices)
    async with pilot_admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM reference_cost_policies")) == 0
        assert await connection.scalar(text("SELECT count(*) FROM reference_provider_pilots")) == 0
        assert await connection.scalar(text("SELECT count(*) FROM reference_provider_tariffs WHERE active")) == 0


@pytest.mark.parametrize("changed", [False, True])
async def test_only_known_previous_policy_can_roll_forward_without_resetting_counters(pilot_admin, changed):
    from scripts.configure_reference_pilot import PREVIOUS_POLICY_ID

    async with pilot_admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO reference_cost_policies(id,timezone,per_search,monthly_total)
          VALUES(:id,'UTC',1000000,5000000)"""),
            {"id": PREVIOUS_POLICY_ID},
        )
        for provider, search, monthly in [
            ("google", 150000, 500000),
            ("jev", 50000, 250000),
            ("apify", 800000, 4250000),
        ]:
            await connection.execute(
                text("""INSERT INTO reference_cost_policy_providers(policy_id,provider,per_search,monthly_total)
              VALUES(:id,:provider,:search,:monthly)"""),
                {
                    "id": PREVIOUS_POLICY_ID,
                    "provider": provider,
                    "search": search,
                    "monthly": monthly + (1 if changed else 0),
                },
            )
        await connection.execute(
            text("UPDATE reference_cost_policy_head SET policy_id=:id"), {"id": PREVIOUS_POLICY_ID}
        )
        await connection.execute(
            text("""INSERT INTO reference_provider_pilots(id,cap_usd_micros,reserved_usd_micros,active)
          VALUES(:id,5000000,12345,true)"""),
            {"id": PILOT_ID},
        )
    if changed:
        with pytest.raises(ValueError, match="PREVIOUS_POLICY_CONFLICT"):
            async with pilot_admin.begin() as connection:
                await configure(connection, tariffs("0.14.782", "0.0.839"))
    else:
        async with pilot_admin.begin() as connection:
            await configure(connection, tariffs("0.14.782", "0.0.839"))
    async with pilot_admin.connect() as connection:
        assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 12345
        assert await connection.scalar(text("SELECT cap_usd_micros FROM reference_provider_pilots")) == 5000000
        assert await connection.scalar(text("SELECT policy_id FROM reference_cost_policy_head")) == (
            PREVIOUS_POLICY_ID if changed else POLICY_ID
        )
        assert await connection.scalar(text("SELECT count(*) FROM reference_cost_policy_activations")) == (
            1 if changed else 2
        )
        prior = await connection.scalar(
            text("SELECT per_search FROM reference_cost_policy_providers WHERE policy_id=:id AND provider='jev'"),
            {"id": PREVIOUS_POLICY_ID},
        )
        assert prior == 50000
