"""Shared, explicit cost policy and restricted accounting entry points."""

from alembic import op

revision = "0071_reference_cost_policy"
down_revision = "0070_reference_cost_guard"
branch_labels = None
depends_on = None


def upgrade():
    # Old claims did not record a policy version or guaranteed common timezone;
    # never assign them a fabricated policy during migration.
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM reference_cost_reservations) OR
         EXISTS(SELECT 1 FROM reference_cost_monthly) THEN
        RAISE EXCEPTION 'REFERENCE_COST_HISTORY_REQUIRES_EXPLICIT_MIGRATION';
      END IF;
    END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("""DO $$ BEGIN
      IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_reference_ledger') THEN
        CREATE ROLE meu_braco_direito_reference_ledger NOLOGIN NOSUPERUSER NOBYPASSRLS
          NOCREATEDB NOCREATEROLE NOREPLICATION;
      END IF;
      IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_reference_ledger'
        AND (rolcanlogin OR rolsuper OR rolbypassrls OR rolcreatedb OR rolcreaterole OR rolreplication)) OR
        EXISTS(SELECT 1 FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid OR r.oid=m.member
          WHERE r.rolname='meu_braco_direito_reference_ledger') THEN
        RAISE EXCEPTION 'UNSAFE_REFERENCE_LEDGER_ROLE';
      END IF;
    END $$""")
    op.execute("GRANT USAGE ON SCHEMA public TO meu_braco_direito_reference_ledger")
    op.execute("""CREATE TABLE reference_cost_policies (
      id uuid PRIMARY KEY, timezone text NOT NULL,
      per_search bigint NOT NULL CHECK(per_search BETWEEN 1 AND 1000000000000),
      monthly_total bigint NOT NULL CHECK(monthly_total BETWEEN 1 AND 1000000000000),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp())""")
    op.execute("""ALTER TABLE reference_cost_reservations ADD COLUMN policy_id uuid NOT NULL
      REFERENCES reference_cost_policies(id)""")
    op.execute("""CREATE TABLE reference_cost_policy_providers (
      policy_id uuid NOT NULL REFERENCES reference_cost_policies(id),
      provider text NOT NULL CHECK(provider IN ('google','apify','jev')),
      per_search bigint NOT NULL CHECK(per_search BETWEEN 1 AND 1000000000000),
      monthly_total bigint NOT NULL CHECK(monthly_total BETWEEN 1 AND 1000000000000),
      PRIMARY KEY(policy_id,provider))""")
    op.execute("""CREATE TABLE reference_cost_policy_head (
      singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton),
      policy_id uuid REFERENCES reference_cost_policies(id),last_timezone text)""")
    op.execute("""CREATE TABLE reference_cost_policy_activations (
      policy_id uuid PRIMARY KEY REFERENCES reference_cost_policies(id),
      first_activated_at timestamptz NOT NULL DEFAULT clock_timestamp())""")
    # A deliberately empty head means there is no active policy or budget.
    op.execute("INSERT INTO reference_cost_policy_head(singleton,policy_id) VALUES(true,NULL)")
    op.execute("""GRANT SELECT ON reference_cost_policies,reference_cost_policy_providers,
      reference_cost_policy_head TO meu_braco_direito_reference_ledger""")
    op.execute("GRANT SELECT,INSERT ON reference_cost_policy_activations TO meu_braco_direito_reference_ledger")
    op.execute("""REVOKE INSERT,UPDATE(state,actual_usd_micros,updated_at) ON reference_cost_reservations
      FROM meu_braco_direito_correlator""")
    op.execute("""REVOKE SELECT,INSERT,UPDATE(committed_usd_micros,outstanding_usd_micros)
      ON reference_cost_monthly FROM meu_braco_direito_correlator""")
    op.execute("""GRANT SELECT,INSERT,UPDATE(state,actual_usd_micros,updated_at)
      ON reference_cost_reservations TO meu_braco_direito_reference_ledger""")
    op.execute("""GRANT SELECT,INSERT,UPDATE(committed_usd_micros,outstanding_usd_micros)
      ON reference_cost_monthly TO meu_braco_direito_reference_ledger""")
    op.execute("""CREATE POLICY reference_ledger_tenant ON reference_cost_reservations
      TO meu_braco_direito_reference_ledger
      USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND
            actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)
      WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND
                 actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)""")
    # An aggregate-only history probe is used solely by the policy-head trigger.
    op.execute("""CREATE FUNCTION public.reference_cost_has_history() RETURNS boolean
      LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      SELECT EXISTS(SELECT 1 FROM public.reference_cost_monthly) $$""")
    op.execute("ALTER FUNCTION public.reference_cost_has_history() OWNER TO meu_braco_direito_reference_ledger")
    op.execute("REVOKE ALL ON FUNCTION public.reference_cost_has_history() FROM PUBLIC")
    op.execute("""CREATE FUNCTION public.reference_cost_policy_switch() RETURNS trigger
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE old_zone text; new_zone text;
      BEGIN
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        old_zone := OLD.last_timezone;
        SELECT timezone INTO new_zone FROM public.reference_cost_policies WHERE id=NEW.policy_id;
        IF NEW.policy_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM pg_timezone_names WHERE name=new_zone) THEN
          RAISE EXCEPTION 'REFERENCE_INVALID_TIMEZONE';
        END IF;
        IF new_zone IS NOT NULL AND new_zone<>'UTC' THEN
          RAISE EXCEPTION 'REFERENCE_TIMEZONE_NOT_SUPPORTED';
        END IF;
        IF old_zone IS NOT NULL AND new_zone IS NOT NULL AND old_zone<>new_zone
           AND public.reference_cost_has_history() THEN
          RAISE EXCEPTION 'REFERENCE_TIMEZONE_RECONCILIATION_REQUIRED';
        END IF;
        IF NEW.policy_id IS NOT NULL THEN
          INSERT INTO public.reference_cost_policy_activations(policy_id) VALUES(NEW.policy_id)
            ON CONFLICT DO NOTHING;
        END IF;
        NEW.last_timezone := coalesce(new_zone,OLD.last_timezone);
        RETURN NEW;
      END $$""")
    op.execute("ALTER FUNCTION public.reference_cost_policy_switch() OWNER TO meu_braco_direito_reference_ledger")
    op.execute("REVOKE ALL ON FUNCTION public.reference_cost_policy_switch() FROM PUBLIC")
    op.execute("""CREATE TRIGGER reference_cost_policy_head_switch BEFORE UPDATE ON reference_cost_policy_head
      FOR EACH ROW EXECUTE FUNCTION public.reference_cost_policy_switch()""")
    op.execute("""CREATE FUNCTION public.reference_cost_policy_immutable() RETURNS trigger
      LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
      BEGIN RAISE EXCEPTION 'REFERENCE_POLICY_IMMUTABLE'; END $$""")
    for table in ("reference_cost_policies", "reference_cost_policy_providers"):
        op.execute(f"""CREATE TRIGGER reference_cost_immutable BEFORE UPDATE OR DELETE ON {table}
          FOR EACH ROW EXECUTE FUNCTION public.reference_cost_policy_immutable()""")
    op.execute("""CREATE FUNCTION public.reference_cost_provider_before_insert() RETURNS trigger
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      BEGIN
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        IF EXISTS(SELECT 1 FROM public.reference_cost_policy_activations WHERE policy_id=NEW.policy_id) THEN
          RAISE EXCEPTION 'REFERENCE_POLICY_IMMUTABLE';
        END IF;
        RETURN NEW;
      END $$""")
    op.execute(
        "ALTER FUNCTION public.reference_cost_provider_before_insert() OWNER TO meu_braco_direito_reference_ledger"
    )
    op.execute("REVOKE ALL ON FUNCTION public.reference_cost_provider_before_insert() FROM PUBLIC")
    op.execute("""CREATE TRIGGER reference_cost_provider_insert BEFORE INSERT ON reference_cost_policy_providers
      FOR EACH ROW EXECUTE FUNCTION public.reference_cost_provider_before_insert()""")
    op.execute("""CREATE TRIGGER reference_cost_head_no_delete BEFORE DELETE ON reference_cost_policy_head
      FOR EACH ROW EXECUTE FUNCTION public.reference_cost_policy_immutable()""")
    op.execute("""GRANT SELECT,UPDATE(state) ON reference_discoveries TO meu_braco_direito_reference_ledger""")
    op.execute("""CREATE POLICY reference_ledger_discovery ON reference_discoveries
      TO meu_braco_direito_reference_ledger
      USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND
            actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)
      WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND
                 actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)""")
    op.execute("GRANT SELECT(id,tenant_id,event_type,payload) ON outbox_events TO meu_braco_direito_reference_ledger")
    op.execute("""CREATE POLICY reference_ledger_outbox ON outbox_events FOR SELECT
      TO meu_braco_direito_reference_ledger USING(
        tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND
        event_type='reference.search_requested' AND
        payload->>'actor_id'=nullif(current_setting('app.actor_id',true),''))""")
    op.execute("GRANT INSERT ON audit_events TO meu_braco_direito_reference_ledger")
    op.execute("""CREATE POLICY reference_ledger_audit ON audit_events FOR INSERT
      TO meu_braco_direito_reference_ledger WITH CHECK(
        tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND
        actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)""")
    op.execute("GRANT EXECUTE ON FUNCTION public.lock_reference_cost_owner() TO meu_braco_direito_reference_ledger")

    op.execute("""CREATE FUNCTION public.reference_cost_claim(
      p_business uuid,p_discovery uuid,p_effect uuid,p_provider text,p_hash text,p_amount bigint)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        r public.reference_cost_reservations%ROWTYPE; pol public.reference_cost_policies%ROWTYPE;
        provider_pol public.reference_cost_policy_providers%ROWTYPE;
        current_month date; search_total numeric; provider_total numeric; used numeric; result jsonb;
        discovery_state text; fixture_intent boolean := false;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_discovery IS NULL OR p_effect IS NULL
          OR p_provider NOT IN ('google','apify','jev') OR p_provider IS NULL
          OR p_hash IS NULL OR p_hash !~ '^[0-9a-f]{64}$'
          OR p_amount IS NULL OR p_amount<1 OR p_amount>1000000000000 THEN
          RAISE EXCEPTION 'INVALID_CLAIM';
        END IF;
        SELECT * INTO r FROM public.reference_cost_reservations WHERE tenant_id=t AND effect_id=p_effect;
        IF FOUND THEN
          IF r.request_hash<>p_hash OR r.business_id<>p_business OR r.discovery_id<>p_discovery
             OR r.provider<>p_provider OR r.reserved_usd_micros<>p_amount THEN
            RAISE EXCEPTION 'REFERENCE_EFFECT_CONFLICT'; END IF;
          RETURN jsonb_build_object('id',r.id,'state',r.state,'created',false,
            'reserved_usd_micros',r.reserved_usd_micros,'actual_usd_micros',r.actual_usd_micros);
        END IF;
        IF NOT public.lock_reference_cost_owner() THEN
          -- An earlier attempt may have committed while this one waited for
          -- identity locks; replay it, but never admit a new effect.
          SELECT * INTO r FROM public.reference_cost_reservations WHERE tenant_id=t AND effect_id=p_effect;
          IF FOUND THEN
            IF r.request_hash<>p_hash OR r.business_id<>p_business OR r.discovery_id<>p_discovery
              OR r.provider<>p_provider OR r.reserved_usd_micros<>p_amount THEN
              RAISE EXCEPTION 'REFERENCE_EFFECT_CONFLICT'; END IF;
            RETURN jsonb_build_object('id',r.id,'state',r.state,'created',false,
              'reserved_usd_micros',r.reserved_usd_micros,'actual_usd_micros',r.actual_usd_micros);
          END IF;
          RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE';
        END IF;
        SELECT d.state INTO discovery_state FROM public.reference_discoveries d JOIN public.outbox_events e
          ON e.tenant_id=d.tenant_id AND e.event_type='reference.search_requested'
          AND e.payload->>'actor_id'=d.actor_id::text AND e.payload->>'business_id'=d.business_id::text
          AND e.payload->>'operation_id'=d.operation_id::text
          WHERE d.id=p_discovery AND d.tenant_id=t AND d.business_id=p_business AND d.actor_id=a
            AND d.state IN ('pending','simulated') FOR SHARE OF d;
        IF NOT FOUND THEN
          SELECT * INTO r FROM public.reference_cost_reservations WHERE tenant_id=t AND effect_id=p_effect;
          IF FOUND THEN
            IF r.request_hash<>p_hash OR r.business_id<>p_business OR r.discovery_id<>p_discovery
             OR r.provider<>p_provider OR r.reserved_usd_micros<>p_amount THEN
            RAISE EXCEPTION 'REFERENCE_EFFECT_CONFLICT'; END IF;
            RETURN jsonb_build_object('id',r.id,'state',r.state,'created',false,
              'reserved_usd_micros',r.reserved_usd_micros,'actual_usd_micros',r.actual_usd_micros);
          END IF;
          RAISE EXCEPTION 'REFERENCE_DISCOVERY_NOT_PENDING';
        END IF;
        IF discovery_state='simulated' THEN
          -- Only the future fixture table can authorize a completed fake discovery.
          -- The dynamic query also keeps revision 0071 usable before 0072 exists.
          IF to_regclass('public.reference_simulated_effects') IS NOT NULL THEN
            EXECUTE 'SELECT EXISTS(SELECT 1 FROM public.reference_simulated_effects WHERE '
              || 'id=$1 AND tenant_id=$2 AND actor_id=$3 AND business_id=$4 AND discovery_id=$5 '
              || 'AND provider=$6 AND reserved_usd_micros=$7)'
              INTO fixture_intent USING p_effect,t,a,p_business,p_discovery,p_provider,p_amount;
          END IF;
          IF NOT fixture_intent THEN RAISE EXCEPTION 'REFERENCE_DISCOVERY_NOT_PENDING'; END IF;
        END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO r FROM public.reference_cost_reservations WHERE tenant_id=t AND effect_id=p_effect;
        IF FOUND THEN
          IF r.request_hash<>p_hash OR r.business_id<>p_business OR r.discovery_id<>p_discovery
             OR r.provider<>p_provider OR r.reserved_usd_micros<>p_amount THEN
            RAISE EXCEPTION 'REFERENCE_EFFECT_CONFLICT'; END IF;
          RETURN jsonb_build_object('id',r.id,'state',r.state,'created',false,
            'reserved_usd_micros',r.reserved_usd_micros,'actual_usd_micros',r.actual_usd_micros);
        END IF;
        SELECT p.* INTO pol FROM public.reference_cost_policy_head h
          JOIN public.reference_cost_policies p ON p.id=h.policy_id WHERE h.singleton;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_BUDGET_DISABLED'; END IF;
        SELECT * INTO provider_pol FROM public.reference_cost_policy_providers
          WHERE policy_id=pol.id AND provider=p_provider;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_BUDGET_DISABLED'; END IF;
        SELECT coalesce(sum(CASE WHEN state='completed' THEN actual_usd_micros ELSE reserved_usd_micros END),0),
          coalesce(sum(CASE WHEN provider=p_provider THEN CASE WHEN state='completed' THEN actual_usd_micros
            ELSE reserved_usd_micros END ELSE 0 END),0) INTO search_total,provider_total
          FROM public.reference_cost_reservations WHERE tenant_id=t AND discovery_id=p_discovery;
        IF search_total+p_amount>pol.per_search THEN RAISE EXCEPTION 'REFERENCE_SEARCH_BUDGET_EXCEEDED'; END IF;
        IF provider_total+p_amount>provider_pol.per_search THEN
          RAISE EXCEPTION 'REFERENCE_SEARCH_PROVIDER_BUDGET_EXCEEDED'; END IF;
        current_month := date_trunc('month',clock_timestamp() AT TIME ZONE pol.timezone)::date;
        SELECT coalesce(sum(CASE WHEN month=current_month THEN committed_usd_micros
          ELSE outstanding_usd_micros END),0) INTO used FROM public.reference_cost_monthly
          WHERE provider='all';
        IF used+p_amount>pol.monthly_total THEN RAISE EXCEPTION 'REFERENCE_MONTHLY_BUDGET_EXCEEDED'; END IF;
        SELECT coalesce(sum(CASE WHEN month=current_month THEN committed_usd_micros
          ELSE outstanding_usd_micros END),0) INTO used FROM public.reference_cost_monthly
          WHERE provider=p_provider;
        IF used+p_amount>provider_pol.monthly_total THEN
          RAISE EXCEPTION 'REFERENCE_MONTHLY_PROVIDER_BUDGET_EXCEEDED'; END IF;
        INSERT INTO public.reference_cost_monthly(month,provider,committed_usd_micros,outstanding_usd_micros)
          VALUES(current_month,'all',p_amount,p_amount),(current_month,p_provider,p_amount,p_amount)
          ON CONFLICT(month,provider) DO UPDATE SET
            committed_usd_micros=reference_cost_monthly.committed_usd_micros+excluded.committed_usd_micros,
            outstanding_usd_micros=reference_cost_monthly.outstanding_usd_micros+excluded.outstanding_usd_micros;
        INSERT INTO public.reference_cost_reservations(id,tenant_id,business_id,actor_id,discovery_id,effect_id,
          request_hash,provider,month,reserved_usd_micros,state,policy_id)
          VALUES(gen_random_uuid(),t,p_business,a,p_discovery,p_effect,p_hash,p_provider,current_month,p_amount,
            'claimed',pol.id)
          RETURNING * INTO r;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_effect,'reference.cost_claimed',r.id);
        result := jsonb_build_object('id',r.id,'state',r.state,'created',true,
          'reserved_usd_micros',r.reserved_usd_micros,'actual_usd_micros',r.actual_usd_micros);
        RETURN result;
      END $$""")
    op.execute("""CREATE FUNCTION public.reference_cost_finish(p_id uuid,p_actual bigint) RETURNS jsonb
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        r public.reference_cost_reservations%ROWTYPE;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_id IS NULL OR p_actual<0 OR p_actual>1000000000000 THEN
          RAISE EXCEPTION 'INVALID_ACTUAL_COST'; END IF;
        -- A worker-supplied amount is not evidence of billed or avoided cost.
        -- No verified external receipt/settlement consumer exists yet.
        IF p_actual IS NOT NULL THEN RAISE EXCEPTION 'REFERENCE_EVIDENCE_REQUIRED'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO r FROM public.reference_cost_reservations WHERE tenant_id=t AND id=p_id;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_RESERVATION_NOT_FOUND'; END IF;
        IF r.state='completed' THEN
          RAISE EXCEPTION 'REFERENCE_OUTCOME_CONFLICT';
        ELSIF r.state='claimed' THEN
            UPDATE public.reference_cost_reservations SET state='uncertain',
              updated_at=clock_timestamp() WHERE id=p_id AND tenant_id=t RETURNING * INTO r;
            INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(t,a,r.effect_id,'reference.cost_uncertain',r.id);
        END IF;
        RETURN jsonb_build_object('id',r.id,'state',r.state,'created',false,
          'reserved_usd_micros',r.reserved_usd_micros,'actual_usd_micros',r.actual_usd_micros);
      END $$""")
    for function in (
        "reference_cost_claim(uuid,uuid,uuid,text,text,bigint)",
        "reference_cost_finish(uuid,bigint)",
    ):
        op.execute(f"ALTER FUNCTION public.{function} OWNER TO meu_braco_direito_reference_ledger")
        op.execute(f"REVOKE ALL ON FUNCTION public.{function} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION public.{function} TO meu_braco_direito_correlator")


