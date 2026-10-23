"""Owner-scoped, durable editorial conversation decisions for local simulation."""

from alembic import op

revision = "0026_editorial_conversation"
down_revision = "0025_editorial_usage_summary"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE editorial_conversation_decisions (
      id uuid PRIMARY KEY, tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id), operation_id uuid NOT NULL,
      request_hash char(64) NOT NULL, intent text NOT NULL,
      state text NOT NULL CHECK(state IN ('awaiting_confirmation','needs_review','confirmed','discarded')),
      proposal jsonb NOT NULL, reply text NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now(), decided_at timestamptz,
      UNIQUE(tenant_id,business_id,operation_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute(
        "CREATE INDEX editorial_conversation_business ON "
        "editorial_conversation_decisions(tenant_id,business_id,created_at DESC)"
    )
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    op.execute("ALTER TABLE editorial_conversation_decisions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE editorial_conversation_decisions FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY owner_conversation ON editorial_conversation_decisions
      TO meu_braco_direito_app USING(tenant_id={tenant} AND {owner})
      WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute("""GRANT SELECT,INSERT,UPDATE(state,reply,decided_at)
      ON editorial_conversation_decisions TO meu_braco_direito_app""")


def downgrade():
    op.execute("DROP TABLE editorial_conversation_decisions")
