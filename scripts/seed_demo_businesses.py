"""Explicit local maintenance, never a foundation test or paid generation.

Run from the repository root with PYTHONPATH=.; see docs/demo-businesses.md.
No backup is produced. --reset preserves the selected administrator's auth state.
"""

import argparse
import asyncio
import base64
import hashlib
import json
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx
from dotenv import dotenv_values
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.core.identity import Identity
from app.db.session import Database, current_schema_head
from app.schemas.brand_kits import BrandKitConfirmRequest, BrandKitDraftRequest, BrandKitLogoUpload
from app.schemas.business_address import BusinessAddressWrite
from app.schemas.business_catalog import CatalogUpdate
from app.schemas.business_collection import CollectionPhotoUpload
from app.schemas.editorial_context import ContextUpdate
from app.schemas.onboarding import OnboardingCreate
from app.schemas.owner_references import ReferenceCreate
from app.services.billing import sponsor
from app.services.brand_kits import BrandKitService
from app.services.business_address import BusinessAddressService
from app.services.business_catalog import BusinessCatalogService
from app.services.business_collection import BusinessCollectionService
from app.services.editorial_context import EditorialContextService
from app.services.onboarding import provision_initial_business
from app.services.owner_references import OwnerReferencesService
from app.services.service_agreement import (
    SERVICE_AGREEMENT_HASH,
    SERVICE_AGREEMENT_VERSION,
    ServiceAgreementService,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures/demo-businesses"
LOCAL = Path(".local/demo-businesses-20261116")
DATABASE = "meu_braco_direito_platform"
VALID_UNTIL = "2027-02-28"
PRESERVE = {
    "alembic_version",
    "reference_cost_policies",
    "reference_cost_policy_providers",
    "reference_cost_policy_head",
    "reference_cost_policy_activations",
    "reference_provider_tariffs",
}


def uid(key):
    return uuid5(NAMESPACE_URL, "local-demo-businesses:2026-11-16:" + key)


def encoded(path):
    return base64.b64encode(path.read_bytes()).decode()


async def reset(engine, admin):
    """One transaction, temporary in-database preservation only; no CASCADE."""
    async with engine.begin() as c:
        await c.execute(text("SET LOCAL lock_timeout='5s'"))
        await c.execute(text("SET LOCAL statement_timeout='60s'"))
        if await c.scalar(text("SELECT version_num FROM alembic_version")) != "0129_content_continuations":
            raise RuntimeError("RESET_REQUIRES_REVIEW_FOR_THIS_SCHEMA")
        tables = (await c.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))).scalars().all()
        copies = {
            "user_accounts": "id=:admin",
            "auth_credentials": "user_id=:admin",
            "platform_staff": "actor_id=:admin",
            "auth_sessions": "user_id=:admin",
            "auth_refresh_tokens": "session_id IN (SELECT id FROM auth_sessions WHERE user_id=:admin)",
            "auth_audit": "user_id=:admin",
        }
        for table, predicate in copies.items():
            await c.execute(
                text(
                    f"CREATE TEMP TABLE keep_{table} ON COMMIT DROP AS SELECT * FROM public.{table} WHERE {predicate}"
                ),
                {"admin": admin},
            )
        assert await c.scalar(text("SELECT count(*) FROM keep_auth_credentials")) == 1
        targets = ",".join(
            "public." + engine.dialect.identifier_preparer.quote(t) for t in sorted(set(tables) - PRESERVE)
        )
        await c.execute(text("TRUNCATE TABLE " + targets))
        for table in copies:
            await c.execute(text(f"INSERT INTO public.{table} SELECT * FROM keep_{table}"))
        await c.execute(
            text("INSERT INTO auth_audit(user_id,event) VALUES(:admin,'local.demo.reset.authorized')"), {"admin": admin}
        )
    print("Base local limpa; identidade e autenticação administrativa preservadas.", flush=True)


