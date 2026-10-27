"""Track consent withdrawal and admitted visual operations per owner business."""

from alembic import op

revision = "0048_visual_consent_gate"
down_revision = "0047_visual_preview_mode"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE visual_consent_gates (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      state text NOT NULL CHECK (state IN ('active','revocation_pending','revoked')),
      updated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (tenant_id,business_id),
      FOREIGN KEY (tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("""CREATE TABLE visual_consent_runs (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, preview_id uuid NOT NULL,
      operation_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES user_accounts(id),
      fence bigint NOT NULL CHECK (fence>0), state text NOT NULL CHECK (state IN ('in_flight','finished')),
      consent_accepted_at timestamptz NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now(), finished_at timestamptz,
      finished_during_withdrawal boolean NOT NULL DEFAULT false,
      completed_sha256 char(64),
      CHECK (NOT finished_during_withdrawal OR completed_sha256 IS NOT NULL),
      PRIMARY KEY (tenant_id,preview_id), UNIQUE (tenant_id,operation_id),
      FOREIGN KEY (tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    for table in ("visual_consent_gates", "visual_consent_runs"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY owner_{table} ON {table} TO meu_braco_direito_app
          USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute("GRANT SELECT,INSERT,UPDATE(state,updated_at) ON visual_consent_gates TO meu_braco_direito_app")
    op.execute(
        "GRANT SELECT,INSERT,UPDATE(state,finished_at,finished_during_withdrawal,completed_sha256) "
        "ON visual_consent_runs TO meu_braco_direito_app"
    )


def downgrade():
    op.execute("DROP TABLE visual_consent_runs")
    op.execute("DROP TABLE visual_consent_gates")
