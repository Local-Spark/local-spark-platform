"""Billing identities, isolated processor, durable jobs and audited six-month sponsorships."""

from alembic import op

revision = "0005_billing"
down_revision = "0004_structured_locality"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_billing') THEN
      CREATE ROLE meu_braco_direito_billing NOLOGIN NOSUPERUSER NOBYPASSRLS; END IF; END $$""")
    op.execute("GRANT USAGE ON SCHEMA public TO meu_braco_direito_billing")
    for sql in [
        """CREATE TABLE billing_jobs (
          id uuid PRIMARY KEY, tenant_id uuid REFERENCES tenants(id), actor_id uuid REFERENCES user_accounts(id),
          livemode boolean NOT NULL, kind text NOT NULL CHECK(kind IN ('checkout','reconcile')),
          dedupe_key varchar(250) NOT NULL, event_type varchar(100), object_id varchar(128),
          price_id varchar(128), amount_minor integer CHECK(amount_minor>0),
          state text NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','leased','dispatched','completed','failed')),
          lease_until timestamptz, fencing_token bigint NOT NULL DEFAULT 0,
          attempts integer NOT NULL DEFAULT 0, result jsonb, created_at timestamptz NOT NULL DEFAULT now(),
          UNIQUE(livemode,dedupe_key), CHECK(kind<>'checkout' OR
            (tenant_id IS NOT NULL AND actor_id IS NOT NULL AND price_id IS NOT NULL AND amount_minor IS NOT NULL)))""",
        "CREATE INDEX billing_jobs_pending ON billing_jobs(created_at,id) WHERE state IN ('pending','leased')",
        "CREATE INDEX billing_jobs_tenant ON billing_jobs(tenant_id,created_at DESC)",
        """CREATE TABLE billing_accounts (
          tenant_id uuid NOT NULL REFERENCES tenants(id), livemode boolean NOT NULL,
          status text NOT NULL DEFAULT 'inactive', paid_until timestamptz,
          subscription_id varchar(128), customer_id varchar(128), checkout_id uuid,
          blocked boolean NOT NULL DEFAULT false, lease_until timestamptz,
          fencing_token bigint NOT NULL DEFAULT 0, PRIMARY KEY(tenant_id,livemode),
          UNIQUE(livemode,subscription_id), UNIQUE(livemode,customer_id))""",
        """CREATE TABLE billing_checkouts (
          id uuid PRIMARY KEY REFERENCES billing_jobs(id), tenant_id uuid NOT NULL REFERENCES tenants(id),
          livemode boolean NOT NULL, price_id varchar(128) NOT NULL, amount_minor integer NOT NULL,
          status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','open','complete','expired')),
          session_id varchar(128), url text, origin text NOT NULL,
          expires_at timestamptz NOT NULL DEFAULT now()+interval '1 hour', UNIQUE(livemode,session_id))""",
        "ALTER TABLE billing_accounts ADD FOREIGN KEY(checkout_id) REFERENCES billing_checkouts(id)",
        """CREATE TABLE billing_sponsorships (
          id uuid PRIMARY KEY, tenant_id uuid NOT NULL UNIQUE REFERENCES tenants(id),
          actor_id uuid NOT NULL REFERENCES user_accounts(id), idempotency_key varchar(128) NOT NULL,
          reason varchar(500) NOT NULL, starts_at timestamptz NOT NULL DEFAULT now(),
          ends_at timestamptz NOT NULL DEFAULT now()+interval '6 months', revoked_at timestamptz,
          CHECK(ends_at>starts_at))""",
        """CREATE TABLE billing_audit (
          id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES tenants(id),
          actor_id uuid REFERENCES user_accounts(id),
          operation_id uuid NOT NULL, action varchar(100) NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
          UNIQUE(operation_id,action))""",
        """CREATE TABLE billing_outbox (
          id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES tenants(id), event_type varchar(100) NOT NULL,
          operation_id uuid NOT NULL, state text NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','delivered')),
          created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(operation_id,event_type))""",
    ]:
        op.execute(sql)
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    member = f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} AND m.actor_id={actor} AND m.active)"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.active AND m.role='owner')"
    )
    for table in (
        "billing_jobs",
        "billing_accounts",
        "billing_checkouts",
        "billing_sponsorships",
        "billing_audit",
        "billing_outbox",
    ):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY billing_processor ON {table} TO meu_braco_direito_billing USING(true) WITH CHECK(true)"
        )
        op.execute(f"""CREATE POLICY billing_read ON {table} FOR SELECT TO meu_braco_direito_app USING (
          (tenant_id={tenant} AND {member}) OR public.is_platform_staff())""")
        op.execute(f"GRANT SELECT ON {table} TO meu_braco_direito_app")
        op.execute(f"GRANT SELECT ON {table} TO meu_braco_direito_billing")
        if table != "billing_sponsorships":
            op.execute(f"GRANT INSERT ON {table} TO meu_braco_direito_billing")
        if table in {"billing_jobs", "billing_accounts", "billing_checkouts"}:
            op.execute(f"GRANT UPDATE ON {table} TO meu_braco_direito_billing")
    op.execute(f"""CREATE POLICY billing_checkout_request ON billing_jobs FOR INSERT TO meu_braco_direito_app
      WITH CHECK (tenant_id={tenant} AND actor_id={actor} AND kind='checkout' AND state='pending' AND {owner})""")
    op.execute("GRANT INSERT ON billing_jobs TO meu_braco_direito_app")
    op.execute(f"""CREATE POLICY sponsorship_create ON billing_sponsorships FOR INSERT TO meu_braco_direito_app
      WITH CHECK(public.is_platform_staff() AND actor_id={actor})""")
    op.execute("""CREATE POLICY sponsorship_revoke ON billing_sponsorships FOR UPDATE TO meu_braco_direito_app
      USING(public.is_platform_staff()) WITH CHECK(public.is_platform_staff())""")
    op.execute("GRANT INSERT ON billing_sponsorships TO meu_braco_direito_app")
    op.execute("GRANT UPDATE(revoked_at) ON billing_sponsorships TO meu_braco_direito_app")
    for table in ("billing_audit", "billing_outbox"):
        op.execute(
            f"CREATE POLICY billing_staff_event ON {table} FOR INSERT "
            "TO meu_braco_direito_app WITH CHECK(public.is_platform_staff())"
        )
        op.execute(f"GRANT INSERT ON {table} TO meu_braco_direito_app")
    for table in ("memberships", "user_accounts", "tenants"):
        op.execute(
            f"CREATE POLICY billing_reference_read ON {table} FOR SELECT TO meu_braco_direito_billing USING(true)"
        )
    op.execute("GRANT SELECT ON memberships TO meu_braco_direito_billing")
    op.execute("GRANT SELECT(id,active,email_verified) ON user_accounts TO meu_braco_direito_billing")
    op.execute("GRANT SELECT(id) ON tenants TO meu_braco_direito_billing")
    op.execute("GRANT SELECT ON alembic_version TO meu_braco_direito_billing")


def downgrade():
    for table in ("memberships", "user_accounts", "tenants"):
        op.execute(f"DROP POLICY billing_reference_read ON {table}")
    op.execute("REVOKE SELECT ON memberships FROM meu_braco_direito_billing")
    op.execute("REVOKE SELECT(id,active,email_verified) ON user_accounts FROM meu_braco_direito_billing")
    op.execute("REVOKE SELECT(id) ON tenants FROM meu_braco_direito_billing")
    op.execute("REVOKE SELECT ON alembic_version FROM meu_braco_direito_billing")
    op.execute("ALTER TABLE billing_accounts DROP CONSTRAINT billing_accounts_checkout_id_fkey")
    for table in (
        "billing_outbox",
        "billing_audit",
        "billing_sponsorships",
        "billing_checkouts",
        "billing_accounts",
        "billing_jobs",
    ):
        op.execute(f"DROP TABLE {table}")