async def seed_one(settings, db, engine, admin, row):
    slug = row["slug"]
    actor = uid(slug + ":owner")
    identity = Identity(actor, "local-demo", str(actor), row["name"] + " — demonstração", row["email"], True)
    profile = OnboardingCreate(
        name=row["name"],
        category=row["category"],
        city="São Paulo",
        state_code="SP",
        city_ibge_code="3550308",
        description=row["description"],
        phone="+5500000000000",
        brand_color=row["color"],
        accept_terms=True,
        accept_privacy=True,
        timezone="America/Sao_Paulo",
    )
    async with db.transaction(UUID(int=0), actor) as session:
        created = await provision_initial_business(session, identity, profile)
    tenant, business = created.tenant_id, created.business_id
    # Local bootstrap of explicit membership, not a runtime tenant/RLS bypass.
    async with engine.begin() as c:
        await c.execute(
            text(
                "INSERT INTO memberships(tenant_id,actor_id,role) VALUES(:t,:a,'owner') ON CONFLICT(tenant_id,actor_id) DO NOTHING"
            ),
            {"t": tenant, "a": admin},
        )
        await c.execute(
            text("INSERT INTO auth_credentials(user_id,email) VALUES(:a,:email) ON CONFLICT(user_id) DO NOTHING"),
            {"a": actor, "email": row["email"]},
        )
        await c.execute(
            text(
                "INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id) VALUES(:t,:a,:op,'local.demo.admin_membership.granted',:b) ON CONFLICT DO NOTHING"
            ),
            {"t": tenant, "a": admin, "op": uid(slug + ":admin"), "b": business},
        )
    async with db.transaction(tenant, admin) as session:
        await sponsor(
            session,
            tenant,
            admin,
            "demo-20261116",
            "Cadastro fictício local para validação administrativa; sem cobrança.",
        )
    await ServiceAgreementService(settings, db).accept(
        tenant, business, admin, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
    )
    offerings = []
    for index, item in enumerate(row["offerings"]):
        entry = {k: item[k] for k in ("name", "kind", "description", "price_minor")}
        entry.update(
            id=uid(slug + ":item:" + item["key"]),
            state="active",
            category=row["category"],
            aliases=[item["key"].replace("-", " ")],
            position=index,
            price_valid_until=VALID_UNTIL,
        )
        if item["kind"] == "service":
            entry.update(
                duration_minutes=item["duration_minutes"],
                booking_instructions="Agendar pelo link informado no cadastro. Horários e condições de demonstração.",
            )
        offerings.append(entry)
    promoted = next((x for x in offerings if x["price_minor"] > 0), offerings[0])
    await BusinessCatalogService(db).update(
        tenant,
        business,
        admin,
        CatalogUpdate(
            operation_id=uid(slug + ":catalog"),
            expected_version=0,
            offerings=offerings,
            promotions=[
                dict(
                    id=uid(slug + ":promotion"),
                    offering_id=promoted["id"],
                    title="Condição de demonstração — novembro",
                    description="Oferta fictícia válida somente no cenário de teste, sem cobrança ou reserva real.",
                    state="active",
                    price_minor=round(promoted["price_minor"] * 0.9),
                    starts_at="2026-11-16T00:00:00-03:00",
                    ends_at="2026-12-01T00:00:00-03:00",
                )
            ],
        ),
    )
    facts = [("hours", row["hours"])] + [("differentiator", x) for x in row["differentiators"]]
    facts += [
        (
            "other",
            "Cadastro fictício de demonstração. Fotos licenciadas ilustrativas; não são registros reais do negócio.",
        )
    ]
    facts += [(x["kind"], x["name"] + ": " + x["description"][:160]) for x in row["offerings"]]
    await EditorialContextService(db).update(
        tenant,
        business,
        admin,
        ContextUpdate(
            operation_id=uid(slug + ":context"),
            expected_version=0,
            facts=[
                dict(
                    id=uid(slug + f":fact:{i}"),
                    kind=k,
                    statement=s,
                    source_detail="Cenário fictício autorizado pelo administrador em 16/11/2026",
                    valid_until=VALID_UNTIL if k in {"price", "hours", "offer"} else None,
                )
                for i, (k, s) in enumerate(facts)
            ],
            preferences=dict(
                goal=row["goal"],
                tone=row["tone"],
                avoided_topics=row["avoided"],
                posts_per_week=3,
                cta_destination=dict(type=row["linktype"], value=row["link"]),
                reference_search=dict(
                    scope="local",
                    radius_km=5,
                    origin=dict(
                        method="manual",
                        address=dict(city="São Paulo", state_code="SP", neighborhood=row["neighborhood"]),
                    ),
                ),
                business_terms=row["terms"],
                business_characteristics=row["description"],
            ),
        ),
    )
    await BusinessAddressService(db).save(
        tenant,
        business,
        admin,
        BusinessAddressWrite(
            operation_id=uid(slug + ":address"),
            expected_version=0,
            address=dict(
                street=row["street"],
                number=row["number"],
                neighborhood=row["neighborhood"],
                city="São Paulo",
                state_code="SP",
                complement="Endereço fictício; não usar para deslocamento ou entrega.",
            ),
        ),
    )
    kits = BrandKitService(settings, db)
    logo = await kits.upload_logo(
        tenant,
        business,
        admin,
        BrandKitLogoUpload(
            operation_id=uid(slug + ":logo"),
            mime_type="image/png",
            content_base64=encoded(FIXTURES / (slug + ".png")),
            rights_confirmed=True,
        ),
    )
    overrides = dict(
        palette=dict(primary=row["color"], background=row["background"], accent=row["accent"]),
        heading_font="DejaVu Sans" if slug == "vertice-autos" else "DejaVu Serif",
        body_font="DejaVu Sans",
        brand_name=row["name"],
        tagline=row["tagline"],
        cta=row["cta"],
        logo_asset_id=logo.id,
        formats={k: dict(layout="photo_focus", image_position="center") for k in ["feed", "story", "reel_cover"]},
    )
    await kits.draft(
        tenant,
        business,
        admin,
        BrandKitDraftRequest(
            operation_id=uid(slug + ":kit-draft"),
            expected_version=0,
            kit_id="cafe-pausas",
            kit_version=1,
            overrides=overrides,
        ),
    )
    await kits.confirm(
        tenant, business, admin, BrandKitConfirmRequest(operation_id=uid(slug + ":kit-confirm"), expected_version=1)
    )
    collection = BusinessCollectionService(settings, db)
    photos = [dict(photo_id=x["photo_id"], space_kind=x["space_kind"], title=x["title"]) for x in row["photo_spaces"]]
    photos += [
        dict(photo_id=x["photo_id"], item_id=uid(slug + ":item:" + x["key"]), title=x["name"]) for x in row["offerings"]
    ]
    for i, photo in enumerate(photos):
        photo = dict(photo)
        photo_id = photo.pop("photo_id")
        photo["title"] += f" — ilustrativa • Pexels {photo_id}"
        await collection.upload(
            tenant,
            business,
            admin,
            CollectionPhotoUpload(
                **photo,
                sort_order=i,
                operation_id=uid(slug + f":photo:{i}"),
                mime_type="image/jpeg",
                content_base64=encoded(LOCAL / f"{photo_id}.jpg"),
                rights_confirmed=True,
            ),
        )
    refs = OwnerReferencesService(db)
    for handle in row["references"]:
        await refs.create(
            tenant,
            business,
            admin,
            ReferenceCreate(operation_id=uid(slug + ":ref:" + handle), instagram=handle, note=row["reference_note"]),
        )
    # Read through the same restricted services the UI uses. No model calls.
    catalog = await BusinessCatalogService(db).read(tenant, business, admin)
    context = await EditorialContextService(db).read(tenant, business, admin)
    kit = await kits.read(tenant, business, admin)
    media = await collection.list_photos(tenant, business, admin)
    references = await refs.list(tenant, business, admin)
    assert len(catalog.offerings) == 6 and context.version > 0 and kit.confirmed is not None and len(media) == 8
    result = dict(
        name=row["name"],
        email=row["email"],
        tenant_id=str(tenant),
        business_id=str(business),
        offerings=len(catalog.offerings),
        promotions=len(catalog.promotions),
        photos=len(media),
        references=len(references),
        context_version=context.version,
        kit_version=kit.confirmed.version,
    )
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


