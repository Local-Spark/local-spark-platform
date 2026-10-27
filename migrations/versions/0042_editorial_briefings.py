"""Owner-scoped durable source resolution for experimental editorial briefings."""

from alembic import op

revision = "0042_editorial_briefings"
down_revision = "0041_visual_cost_ledger"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE editorial_briefings (
      id uuid PRIMARY KEY, tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),
      source_asset_id uuid NOT NULL REFERENCES whatsapp_material_assets(id) ON DELETE CASCADE,
      operation_id uuid NOT NULL, request_hash char(64) NOT NULL, source_digest char(64),
      state text NOT NULL CHECK(state IN ('submitted','prepared','needs_clarification','uncertain')),
      catalog_snapshot jsonb,
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE(tenant_id,business_id,operation_id), UNIQUE(tenant_id,business_id,source_asset_id),
      UNIQUE(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id),
      CHECK((state='prepared' AND catalog_snapshot IS NOT NULL) OR
            (state<>'prepared' AND catalog_snapshot IS NULL)))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    op.execute("ALTER TABLE editorial_briefings ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE editorial_briefings FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY owner_editorial_briefing ON editorial_briefings TO meu_braco_direito_app
      USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute(
        "GRANT SELECT,INSERT,UPDATE(state,catalog_snapshot,updated_at) ON editorial_briefings TO meu_braco_direito_app"
    )
    op.execute("GRANT SELECT(sender_hash,expires_at) ON whatsapp_material_events TO meu_braco_direito_app")
    op.execute("ALTER TABLE editorial_proposals ADD COLUMN briefing_id uuid")
    op.execute("ALTER TABLE editorial_proposals ADD COLUMN briefing_required boolean NOT NULL DEFAULT false")
    op.execute("""ALTER TABLE editorial_proposals ADD CONSTRAINT editorial_proposals_briefing_fk
      FOREIGN KEY(tenant_id,business_id,briefing_id) REFERENCES editorial_briefings(tenant_id,business_id,id)
      ON DELETE SET NULL (briefing_id)""")


def downgrade():
    op.execute("REVOKE SELECT(sender_hash,expires_at) ON whatsapp_material_events FROM meu_braco_direito_app")
    op.execute("ALTER TABLE editorial_proposals DROP CONSTRAINT editorial_proposals_briefing_fk")
    op.execute("ALTER TABLE editorial_proposals DROP COLUMN briefing_required")
    op.execute("ALTER TABLE editorial_proposals DROP COLUMN briefing_id")
    op.execute("DROP TABLE editorial_briefings")
