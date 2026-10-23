"""Consent, durable proposal requests and a bounded text-provider ledger."""

from alembic import op

revision = "0022_editorial_proposals"
down_revision = "0021_business_context"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE editorial_ai_consents (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES user_accounts(id),
      accepted_at timestamptz NOT NULL DEFAULT now(), revoked_at timestamptz,
      PRIMARY KEY(tenant_id,business_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("""CREATE TABLE editorial_proposals (
      id uuid PRIMARY KEY, tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id), operation_id uuid NOT NULL,
      request_hash char(64) NOT NULL, context_version integer NOT NULL CHECK(context_version>=0),
      source_asset_id uuid REFERENCES whatsapp_material_assets(id) ON DELETE CASCADE,
      state text NOT NULL DEFAULT 'pending' CHECK(state IN
        ('pending','dispatching','submitted','completed','rejected','budget_exceeded','uncertain')),
      document jsonb, error_code text, reserved_tokens integer NOT NULL DEFAULT 0,
      input_tokens integer, output_tokens integer, model text,
      dispatch_owner uuid, dispatch_lease_until timestamptz, dispatch_fence bigint NOT NULL DEFAULT 0,
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
      expires_at timestamptz NOT NULL DEFAULT now()+interval '30 days',
      UNIQUE(tenant_id,business_id,operation_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("CREATE INDEX editorial_proposals_due ON editorial_proposals(state,created_at,id)")
    op.execute("CREATE INDEX editorial_proposals_owner ON editorial_proposals(tenant_id,business_id,created_at DESC)")
    op.execute("""CREATE TABLE editorial_ai_usage (
      proposal_id uuid PRIMARY KEY, tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      reserved_tokens integer NOT NULL CHECK(reserved_tokens>0),
      input_tokens integer, output_tokens integer,
      state text NOT NULL CHECK(state IN ('submitted','completed','uncertain')),
      created_at timestamptz NOT NULL DEFAULT now(),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("CREATE INDEX editorial_ai_usage_daily ON editorial_ai_usage(tenant_id,created_at)")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    for table in ("editorial_ai_consents", "editorial_proposals"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY owner_editorial ON {table} TO meu_braco_direito_app
          USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
        op.execute(f"""CREATE POLICY worker_editorial ON {table} TO meu_braco_direito_correlator
          USING(true) WITH CHECK(true)""")
    op.execute("""CREATE POLICY worker_proposal_expiry ON editorial_proposals FOR DELETE
      TO meu_braco_direito_correlator USING(expires_at<=now())""")
    op.execute(f"""CREATE POLICY owner_proposal_delete ON editorial_proposals FOR DELETE
      TO meu_braco_direito_app USING(tenant_id={tenant} AND {owner})""")
    op.execute("ALTER TABLE editorial_ai_usage ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE editorial_ai_usage FORCE ROW LEVEL SECURITY")
    op.execute("""CREATE POLICY worker_usage ON editorial_ai_usage TO meu_braco_direito_correlator
      USING(true) WITH CHECK(true)""")
    op.execute("""GRANT SELECT,INSERT,UPDATE(actor_id,accepted_at,revoked_at)
      ON editorial_ai_consents TO meu_braco_direito_app""")
    op.execute("GRANT SELECT,INSERT ON editorial_proposals TO meu_braco_direito_app")
    op.execute("GRANT DELETE ON editorial_proposals TO meu_braco_direito_app")
    op.execute("GRANT DELETE ON editorial_proposals TO meu_braco_direito_correlator")
    op.execute("GRANT SELECT ON editorial_ai_consents,business_context_versions TO meu_braco_direito_correlator")
    op.execute("""GRANT SELECT,UPDATE(state,document,error_code,reserved_tokens,input_tokens,
      output_tokens,model,updated_at,dispatch_owner,dispatch_lease_until,dispatch_fence)
      ON editorial_proposals TO meu_braco_direito_correlator""")
    op.execute("""GRANT SELECT,INSERT,UPDATE(state,input_tokens,output_tokens)
      ON editorial_ai_usage TO meu_braco_direito_correlator""")
    op.execute("""CREATE POLICY worker_context ON business_context_versions FOR SELECT
      TO meu_braco_direito_correlator USING(true)""")


def downgrade():
    op.execute("DROP POLICY worker_context ON business_context_versions")
    op.execute("DROP TABLE editorial_ai_usage")
    op.execute("DROP TABLE editorial_proposals")
    op.execute("DROP TABLE editorial_ai_consents")
