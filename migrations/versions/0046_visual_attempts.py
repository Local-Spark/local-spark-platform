"""Bind one visual submission intent to a fenced private preview."""

from alembic import op

revision = "0046_visual_attempts"
down_revision = "0045_visual_consent"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE visual_ai_attempts (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      preview_id uuid NOT NULL REFERENCES media_previews(id) ON DELETE CASCADE,
      operation_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES user_accounts(id),
      request_hash char(64) NOT NULL, dispatch_fence bigint NOT NULL CHECK(dispatch_fence>0),
      reservation_id uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(tenant_id,preview_id), UNIQUE(tenant_id,operation_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id),
      FOREIGN KEY(tenant_id,reservation_id) REFERENCES visual_cost_reservations(tenant_id,id))""")
    op.execute("ALTER TABLE visual_ai_attempts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE visual_ai_attempts FORCE ROW LEVEL SECURITY")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    op.execute(f"""CREATE POLICY worker_tenant_visual_attempt ON visual_ai_attempts
      TO meu_braco_direito_correlator USING(tenant_id={tenant}) WITH CHECK(tenant_id={tenant})""")
    op.execute("GRANT SELECT,INSERT ON visual_ai_attempts TO meu_braco_direito_correlator")


def downgrade():
    op.execute("DROP TABLE visual_ai_attempts")
