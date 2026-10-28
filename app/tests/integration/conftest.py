import os
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.session import Database
from app.main import create_app
from app.tests.unit.test_core import access_token


@pytest.fixture
async def admin():
    url = os.environ["TEST_ADMIN_DATABASE_URL"]
    if not (make_url(url).database or "").endswith("_test"):
        pytest.fail("Integration cleanup requires a dedicated database ending in _test")
    for key in (
        "TEST_DATABASE_URL",
        "TEST_RELAY_DATABASE_URL",
        "TEST_AUTH_DATABASE_URL",
        "TEST_BILLING_DATABASE_URL",
        "TEST_META_DATABASE_URL",
        "TEST_CORRELATOR_DATABASE_URL",
    ):
        if not os.getenv(key):
            pytest.fail(f"{key} must use a restricted runtime login")
        other = make_url(os.environ[key])
        assert (other.host, other.port, other.database) == (
            make_url(url).host,
            make_url(url).port,
            make_url(url).database,
        )
        assert other.username != make_url(url).username
    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "TRUNCATE user_accounts, tenants, memberships, businesses, idempotency_records, "
                "outbox_events, audit_events, processed_events, auth_limits, billing_jobs, whatsapp_inbox, "
                "visual_global_monthly_budget CASCADE"
            )
        )
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def database(admin, settings):
    db = Database(settings)
    try:
        yield db
    finally:
        await db.close()


@pytest.fixture
async def relay_database(admin, settings):
    db = Database(settings, relay=True)
    try:
        yield db
    finally:
        await db.close()


@pytest.fixture
async def seeded(admin):
    t1, t2, a1, a2, viewer = [uuid4() for _ in range(5)]
    async with admin.begin() as connection:
        for tenant, actor in ((t1, a1), (t2, a2)):
            await connection.execute(text("INSERT INTO tenants(id,name) VALUES (:id,'test')"), {"id": tenant})
            await connection.execute(
                text("INSERT INTO memberships(tenant_id,actor_id,role) VALUES (:tenant,:actor,'owner')"),
                {"tenant": tenant, "actor": actor},
            )
        from uuid import uuid5

        from app.services.auth import digest

        for actor in (a1, a2, viewer):
            await connection.execute(
                text(
                    """
INSERT INTO user_accounts(id,issuer,subject,display_name,email_verified) VALUES
(:id,'test',:sub,'Test',true)
"""
                ),
                {"id": actor, "sub": str(actor)},
            )
            await connection.execute(
                text(
                    """
INSERT INTO auth_sessions(id,user_id,csrf_hash,expires_at) VALUES
(:id,:user,:csrf,now()+interval '1 day')
"""
                ),
                {"id": uuid5(actor, "test-session"), "user": actor, "csrf": digest("test-csrf")},
            )
        await connection.execute(
            text("INSERT INTO memberships(tenant_id,actor_id,role) VALUES (:tenant,:actor,'viewer')"),
            {"tenant": t1, "actor": viewer},
        )
    return {"t1": t1, "t2": t2, "a1": a1, "a2": a2, "viewer": viewer}


@pytest.fixture
async def api(database, settings):
    app = create_app(settings, database)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client,
    ):
        yield client


@pytest.fixture
def headers(settings, seeded):
    return {
        "Authorization": f"Bearer {access_token(settings, seeded['a1'])}",
        "X-Tenant-ID": str(seeded["t1"]),
        "Idempotency-Key": "business-request-001",
    }


@pytest.fixture
async def auth_database(admin, settings):
    db = Database(settings, auth=True)
    try:
        yield db
    finally:
        await db.close()


@pytest.fixture
async def billing_database(admin, settings):
    config = settings.model_copy(update={"billing_database_url": os.environ["TEST_BILLING_DATABASE_URL"]})
    from pydantic import SecretStr

    config.billing_database_url = SecretStr(os.environ["TEST_BILLING_DATABASE_URL"])
    db = Database(config, billing=True)
    try:
        yield db
    finally:
        await db.close()


@pytest.fixture
async def auth_service(auth_database, settings):
    from app.services.auth import AuthService

    return AuthService(settings, auth_database)


@pytest.fixture
async def native_api(database, auth_database, settings):
    app = create_app(settings, database, auth_database)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app),
            base_url=settings.public_web_url,
            headers={"Origin": settings.public_web_url},
        ) as client,
    ):
        yield client
