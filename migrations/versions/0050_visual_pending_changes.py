"""Defer owner-requested visual source changes until admitted work finishes."""

from alembic import op

revision = "0050_visual_pending_changes"
down_revision = "0049_visual_global_budget"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE business_visual_pending_changes (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, operation_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id), kind text NOT NULL, resource_key text NOT NULL,
      request_hash char(64) NOT NULL, payload jsonb NOT NULL,
      state text NOT NULL CHECK(state IN ('pending','completed','failed','cancelled')), error_code text,
      requested_at timestamptz NOT NULL DEFAULT clock_timestamp(), finished_at timestamptz,
      PRIMARY KEY(tenant_id,business_id,operation_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("""CREATE UNIQUE INDEX business_visual_pending_resource
      ON business_visual_pending_changes(tenant_id,business_id,resource_key) WHERE state IN ('pending','failed')""")
    op.execute("""CREATE TABLE visual_change_completed_previews (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES user_accounts(id),
      preview_id uuid NOT NULL REFERENCES media_previews(id) ON DELETE CASCADE,
      operation_id uuid NOT NULL, fence bigint NOT NULL CHECK(fence>0),
      sha256 char(64) NOT NULL, visual_fingerprint char(64) NOT NULL,
      consent_accepted_at timestamptz NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(tenant_id,business_id,preview_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    for table in ("business_visual_pending_changes", "visual_change_completed_previews"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY owner_{table} ON {table} TO meu_braco_direito_app
          USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute("""GRANT SELECT,INSERT,UPDATE(state,finished_at,error_code) ON business_visual_pending_changes
      TO meu_braco_direito_app""")
    op.execute("GRANT SELECT,INSERT ON visual_change_completed_previews TO meu_braco_direito_app")


def downgrade():
    op.execute("DROP TABLE visual_change_completed_previews")
    op.execute("DROP TABLE business_visual_pending_changes")
