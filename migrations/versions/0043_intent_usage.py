"""Reserve and audit semantic interpretation independently of business content."""

from alembic import op

revision = "0043_intent_usage"
down_revision = "0042_editorial_briefings"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE intent_jev_consents (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES user_accounts(id),
      accepted_at timestamptz NOT NULL DEFAULT now(), revoked_at timestamptz,
      PRIMARY KEY(tenant_id,business_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("""ALTER TABLE editorial_briefings ADD COLUMN intent_kind text
      CHECK(intent_kind IN ('content_request','price','availability','question','other'))""")
    op.execute("""ALTER TABLE editorial_briefings ADD COLUMN suggested_format text
      CHECK(suggested_format IN ('photo','carousel','short_video','story'))""")
    op.execute("GRANT UPDATE(intent_kind,suggested_format) ON editorial_briefings TO meu_braco_direito_app")
    op.execute("""CREATE TABLE editorial_intent_usage (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, actor_id uuid NOT NULL,
      operation_id uuid NOT NULL, request_hash char(64) NOT NULL,
      provider text NOT NULL, model text NOT NULL,
      rate_input_micros bigint NOT NULL CHECK(rate_input_micros > 0),
      rate_output_micros bigint NOT NULL CHECK(rate_output_micros >= 0),
      reserved_micros bigint NOT NULL CHECK(reserved_micros > 0),
      estimated_micros bigint CHECK(estimated_micros >= 0),
      input_tokens integer CHECK(input_tokens >= 0), output_tokens integer CHECK(output_tokens >= 0),
      state text NOT NULL CHECK(state IN ('submitted','completed','uncertain')),
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(tenant_id, operation_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("CREATE INDEX editorial_intent_usage_daily ON editorial_intent_usage(tenant_id,created_at)")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    op.execute("ALTER TABLE intent_jev_consents ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE intent_jev_consents FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY owner_intent_jev_consent ON intent_jev_consents
      TO meu_braco_direito_app USING(tenant_id={tenant} AND {owner})
      WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute(
        "GRANT SELECT,INSERT,UPDATE(actor_id,accepted_at,revoked_at) ON intent_jev_consents TO meu_braco_direito_app"
    )
    op.execute("ALTER TABLE editorial_intent_usage ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE editorial_intent_usage FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY owner_intent_usage_read ON editorial_intent_usage FOR SELECT
      TO meu_braco_direito_app USING(tenant_id={tenant} AND {owner})""")
    op.execute(f"""CREATE POLICY owner_intent_usage_insert ON editorial_intent_usage FOR INSERT
      TO meu_braco_direito_app WITH CHECK(tenant_id={tenant} AND actor_id={actor} AND {owner})""")
    op.execute(f"""CREATE POLICY owner_intent_usage_update ON editorial_intent_usage FOR UPDATE
      TO meu_braco_direito_app USING(tenant_id={tenant} AND actor_id={actor} AND {owner})
      WITH CHECK(tenant_id={tenant} AND actor_id={actor} AND {owner})""")
    op.execute("""GRANT SELECT,INSERT,UPDATE(state,input_tokens,output_tokens,estimated_micros,updated_at)
      ON editorial_intent_usage TO meu_braco_direito_app""")


def downgrade():
    op.execute("DROP TABLE editorial_intent_usage")
    op.execute("DROP TABLE intent_jev_consents")
    op.execute("ALTER TABLE editorial_briefings DROP COLUMN suggested_format")
    op.execute("ALTER TABLE editorial_briefings DROP COLUMN intent_kind")
