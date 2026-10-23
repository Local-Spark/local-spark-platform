"""Versioned owner-confirmed editorial context, isolated per business."""

from alembic import op

revision = "0021_business_context"
down_revision = "0020_audio_transcription"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE business_context_heads (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, version integer NOT NULL DEFAULT 0 CHECK(version>=0),
      PRIMARY KEY(tenant_id,business_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("""CREATE TABLE business_context_versions (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, version integer NOT NULL CHECK(version>0),
      operation_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES user_accounts(id),
      request_hash char(64) NOT NULL, document jsonb NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(tenant_id,business_id,version),
      UNIQUE(tenant_id,business_id,operation_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES business_context_heads(tenant_id,business_id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    for table in ("business_context_heads", "business_context_versions"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY owner_context ON {table} TO meu_braco_direito_app
          USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute("GRANT SELECT,INSERT,UPDATE(version) ON business_context_heads TO meu_braco_direito_app")
    op.execute("GRANT SELECT,INSERT ON business_context_versions TO meu_braco_direito_app")


def downgrade():
    op.execute("DROP TABLE business_context_versions")
    op.execute("DROP TABLE business_context_heads")