def downgrade():
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM reference_cost_reservations) OR
         EXISTS(SELECT 1 FROM reference_cost_policies) THEN
        RAISE EXCEPTION 'REFERENCE_POLICY_PREVENTS_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("DROP FUNCTION public.reference_cost_finish(uuid,bigint)")
    op.execute("DROP FUNCTION public.reference_cost_claim(uuid,uuid,uuid,text,text,bigint)")
    op.execute("DROP TRIGGER reference_cost_policy_head_switch ON reference_cost_policy_head")
    op.execute("DROP TRIGGER reference_cost_head_no_delete ON reference_cost_policy_head")
    op.execute("DROP TRIGGER reference_cost_provider_insert ON reference_cost_policy_providers")
    op.execute("DROP FUNCTION public.reference_cost_provider_before_insert()")
    op.execute("DROP TRIGGER reference_cost_immutable ON reference_cost_policy_providers")
    op.execute("DROP TRIGGER reference_cost_immutable ON reference_cost_policies")
    op.execute("DROP FUNCTION public.reference_cost_policy_immutable()")
    op.execute("DROP FUNCTION public.reference_cost_policy_switch()")
    op.execute("DROP FUNCTION public.reference_cost_has_history()")
    op.execute("DROP POLICY reference_ledger_audit ON audit_events")
    op.execute("DROP POLICY reference_ledger_outbox ON outbox_events")
    op.execute("DROP POLICY reference_ledger_discovery ON reference_discoveries")
    op.execute("DROP POLICY reference_ledger_tenant ON reference_cost_reservations")
    op.execute("ALTER TABLE reference_cost_reservations DROP COLUMN policy_id")
    op.execute("""DROP TABLE reference_cost_policy_head,reference_cost_policy_activations,
      reference_cost_policy_providers,reference_cost_policies""")
    op.execute("REVOKE SELECT,UPDATE(state) ON reference_discoveries FROM meu_braco_direito_reference_ledger")
    op.execute(
        "REVOKE SELECT(id,tenant_id,event_type,payload) ON outbox_events FROM meu_braco_direito_reference_ledger"
    )
    op.execute("REVOKE INSERT ON audit_events FROM meu_braco_direito_reference_ledger")
    op.execute("REVOKE EXECUTE ON FUNCTION public.lock_reference_cost_owner() FROM meu_braco_direito_reference_ledger")
    op.execute(
        "REVOKE SELECT,INSERT,UPDATE(state,actual_usd_micros,updated_at) ON reference_cost_reservations "
        "FROM meu_braco_direito_reference_ledger"
    )
    op.execute(
        "REVOKE SELECT,INSERT,UPDATE(committed_usd_micros,outstanding_usd_micros) ON reference_cost_monthly "
        "FROM meu_braco_direito_reference_ledger"
    )
    op.execute("REVOKE USAGE ON SCHEMA public FROM meu_braco_direito_reference_ledger")
    op.execute(
        "GRANT SELECT,INSERT,UPDATE(state,actual_usd_micros,updated_at) ON reference_cost_reservations "
        "TO meu_braco_direito_correlator"
    )
    op.execute(
        "GRANT SELECT,INSERT,UPDATE(committed_usd_micros,outstanding_usd_micros) ON reference_cost_monthly "
        "TO meu_braco_direito_correlator"
    )
