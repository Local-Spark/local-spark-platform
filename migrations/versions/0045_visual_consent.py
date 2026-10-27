"""Separate owner consent for transmitting image references to visual AI."""

from alembic import op

revision = "0045_visual_consent"
down_revision = "0044_briefing_budget_block"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE visual_ai_consents (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES user_accounts(id),
      accepted_at timestamptz NOT NULL DEFAULT now(), revoked_at timestamptz,
      PRIMARY KEY(tenant_id,business_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    op.execute("ALTER TABLE visual_ai_consents ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE visual_ai_consents FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY owner_visual_ai_consent ON visual_ai_consents
      TO meu_braco_direito_app USING(tenant_id={tenant} AND {owner})
      WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute(
        "GRANT SELECT,INSERT,UPDATE(actor_id,accepted_at,revoked_at) ON visual_ai_consents TO meu_braco_direito_app"
    )


def downgrade():
    op.execute("DROP TABLE visual_ai_consents")
