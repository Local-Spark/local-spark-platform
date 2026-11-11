"""Private scene boards and exact-version owner decision before video rendering."""

from alembic import op

revision = "0114_motion_storyboards"
down_revision = "0113_motion_production"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE motion_storyboards (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,request_id uuid NOT NULL,
      version_id uuid NOT NULL,content_sha256 char(64) NOT NULL,payload_ciphertext text NOT NULL,
      state text NOT NULL CHECK(state IN ('awaiting_approval','approved','rejected','rendering')),
      decision_operation_id uuid,decision_hash char(64),feedback_ciphertext text,
      created_at timestamptz NOT NULL DEFAULT now(),decided_at timestamptz,
      PRIMARY KEY(tenant_id,business_id,request_id),UNIQUE(tenant_id,version_id),
      UNIQUE(tenant_id,decision_operation_id),
      FOREIGN KEY(tenant_id,business_id,request_id) REFERENCES motion_requests(tenant_id,business_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    op.execute("ALTER TABLE motion_storyboards ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE motion_storyboards FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY motion_storyboard_owner ON motion_storyboards TO meu_braco_direito_app
      USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute("""GRANT SELECT,INSERT,UPDATE(state,decision_operation_id,decision_hash,feedback_ciphertext,decided_at)
      ON motion_storyboards TO meu_braco_direito_app""")


def downgrade():
    op.execute("DROP TABLE motion_storyboards")