async def main(args):
    settings = get_settings()
    values = dotenv_values(".env")
    migration = make_url(values["MEU_BRACO_DIREITO_MIGRATION_DATABASE_URL"])
    runtime = make_url(settings.database_url.get_secret_value())
    if (
        settings.environment != "development"
        or migration.host not in {"localhost", "127.0.0.1"}
        or migration.database != DATABASE
        or (migration.host, migration.port, migration.database) != (runtime.host, runtime.port, runtime.database)
    ):
        raise RuntimeError("LOCAL_DEVELOPMENT_DATABASE_REQUIRED")
    admin = UUID(args.admin_id)
    if admin != settings.creation_lab_actor_id:
        raise RuntimeError("CREATION_LAB_ADMIN_MISMATCH")
    # Validate all downloaded inputs before any destructive operation.
    LOCAL.mkdir(parents=True, exist_ok=True)
    rows = json.loads((FIXTURES / "businesses.json").read_text())
    for media in json.loads((FIXTURES / "media.json").read_text()):
        path = LOCAL / f"{media['id']}.jpg"
        if not path.exists():
            expected = f"https://images.pexels.com/photos/{media['id']}/pexels-photo-{media['id']}.jpeg?auto=compress&cs=tinysrgb&w=1200"
            if media["download_url"] != expected:
                raise RuntimeError("UNRECOGNIZED_MEDIA_SOURCE")
            async with httpx.AsyncClient(timeout=60) as client:
                async with client.stream("GET", expected) as response:
                    response.raise_for_status()
                    content = bytearray()
                    async for chunk in response.aiter_bytes():
                        content.extend(chunk)
                        if len(content) > 2 * 1024 * 1024:
                            raise RuntimeError("MEDIA_TOO_LARGE")
            if hashlib.sha256(content).hexdigest() != media["sha256"]:
                raise RuntimeError("DOWNLOADED_MEDIA_CHECKSUM_MISMATCH")
            path.write_bytes(content)
        if hashlib.sha256(path.read_bytes()).hexdigest() != media["sha256"]:
            raise RuntimeError("MEDIA_CHECKSUM_MISMATCH")
    for row in rows:
        if not (FIXTURES / (row["slug"] + ".png")).is_file():
            raise RuntimeError("LOGO_REQUIRED")
    engine = create_async_engine(migration, hide_parameters=True)
    db = Database(settings)
    try:
        async with engine.connect() as c:
            if await c.scalar(text("SELECT version_num FROM alembic_version")) != current_schema_head():
                raise RuntimeError("SCHEMA_HEAD_REQUIRED")
            found = await c.scalar(
                text(
                    "SELECT u.id FROM user_accounts u JOIN platform_staff s ON s.actor_id=u.id WHERE u.id=:a AND u.active AND s.active"
                ),
                {"a": admin},
            )
            if found != admin:
                raise RuntimeError("EXISTING_ACTIVE_ADMIN_REQUIRED")
        if args.reset:
            if args.confirm_database != DATABASE:
                raise RuntimeError("EXPLICIT_DATABASE_CONFIRMATION_REQUIRED")
            await reset(engine, admin)
        results = []
        for row in rows:
            results.append(await seed_one(settings, db, engine, admin, row))
            (LOCAL / "result.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    finally:
        await db.close()
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admin-id", required=True)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Erase local business data, preserving only admin authentication and global tariffs.",
    )
    parser.add_argument("--confirm-database", help="Exact local database name; required together with --reset.")
    asyncio.run(main(parser.parse_args()))
