"""Identity, constrained initial provisioning and audited read-only platform administration."""

from alembic import op

revision = "0002_identity_onboarding"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade():
    for sql in [
        """CREATE TABLE user_accounts (
          id uuid PRIMARY KEY, issuer text NOT NULL, subject text NOT NULL,
          display_name varchar(120) NOT NULL, email text, email_verified boolean NOT NULL,
          active boolean NOT NULL DEFAULT true, created_at timestamptz NOT NULL DEFAULT now(),
          UNIQUE(issuer,subject))""",
        """CREATE TABLE platform_staff (
          actor_id uuid PRIMARY KEY REFERENCES user_accounts(id), active boolean NOT NULL DEFAULT true)""",
        """CREATE TABLE onboarding_registrations (
          actor_id uuid PRIMARY KEY REFERENCES user_accounts(id), tenant_id uuid NOT NULL UNIQUE,
          request_hash char(64) NOT NULL, response jsonb,
          FOREIGN KEY(tenant_id) REFERENCES tenants(id) DEFERRABLE INITIALLY DEFERRED)""",
        """CREATE TABLE business_profiles (
          tenant_id uuid NOT NULL, business_id uuid NOT NULL, category varchar(60) NOT NULL,
          city varchar(100) NOT NULL, description varchar(1000) NOT NULL,
          phone varchar(30) NOT NULL, phone_verified boolean NOT NULL DEFAULT false,
          brand_color varchar(7) NOT NULL, completed boolean NOT NULL DEFAULT true,
          PRIMARY KEY(tenant_id,business_id),
          FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""",
        """CREATE TABLE consents (
          tenant_id uuid NOT NULL REFERENCES tenants(id), actor_id uuid NOT NULL REFERENCES user_accounts(id),
          purpose text NOT NULL CHECK(purpose IN ('terms','privacy')), version text NOT NULL,
          accepted_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(tenant_id,actor_id,purpose,version))""",
        """CREATE TABLE platform_audit (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(), actor_id uuid NOT NULL REFERENCES user_accounts(id),
          action text NOT NULL, created_at timestamptz NOT NULL DEFAULT now())""",
        "CREATE INDEX memberships_actor ON memberships(actor_id,tenant_id) WHERE active",
        "CREATE INDEX tenants_created ON tenants(created_at)",
    ]:
        op.execute(sql)
    for table in (
        "user_accounts",
        "platform_staff",
        "onboarding_registrations",
        "business_profiles",
        "consents",
        "platform_audit",
    ):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    op.execute(
        f"CREATE POLICY self_account ON user_accounts TO meu_braco_direito_app "
        f"USING (id={actor}) WITH CHECK (id={actor})"
    )
    op.execute(
        f"CREATE POLICY self_staff ON platform_staff FOR SELECT TO meu_braco_direito_app USING (actor_id={actor})"
    )
    op.execute(
        f"CREATE POLICY self_registration_read ON onboarding_registrations FOR SELECT "
        f"TO meu_braco_direito_app "
        f"USING (actor_id={actor})"
    )
    op.execute(
        f"CREATE POLICY self_registration_update ON onboarding_registrations FOR UPDATE "
        f"TO meu_braco_direito_app "
        f"USING (actor_id={actor})"
    )
    op.execute(f"""CREATE POLICY new_registration ON onboarding_registrations FOR INSERT TO meu_braco_direito_app
      WITH CHECK (actor_id={actor} AND tenant_id={tenant} AND NOT EXISTS(SELECT 1 FROM tenants WHERE id=tenant_id))""")
    for table, predicate in (("tenants", f"id={tenant}"), ("memberships", f"tenant_id={tenant} AND actor_id={actor}")):
        op.execute(f"DROP POLICY tenant_isolation ON {table}")
        op.execute(f"CREATE POLICY tenant_isolation ON {table} FOR SELECT TO meu_braco_direito_app USING ({predicate})")
    op.execute(
        f"CREATE POLICY own_memberships ON memberships FOR SELECT "
        f"TO meu_braco_direito_app "
        f"USING (actor_id={actor} AND active)"
    )
    op.execute(f"""CREATE POLICY own_tenants ON tenants FOR SELECT TO meu_braco_direito_app USING
      (EXISTS(SELECT 1 FROM memberships WHERE tenant_id=tenants.id AND actor_id={actor} AND active))""")
    registration = f"EXISTS(SELECT 1 FROM onboarding_registrations r WHERE r.actor_id={actor} AND r.tenant_id={tenant})"
    op.execute(
        f"CREATE POLICY bootstrap_tenant ON tenants FOR INSERT "
        f"TO meu_braco_direito_app WITH CHECK (id={tenant} AND {registration})"
    )
    op.execute(f"""CREATE POLICY bootstrap_owner ON memberships FOR INSERT TO meu_braco_direito_app
      WITH CHECK (actor_id={actor} AND tenant_id={tenant} AND role='owner' AND {registration})""")
    for table in ("business_profiles", "consents"):
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} TO meu_braco_direito_app "
            f"USING (tenant_id={tenant}) "
            f"WITH CHECK (tenant_id={tenant})"
        )
    for table in ("businesses", "business_profiles"):
        op.execute(f"""CREATE POLICY own_business_read ON {table} FOR SELECT TO meu_braco_direito_app USING
          (EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={table}.tenant_id
            AND m.actor_id={actor} AND m.active))""")
    # Narrow, argument-free boolean; no dynamic SQL or caller-controlled search path.
    op.execute(f"""CREATE FUNCTION public.is_platform_staff() RETURNS boolean LANGUAGE sql STABLE
      SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      SELECT EXISTS(SELECT 1 FROM public.platform_staff s JOIN public.user_accounts u ON u.id=s.actor_id
        WHERE s.actor_id={actor} AND s.active AND u.active) $$""")
    op.execute("REVOKE ALL ON FUNCTION public.is_platform_staff() FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION public.is_platform_staff() TO meu_braco_direito_app")
    for table in ("tenants", "memberships", "businesses", "business_profiles", "user_accounts"):
        op.execute(
            f"CREATE POLICY staff_read ON {table} FOR SELECT TO meu_braco_direito_app "
            f"USING (public.is_platform_staff())"
        )
    op.execute(f"""CREATE POLICY staff_audit ON platform_audit TO meu_braco_direito_app
      USING (actor_id={actor} AND public.is_platform_staff())
      WITH CHECK (actor_id={actor} AND public.is_platform_staff())""")
    op.execute(
        "GRANT SELECT,INSERT ON user_accounts, onboarding_registrations, "
        "business_profiles, consents, platform_audit TO meu_braco_direito_app"
    )
    op.execute("GRANT UPDATE(display_name,email,email_verified) ON user_accounts TO meu_braco_direito_app")
    op.execute("GRANT UPDATE(response) ON onboarding_registrations TO meu_braco_direito_app")
    op.execute("GRANT SELECT ON platform_staff TO meu_braco_direito_app")
    op.execute("GRANT INSERT ON tenants,memberships TO meu_braco_direito_app")


