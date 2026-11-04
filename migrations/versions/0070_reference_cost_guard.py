"""Operational accounting for future reference-discovery provider effects."""

from alembic import op

revision = "0070_reference_cost_guard"
down_revision = "0069_reference_recovery"
branch_labels = None
depends_on = None


def upgrade():
    # The correlator may lock, but cannot directly update, these identity rows.
    # Both locks live until the caller's claim transaction ends.
    op.execute("""DO $$ BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_reference_lock') THEN
        CREATE ROLE meu_braco_direito_reference_lock NOLOGIN NOSUPERUSER NOBYPASSRLS
          NOCREATEDB NOCREATEROLE NOREPLICATION;
      END IF;
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_reference_lock'
        AND (rolcanlogin OR rolsuper OR rolbypassrls OR rolcreatedb OR rolcreaterole OR rolreplication)) OR
        EXISTS (SELECT 1 FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid OR r.oid=m.member
          WHERE r.rolname='meu_braco_direito_reference_lock') THEN
        RAISE EXCEPTION 'UNSAFE_REFERENCE_LOCK_ROLE';
      END IF;
    END $$""")
    op.execute("GRANT USAGE ON SCHEMA public TO meu_braco_direito_reference_lock")
    op.execute("""GRANT SELECT(id,active),UPDATE(active) ON user_accounts TO meu_braco_direito_reference_lock""")
    op.execute("""GRANT SELECT(tenant_id,actor_id,role,active),UPDATE(active) ON memberships
      TO meu_braco_direito_reference_lock""")
    op.execute("""CREATE POLICY reference_lock_account ON user_accounts TO meu_braco_direito_reference_lock
      USING(id=nullif(current_setting('app.actor_id',true),'')::uuid)
      WITH CHECK(id=nullif(current_setting('app.actor_id',true),'')::uuid)""")
    op.execute("""CREATE POLICY reference_lock_membership ON memberships TO meu_braco_direito_reference_lock
      USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND
            actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)
      WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND
                 actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)""")
    op.execute("""CREATE FUNCTION public.lock_reference_cost_owner() RETURNS boolean
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE v_tenant uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
              v_actor uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
      BEGIN
        IF v_tenant IS NULL OR v_actor IS NULL THEN RETURN false; END IF;
        PERFORM 1 FROM public.user_accounts WHERE id=v_actor AND active FOR SHARE;
        IF NOT FOUND THEN RETURN false; END IF;
        PERFORM 1 FROM public.memberships
          WHERE tenant_id=v_tenant AND actor_id=v_actor AND role='owner' AND active FOR SHARE;
        RETURN FOUND;
      END $$""")
    op.execute("ALTER FUNCTION public.lock_reference_cost_owner() OWNER TO meu_braco_direito_reference_lock")
    op.execute("REVOKE ALL ON FUNCTION public.lock_reference_cost_owner() FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION public.lock_reference_cost_owner() TO meu_braco_direito_correlator")
    op.execute("""CREATE TABLE reference_cost_reservations (
      id uuid PRIMARY KEY, tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id), discovery_id uuid NOT NULL
        REFERENCES reference_discoveries(id), effect_id uuid NOT NULL,
      request_hash char(64) NOT NULL,
      provider text NOT NULL CHECK(provider IN ('google','apify','jev')),
      month date NOT NULL CHECK(month = date_trunc('month',month::timestamp)::date),
      reserved_usd_micros bigint NOT NULL CHECK(reserved_usd_micros > 0),
      actual_usd_micros bigint CHECK(actual_usd_micros >= 0),
      state text NOT NULL CHECK(state IN ('claimed','uncertain','completed')),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      UNIQUE(tenant_id,effect_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id),
      CHECK((state='completed' AND actual_usd_micros IS NOT NULL) OR
            (state IN ('claimed','uncertain') AND actual_usd_micros IS NULL)))""")
    op.execute("CREATE INDEX reference_cost_search ON reference_cost_reservations(tenant_id,discovery_id)")
    op.execute("ALTER TABLE reference_cost_reservations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reference_cost_reservations FORCE ROW LEVEL SECURITY")
    op.execute("""CREATE POLICY worker_reference_cost ON reference_cost_reservations
      TO meu_braco_direito_correlator
      USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)
      WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)""")
    op.execute("""GRANT SELECT,INSERT,UPDATE(state,actual_usd_micros,updated_at)
      ON reference_cost_reservations TO meu_braco_direito_correlator""")
    # Aggregate-only operational counters, never tenant or business details.
    op.execute("""CREATE TABLE reference_cost_monthly (
      month date NOT NULL CHECK(month = date_trunc('month',month::timestamp)::date),
      provider text NOT NULL CHECK(provider IN ('all','google','apify','jev')),
      committed_usd_micros bigint NOT NULL DEFAULT 0 CHECK(committed_usd_micros >= 0),
      outstanding_usd_micros bigint NOT NULL DEFAULT 0 CHECK(outstanding_usd_micros >= 0),
      PRIMARY KEY(month,provider))""")
    op.execute("""GRANT SELECT,INSERT,UPDATE(committed_usd_micros,outstanding_usd_micros)
      ON reference_cost_monthly TO meu_braco_direito_correlator""")


def downgrade():
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM reference_cost_reservations) THEN
        RAISE EXCEPTION 'REFERENCE_COST_LEDGER_PREVENTS_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("DROP TABLE reference_cost_monthly")
    op.execute("DROP TABLE reference_cost_reservations")
    op.execute("DROP FUNCTION public.lock_reference_cost_owner()")
    op.execute("DROP POLICY reference_lock_membership ON memberships")
    op.execute("DROP POLICY reference_lock_account ON user_accounts")
    op.execute(
        "REVOKE SELECT(tenant_id,actor_id,role,active),UPDATE(active) ON memberships "
        "FROM meu_braco_direito_reference_lock"
    )
    op.execute("REVOKE SELECT(id,active),UPDATE(active) ON user_accounts FROM meu_braco_direito_reference_lock")
    op.execute("REVOKE USAGE ON SCHEMA public FROM meu_braco_direito_reference_lock")
