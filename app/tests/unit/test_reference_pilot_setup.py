"""The local pilot setup never accepts a remote or mismatched database."""

import pytest

from scripts.configure_reference_pilot import CAP, plan, tariffs, validate_local_database

ADMIN = "postgresql+asyncpg://admin:synthetic@localhost:5432/pilot_test"
RUNTIME = "postgresql+asyncpg://runtime:synthetic@localhost:5432/pilot_test"


@pytest.mark.parametrize("environment", ["development", "testing"])
def test_pilot_requires_separate_admin_and_same_local_database(environment):
    validate_local_database(environment, ADMIN, RUNTIME)


@pytest.mark.parametrize(
    "environment,admin,runtime,code",
    [
        ("production", ADMIN, RUNTIME, "LOCAL_ONLY"),
        ("development", ADMIN.replace("localhost", "remote.example"), RUNTIME, "LOCAL_ONLY"),
        ("development", ADMIN.replace("5432", "5433"), RUNTIME, "DATABASE_MISMATCH"),
        ("development", ADMIN.replace("pilot_test", "another"), RUNTIME, "DATABASE_MISMATCH"),
        ("development", ADMIN.replace("postgresql+asyncpg", "postgresql"), RUNTIME, "DATABASE_MISMATCH"),
        ("development", ADMIN, ADMIN, "ADMIN_ROLE_REQUIRED"),
        (
            "testing",
            ADMIN.replace("pilot_test", "project"),
            RUNTIME.replace("pilot_test", "project"),
            "TEST_DATABASE_REQUIRED",
        ),
    ],
)
def test_invalid_pilot_targets_are_rejected_without_io(environment, admin, runtime, code):
    with pytest.raises(ValueError, match=code):
        validate_local_database(environment, admin, runtime)


@pytest.mark.parametrize("build", ["latest", "1.2", "1.2.3?other", "1." + "2" * 24 + ".3"])
def test_only_fixed_actor_builds_can_be_priced(build):
    with pytest.raises(ValueError, match="BUILD_INVALID"):
        tariffs(build, "1.2.3")
    with pytest.raises(ValueError, match="BUILD_INVALID"):
        tariffs("1.2.3", build)


def test_plan_limits_the_single_pilot_and_does_not_enable_network():
    result = plan(tariffs("0.14.782", "0.0.839"))
    assert result["total_cap_usd_micros"] == CAP == 5_000_000
    assert result["per_search_usd_micros"] == 1_000_000
    assert result["provider_flags_enabled"] is False
    assert len(result["tariffs"]) == 5
    assert plan(tariffs("0.14.782", "0.0.839")) == result
