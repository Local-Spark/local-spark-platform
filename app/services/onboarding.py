"""Initial ownership and context, without activating a paid plan or claiming a verified phone."""

import hashlib
import json
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import Identity
from app.schemas.business import BusinessCreate
from app.schemas.onboarding import OnboardingCreate, OnboardingResult, OrganizationRead, SessionRead, UserRead
from app.services.business import AccessDenied, IdempotencyConflict, create_business, require_member


async def sync_identity(session: AsyncSession, identity: Identity) -> None:
    # Serialize the initial insert across both unique identity indexes before a row exists.
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:actor,0))"), {"actor": str(identity.actor_id)}
    )
    result = await session.scalar(
        text("""INSERT INTO user_accounts(id,issuer,subject,display_name,email,email_verified)
          VALUES (:id,:issuer,:subject,:name,:email,:verified)
          ON CONFLICT(id) DO UPDATE SET display_name=excluded.display_name,
            email=excluded.email,email_verified=excluded.email_verified
          WHERE user_accounts.active AND user_accounts.issuer=excluded.issuer AND user_accounts.subject=excluded.subject
          RETURNING id"""),
        {
            "id": identity.actor_id,
            "issuer": identity.issuer,
            "subject": identity.subject,
            "name": identity.display_name,
            "email": identity.email,
            "verified": identity.email_verified,
        },
    )
    if result is None:
        raise AccessDenied


async def session_context(session: AsyncSession, identity: Identity) -> SessionRead:
    user = (
        (
            await session.execute(
                text("SELECT id,display_name,email,email_verified FROM user_accounts WHERE id=:id AND active"),
                {"id": identity.actor_id},
            )
        )
        .mappings()
        .one_or_none()
    )
    if user is None:
        raise AccessDenied
    organizations = (
        (
            await session.execute(
                text("""SELECT t.id,t.name,m.role,
      (SELECT count(*) FROM businesses b WHERE b.tenant_id=t.id) AS business_count,
      EXISTS(SELECT 1 FROM business_profiles p WHERE p.tenant_id=t.id AND p.completed) AS onboarding_completed
      FROM memberships m JOIN tenants t ON t.id=m.tenant_id
      WHERE m.actor_id=:actor AND m.active ORDER BY t.id"""),
                {"actor": identity.actor_id},
            )
        )
        .mappings()
        .all()
    )
    staff = await session.scalar(text("SELECT public.is_platform_staff()"))
    return SessionRead(
        user=UserRead.model_validate(user),
        organizations=[OrganizationRead.model_validate(row) for row in organizations],
        is_staff=bool(staff),
    )


async def provision_initial_business(
    session: AsyncSession, identity: Identity, payload: OnboardingCreate
) -> OnboardingResult:
    if not identity.email_verified:
        raise AccessDenied
    await sync_identity(session, identity)
    tenant_id = uuid4()
    await session.execute(text("SELECT set_config('app.tenant_id',:tenant,true)"), {"tenant": str(tenant_id)})
    digest = hashlib.sha256(payload.model_dump_json(exclude_none=True).encode()).hexdigest()
    inserted = await session.scalar(
        text("""INSERT INTO onboarding_registrations(actor_id,tenant_id,request_hash)
      VALUES (:actor,:tenant,:hash) ON CONFLICT(actor_id) DO NOTHING RETURNING tenant_id"""),
        {"actor": identity.actor_id, "tenant": tenant_id, "hash": digest},
    )
    if inserted is None:
        record = (
            (
                await session.execute(
                    text("SELECT tenant_id,request_hash,response FROM onboarding_registrations WHERE actor_id=:actor"),
                    {"actor": identity.actor_id},
                )
            )
            .mappings()
            .one()
        )
        await session.execute(
            text("SELECT set_config('app.tenant_id',:tenant,true)"), {"tenant": str(record["tenant_id"])}
        )
        await require_member(session, record["tenant_id"], identity.actor_id, write=True)
        if record["request_hash"] != digest:
            raise IdempotencyConflict
        return OnboardingResult.model_validate({**record["response"], "replayed": True})
    await session.execute(
        text("INSERT INTO tenants(id,name) VALUES (:id,:name)"), {"id": tenant_id, "name": payload.name}
    )
    await session.execute(
        text("INSERT INTO memberships(tenant_id,actor_id,role) VALUES (:tenant,:actor,'owner')"),
        {"tenant": tenant_id, "actor": identity.actor_id},
    )
    created = await create_business(
        session,
        tenant_id,
        identity.actor_id,
        "initial-onboarding",
        BusinessCreate(name=payload.name, timezone=payload.timezone),
    )
    await session.execute(
        text("""INSERT INTO business_profiles(
          tenant_id,business_id,category,city,description,phone,brand_color,state_code,city_ibge_code)
      VALUES (:tenant,:business,:category,:city,:description,:phone,:brand_color,:state_code,:city_ibge_code)"""),
        {
            "tenant": tenant_id,
            "business": created.business.id,
            **payload.model_dump(
                include={"category", "city", "description", "phone", "brand_color", "state_code", "city_ibge_code"}
            ),
        },
    )
    for purpose in ("terms", "privacy"):
        await session.execute(
            text("INSERT INTO consents(tenant_id,actor_id,purpose,version) VALUES (:tenant,:actor,:purpose,:version)"),
            {"tenant": tenant_id, "actor": identity.actor_id, "purpose": purpose, "version": payload.terms_version},
        )
    result = OnboardingResult(tenant_id=tenant_id, business_id=created.business.id)
    await session.execute(
        text("UPDATE onboarding_registrations SET response=CAST(:response AS jsonb) WHERE actor_id=:actor"),
        {"response": json.dumps(result.model_dump(mode="json")), "actor": identity.actor_id},
    )
    return result
