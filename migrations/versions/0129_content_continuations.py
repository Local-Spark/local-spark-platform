"""Explicit owner replies link real inbound materials to one prior delivery."""

from alembic import op

revision = "0129_content_continuations"
down_revision = "0128_creation_lab_continuations"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE content_source_continuations (
      source_event_id uuid PRIMARY KEY REFERENCES whatsapp_material_events(id) ON DELETE CASCADE,
      parent_delivery_id uuid NOT NULL UNIQUE REFERENCES content_deliveries(id) ON DELETE CASCADE,
      parent_source_id uuid NOT NULL REFERENCES whatsapp_material_events(id) ON DELETE CASCADE,
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES user_accounts(id),
      kind text NOT NULL CHECK(kind IN ('reply','adjustment')),
      note_ciphertext text NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      CHECK(source_event_id<>parent_source_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id)
    )""")
    op.execute("ALTER TABLE content_source_continuations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE content_source_continuations FORCE ROW LEVEL SECURITY")
    owner = """tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
      AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid
      AND EXISTS(SELECT 1 FROM memberships m JOIN user_accounts u ON u.id=m.actor_id
        WHERE m.tenant_id=content_source_continuations.tenant_id AND m.actor_id=content_source_continuations.actor_id
          AND m.role='owner' AND m.active AND u.active)"""
    op.execute(
        f"CREATE POLICY owner_continuation ON content_source_continuations TO meu_braco_direito_app USING({owner}) WITH CHECK({owner})"
    )
    op.execute(
        "CREATE POLICY worker_continuation ON content_source_continuations FOR SELECT TO meu_braco_direito_correlator USING(true)"
    )
    op.execute("GRANT SELECT,INSERT ON content_source_continuations TO meu_braco_direito_app")
    op.execute("GRANT SELECT ON content_source_continuations TO meu_braco_direito_correlator")


def downgrade():
    raise RuntimeError("Conversation provenance must be retained")
