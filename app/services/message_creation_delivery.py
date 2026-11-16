"""Product-only projections of common execution outputs; never publishes a piece.

The existing WhatsApp transport is simulated. Receipts explicitly retain that
fact and cannot be mistaken for provider delivery acknowledgements.
"""

from uuid import uuid5

from sqlalchemy import text

from app.services.auth import AuthError
from app.services.content_pieces import PieceArtifact, _event, write_version
from app.services.motion_context import MotionContext


async def record_product_message(session, row, cipher, message, *, kind, sha, stage=None):
    if row["origin"] != "whatsapp":
        return
    await session.execute(text("SELECT set_config('app.tenant_id',:tenant,true)"), {"tenant": str(row["tenant_id"])})
    sender = await session.scalar(
        text("""SELECT l.sender_hash FROM whatsapp_channel_links l
      JOIN whatsapp_material_events e ON e.tenant_id=l.tenant_id AND e.business_id=l.business_id AND e.sender_hash=l.sender_hash
      WHERE e.id=:source AND l.active AND l.actor_id=:actor"""),
        {"source": row["source_event_id"], "actor": row["actor_id"]},
    )
    if not sender:
        raise AuthError("MESSAGE_CHANNEL_CHANGED", 409)
    identifier = uuid5(row["id"], "product-delivery")
    await session.execute(
        text("""INSERT INTO message_creation_deliveries
      (id,run_id,tenant_id,business_id,actor_id,recipient_hash,provider_message_id,message_ciphertext,kind,stage,content_sha256)
      VALUES(:id,:run,:tenant,:business,:actor,:sender,:provider,:message,:kind,:stage,:sha)"""),
        {
            "id": identifier,
            "run": row["id"],
            "tenant": row["tenant_id"],
            "business": row["business_id"],
            "actor": row["actor_id"],
            "sender": sender,
            "provider": f"fake-whatsapp/{identifier}",
            "message": cipher.seal({"message": message}),
            "kind": kind,
            "stage": stage,
            "sha": sha,
        },
    )
    await _event(session, row["tenant_id"], row["business_id"], row["actor_id"], row["id"], "creation.message_recorded")


async def persist_product_result(session, row, cipher):
    if row["origin"] != "whatsapp":
        return
    await session.execute(text("SELECT set_config('app.tenant_id',:tenant,true)"), {"tenant": str(row["tenant_id"])})
    result = (
        (
            await session.execute(
                text("SELECT * FROM creation_lab_versions WHERE run_id=:run AND selected"), {"run": row["id"]}
            )
        )
        .mappings()
        .one()
    )
    # Each explicit attempt remains an independently reviewable piece. Parent
    # lineage remains on the execution; no existing approved version is replaced.
    piece = uuid5(row["id"], "product-piece")
    await write_version(
        session,
        row["tenant_id"],
        row["business_id"],
        row["actor_id"],
        piece,
        row["id"],
        row["format"],
        (
            PieceArtifact(
                uuid5(result["id"], "product-artifact"),
                result["object_key"],
                result["sha256"],
                result["mime_type"],
                result["size_bytes"],
            ),
        ),
    )
    await session.execute(
        text("UPDATE creation_lab_runs SET output_piece_id=:piece WHERE id=:run"), {"piece": piece, "run": row["id"]}
    )
    copy = cipher.open(result["copy_ciphertext"]) if result.get("copy_ciphertext") else {}
    caption = "\n".join(value for value in (copy.get("caption"), copy.get("cta")) if value)
    await record_product_message(
        session,
        row,
        cipher,
        "Sua peça está pronta para revisão no seu espaço. Responda a esta mensagem para pedir um ajuste."
        + ("\n" + caption if caption else ""),
        kind="result",
        sha=result["sha256"],
    )


async def list_product_messages(settings, database, tenant, business, actor):
    from app.services.whatsapp_materials import WhatsAppMaterialsService

    cipher = MotionContext(settings)
    async with database.transaction(tenant, actor) as session:
        await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
        rows = (
            (
                await session.execute(
                    text("""SELECT id,kind,message_ciphertext,provider_message_id,simulated,created_at,expires_at
          FROM message_creation_deliveries WHERE tenant_id=:tenant AND business_id=:business ORDER BY created_at DESC LIMIT 50"""),
                    {"tenant": tenant, "business": business},
                )
            )
            .mappings()
            .all()
        )
    return [
        {k: v for k, v in row.items() if k != "message_ciphertext"} | cipher.open(row["message_ciphertext"])
        for row in rows
    ]