def downgrade():
    for table in ("businesses", "business_profiles"):
        op.execute(f"DROP POLICY own_business_read ON {table}")
    for table in ("tenants", "memberships", "businesses", "business_profiles", "user_accounts"):
        op.execute(f"DROP POLICY staff_read ON {table}")
    op.execute("DROP TABLE platform_audit")
    op.execute("DROP FUNCTION public.is_platform_staff()")
    for sql in (
        "DROP POLICY bootstrap_owner ON memberships",
        "DROP POLICY bootstrap_tenant ON tenants",
        "DROP POLICY own_tenants ON tenants",
        "DROP POLICY own_memberships ON memberships",
        "REVOKE INSERT ON tenants,memberships FROM meu_braco_direito_app",
    ):
        op.execute(sql)
    for table in ("consents", "business_profiles", "onboarding_registrations", "platform_staff", "user_accounts"):
        op.execute(f"DROP TABLE {table}")
    op.execute("DROP INDEX memberships_actor")
    op.execute("DROP INDEX tenants_created")
    for table, column in (("tenants", "id"), ("memberships", "tenant_id")):
        predicate = f"{column}=nullif(current_setting('app.tenant_id',true),'')::uuid"
        if table == "memberships":
            predicate += " AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid"
        op.execute(f"DROP POLICY tenant_isolation ON {table}")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} TO meu_braco_direito_app "
            f"USING ({predicate}) WITH CHECK ({predicate})"
        )
