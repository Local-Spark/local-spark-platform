"""A terminal Actor can still expose preliminary accounting figures."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import pytest

from app.adapters.apify_run_metadata import terminal_run_cost_ready
from app.tests.unit.test_apify_instagram_feed import adapter as feed_adapter
from app.tests.unit.test_apify_instagram_feed import image_post
from app.tests.unit.test_apify_instagram_feed import metadata as feed_metadata
from app.tests.unit.test_apify_instagram_feed import submitted as feed_run
from app.tests.unit.test_apify_place_contacts import metadata as contacts_metadata
from app.tests.unit.test_apify_place_contacts import provider as contacts_adapter
from app.tests.unit.test_apify_place_contacts import row as contacts_row
from app.tests.unit.test_apify_place_contacts import run as contacts_run

_FINISHED = datetime(2026, 1, 1, tzinfo=UTC)


@pytest.mark.parametrize("elapsed,ready", [(-1, False), (0, False), (29.999, False), (30, True), (31, True)])
def test_cost_waits_thirty_seconds_after_finished_at(elapsed, ready):
    assert (
        terminal_run_cost_ready({"finishedAt": _FINISHED.isoformat()}, now=_FINISHED + timedelta(seconds=elapsed))
        is ready
    )


@pytest.mark.parametrize("finished", [None, 1, "invalid", "2026-01-01", "2026-01-01T00:00:00"])
def test_missing_or_unzoned_finish_time_keeps_the_reservation_pending(finished):
    assert not terminal_run_cost_ready({"finishedAt": finished}, now=_FINISHED + timedelta(days=1))


def test_missing_finish_field_and_unzoned_clock_do_not_invent_maturity():
    assert not terminal_run_cost_ready({})
    assert not terminal_run_cost_ready({"finishedAt": _FINISHED.isoformat()}, now=datetime(2026, 1, 2))


def test_default_clock_and_equivalent_timezone_use_elapsed_time():
    assert terminal_run_cost_ready({"finishedAt": "2000-01-01T00:00:00Z"})
    assert terminal_run_cost_ready({"finishedAt": "2025-12-31T21:00:00-03:00"}, now=_FINISHED + timedelta(seconds=30))


@pytest.mark.parametrize(
    "charged,accounted,ready",
    [
        (None, None, True),
        ({}, {}, True),
        ({"result": 20}, {"result": 20}, True),
        ({"result": 20}, {"result": 19}, False),
        ({"result": 0}, {}, False),
        ({"result": 20}, None, False),
        (None, {"result": 20}, False),
        ([], {}, False),
        ({}, [], False),
        ({"result": True}, {"result": True}, False),
        ({"result": -1}, {"result": -1}, False),
        ({"result": 1}, {"result": "1"}, False),
    ],
)
def test_exposed_event_counters_must_be_valid_and_accounted(charged, accounted, ready):
    assert (
        terminal_run_cost_ready(
            {
                "finishedAt": _FINISHED.isoformat(),
                "chargedEventCounts": charged,
                "accountedChargedEventCounts": accounted,
            },
            now=_FINISHED + timedelta(seconds=30),
        )
        is ready
    )


@pytest.mark.parametrize("kind", ["feed", "contacts"])
@pytest.mark.parametrize("terminal", ["SUCCEEDED", "FAILED"])
async def test_terminal_poll_waits_for_clock_and_accounting_without_another_submission(monkeypatch, kind, terminal):
    class Clock(datetime):
        current = _FINISHED

        @classmethod
        def now(cls, tz=None):
            return cls.current

    monkeypatch.setattr("app.adapters.apify_run_metadata.datetime", Clock)
    metadata, make_run, make_adapter = (
        (feed_metadata, feed_run, feed_adapter)
        if kind == "feed"
        else (contacts_metadata, contacts_run, contacts_adapter)
    )
    requests = []

    def respond(request):
        assert request.method == "GET"
        requests.append(request.url.path)
        if "/actor-runs/" in request.url.path:
            mature = Clock.current >= _FINISHED + timedelta(seconds=31)
            return httpx.Response(
                200,
                json=metadata(
                    terminal,
                    finishedAt=_FINISHED.isoformat(),
                    usageTotalUsd=0.004 if mature else 0.002,
                    chargedEventCounts={"result": 2},
                    accountedChargedEventCounts={"result": 2 if mature else 1},
                ),
            )
        return httpx.Response(200, json=[image_post()] if kind == "feed" else [contacts_row()])

    client, run = make_adapter(respond), make_run()
    for seconds in (0, 29.999, 30):
        Clock.current = _FINISHED + timedelta(seconds=seconds)
        result = await client.inspect(run, uuid4())
        assert result.state == "pending" and result.reported_cost_usd_micros is None
    assert len(requests) == 3 and all("/actor-runs/" in path for path in requests)
    Clock.current = _FINISHED + timedelta(seconds=31)
    final = await client.inspect(run, uuid4())
    assert final.state != "pending" and final.reported_cost_usd_micros == 4000
    assert len({path for path in requests if "/actor-runs/" in path}) == 1
