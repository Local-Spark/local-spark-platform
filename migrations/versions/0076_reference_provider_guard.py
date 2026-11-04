"""Durable, opt-in provider claims sharing the existing cost ledger.

No runtime actor can create a pilot or provider intent in this slice. A future
writer must authenticate its intent and emit its outbox event transactionally.
"""

from alembic import op

revision = "0076_reference_provider_guard"
down_revision = "0075_reference_results_storage"
branch_labels = None
depends_on = None


def _replace_legacy_finish(*, protect_provider: bool):
    provider_check = (
        "IF r.provider_search_id IS NOT NULL THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_FENCE_REQUIRED'; END IF;"
        if protect_provider
        else ""
    )
    op.execute(f"""CREATE OR REPLACE FUNCTION public.reference_cost_finish(p_id uuid,p_actual bigint) RETURNS jsonb
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        r public.reference_cost_reservations%ROWTYPE;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_id IS NULL OR p_actual<0 OR p_actual>1000000000000 THEN
          RAISE EXCEPTION 'INVALID_ACTUAL_COST'; END IF;
        IF p_actual IS NOT NULL THEN RAISE EXCEPTION 'REFERENCE_EVIDENCE_REQUIRED'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO r FROM public.reference_cost_reservations WHERE tenant_id=t AND id=p_id;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_RESERVATION_NOT_FOUND'; END IF;
        {provider_check}
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


def upgrade():
    op.execute("""CREATE TABLE reference_provider_tariffs (
      version text PRIMARY KEY CHECK(version ~ '^[a-zA-Z0-9_.-]{1,64}$'),
      provider text NOT NULL CHECK(provider='google'),
      field_mask text NOT NULL CHECK(length(field_mask) BETWEEN 1 AND 4096),
      minimum_reserved_usd_micros bigint NOT NULL CHECK(minimum_reserved_usd_micros BETWEEN 1 AND 5000000),
      active boolean NOT NULL DEFAULT false)""")
    op.execute("""CREATE FUNCTION public.reference_provider_tariff_immutable() RETURNS trigger
      LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
      BEGIN
        IF TG_OP='DELETE' OR NEW.version<>OLD.version OR NEW.provider<>OLD.provider
          OR NEW.field_mask<>OLD.field_mask OR NEW.minimum_reserved_usd_micros<>OLD.minimum_reserved_usd_micros THEN
          RAISE EXCEPTION 'REFERENCE_PROVIDER_TARIFF_IMMUTABLE'; END IF;
        RETURN NEW;
      END $$""")
    op.execute("""CREATE TRIGGER reference_provider_tariff_immutable BEFORE UPDATE OR DELETE
      ON reference_provider_tariffs FOR EACH ROW EXECUTE FUNCTION public.reference_provider_tariff_immutable()""")
    op.execute("""CREATE TABLE reference_provider_pilots (
      singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton), id uuid NOT NULL UNIQUE,
      cap_usd_micros bigint NOT NULL CHECK(cap_usd_micros BETWEEN 1 AND 5000000),
      reserved_usd_micros bigint NOT NULL DEFAULT 0 CHECK(reserved_usd_micros BETWEEN 0 AND cap_usd_micros),
      active boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT clock_timestamp())""")
    op.execute("""CREATE TABLE reference_provider_effects (
      id uuid NOT NULL, tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id), search_id uuid NOT NULL,
      pilot_id uuid NOT NULL REFERENCES reference_provider_pilots(id),
      provider text NOT NULL CHECK(provider='google'),
      request_mac char(64) NOT NULL CHECK(request_mac ~ '^[0-9a-f]{64}$'),
      key_version text NOT NULL CHECK(key_version ~ '^[a-zA-Z0-9_.-]{1,64}$'),
      tariff_version text NOT NULL REFERENCES reference_provider_tariffs(version),
      credential_version text NOT NULL CHECK(credential_version ~ '^[a-zA-Z0-9_.-]{1,64}$'),
      field_mask text NOT NULL CHECK(length(field_mask) BETWEEN 1 AND 4096),
      reserved_usd_micros bigint NOT NULL CHECK(reserved_usd_micros BETWEEN 1 AND 5000000),
      state text NOT NULL CHECK(state IN ('pending','running','uncertain')),
      executor_token uuid, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(tenant_id,business_id,id), UNIQUE(tenant_id,id),
      FOREIGN KEY(tenant_id,business_id,search_id)
        REFERENCES reference_provider_searches(tenant_id,business_id,id),
      CHECK((state='pending' AND executor_token IS NULL) OR
            (state IN ('running','uncertain') AND executor_token IS NOT NULL)))""")
    op.execute("ALTER TABLE reference_provider_effects ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reference_provider_effects FORCE ROW LEVEL SECURITY")
    own = (
        "tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND "
        "actor_id=nullif(current_setting('app.actor_id',true),'')::uuid"
    )
    op.execute(f"""CREATE POLICY reference_provider_ledger ON reference_provider_effects
      TO meu_braco_direito_reference_ledger USING({own}) WITH CHECK({own})""")
    op.execute("""GRANT SELECT,UPDATE(state,executor_token,updated_at) ON reference_provider_effects
      TO meu_braco_direito_reference_ledger""")
    op.execute(
        "GRANT SELECT,UPDATE(reserved_usd_micros) ON reference_provider_pilots TO meu_braco_direito_reference_ledger"
    )
    op.execute("GRANT SELECT,UPDATE(active) ON reference_provider_tariffs TO meu_braco_direito_reference_ledger")
    op.execute(f"""CREATE POLICY reference_provider_search_ledger ON reference_provider_searches
      TO meu_braco_direito_reference_ledger USING({own}) WITH CHECK({own})""")
    op.execute("GRANT SELECT,UPDATE(state) ON reference_provider_searches TO meu_braco_direito_reference_ledger")
    op.execute("ALTER TABLE reference_cost_reservations ALTER COLUMN discovery_id DROP NOT NULL")
    op.execute("""ALTER TABLE reference_cost_reservations ADD COLUMN provider_search_id uuid,
      ADD COLUMN pilot_id uuid REFERENCES reference_provider_pilots(id),
      ADD CONSTRAINT reference_cost_one_search CHECK (
        (discovery_id IS NOT NULL AND provider_search_id IS NULL AND pilot_id IS NULL) OR
        (discovery_id IS NULL AND provider_search_id IS NOT NULL AND pilot_id IS NOT NULL)),
      ADD FOREIGN KEY(tenant_id,business_id,provider_search_id)
        REFERENCES reference_provider_searches(tenant_id,business_id,id)""")
    _replace_legacy_finish(protect_provider=True)
    op.execute("""ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check""")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed',
       'reference.provider_effect_requested','reference.provider_cost_changed'))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    op.execute(f"""CREATE POLICY reference_provider_event_ledger ON outbox_events FOR SELECT
      TO meu_braco_direito_reference_ledger USING(tenant_id={tenant}
      AND event_type='reference.provider_effect_requested' AND payload->>'actor_id'={actor}::text)""")
    op.execute(f"""CREATE POLICY reference_provider_cost_emit ON outbox_events FOR INSERT
      TO meu_braco_direito_reference_ledger WITH CHECK(tenant_id={tenant}
      AND event_type='reference.provider_cost_changed' AND payload->>'actor_id'={actor}::text)""")
    op.execute("""CREATE FUNCTION public.reference_provider_claim(
      p_effect uuid,p_event uuid,p_mac text,p_business uuid,p_search uuid,p_pilot uuid,
      p_amount bigint,p_key text,p_tariff text,p_credential text,p_mask text)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        e public.reference_provider_effects%ROWTYPE; p public.reference_provider_pilots%ROWTYPE;
        tariff public.reference_provider_tariffs%ROWTYPE;
        pol public.reference_cost_policies%ROWTYPE; pp public.reference_cost_policy_providers%ROWTYPE;
        r public.reference_cost_reservations%ROWTYPE; cm date; search_used numeric; provider_used numeric;
        monthly_used numeric; token uuid;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_effect IS NULL OR p_event IS NULL OR p_mac IS NULL
          OR p_mac !~ '^[0-9a-f]{64}$' THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_INVALID'; END IF;
        SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND actor_id=a AND id=p_effect;
        IF NOT FOUND OR e.request_mac IS DISTINCT FROM p_mac OR e.business_id IS DISTINCT FROM p_business
          OR e.search_id IS DISTINCT FROM p_search OR e.pilot_id IS DISTINCT FROM p_pilot
          OR e.reserved_usd_micros IS DISTINCT FROM p_amount OR e.key_version IS DISTINCT FROM p_key
          OR e.tariff_version IS DISTINCT FROM p_tariff OR e.credential_version IS DISTINCT FROM p_credential
          OR e.field_mask IS DISTINCT FROM p_mask THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_INTENT_INVALID'; END IF;
        IF NOT EXISTS(SELECT 1 FROM public.outbox_events o WHERE o.id=p_event AND o.tenant_id=t
          AND o.event_type='reference.provider_effect_requested' AND o.payload=jsonb_build_object(
            'business_id',e.business_id::text,'actor_id',a::text,'operation_id',e.id::text)) THEN
          RAISE EXCEPTION 'REFERENCE_PROVIDER_EVENT_INVALID'; END IF;
        IF e.state<>'pending' THEN RETURN jsonb_build_object('created',false,'state',e.state); END IF;
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO e FROM public.reference_provider_effects
          WHERE tenant_id=t AND actor_id=a AND id=p_effect FOR UPDATE;
        IF e.request_mac IS DISTINCT FROM p_mac OR e.business_id IS DISTINCT FROM p_business
          OR e.search_id IS DISTINCT FROM p_search OR e.pilot_id IS DISTINCT FROM p_pilot
          OR e.reserved_usd_micros IS DISTINCT FROM p_amount OR e.key_version IS DISTINCT FROM p_key
          OR e.tariff_version IS DISTINCT FROM p_tariff OR e.credential_version IS DISTINCT FROM p_credential
          OR e.field_mask IS DISTINCT FROM p_mask THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_INTENT_INVALID'; END IF;
        IF e.state<>'pending' THEN RETURN jsonb_build_object('created',false,'state',e.state); END IF;
        IF NOT EXISTS(SELECT 1 FROM public.outbox_events o WHERE o.id=p_event AND o.tenant_id=t
          AND o.event_type='reference.provider_effect_requested' AND o.payload=jsonb_build_object(
            'business_id',e.business_id::text,'actor_id',a::text,'operation_id',e.id::text)) THEN
          RAISE EXCEPTION 'REFERENCE_PROVIDER_EVENT_INVALID'; END IF;
        PERFORM 1 FROM public.reference_provider_searches s WHERE s.tenant_id=t AND s.business_id=e.business_id
          AND s.id=e.search_id AND s.actor_id=a AND s.state='pending' FOR SHARE;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_SEARCH_INACTIVE'; END IF;
        SELECT * INTO tariff FROM public.reference_provider_tariffs WHERE version=e.tariff_version FOR SHARE;
        IF NOT FOUND OR NOT tariff.active OR tariff.provider<>e.provider OR tariff.field_mask<>e.field_mask
          OR e.reserved_usd_micros<tariff.minimum_reserved_usd_micros THEN
          RAISE EXCEPTION 'REFERENCE_PROVIDER_TARIFF_INVALID'; END IF;
        SELECT * INTO p FROM public.reference_provider_pilots WHERE id=e.pilot_id FOR UPDATE;
        IF NOT FOUND OR NOT p.active THEN RAISE EXCEPTION 'REFERENCE_PILOT_DISABLED'; END IF;
        IF p.reserved_usd_micros+e.reserved_usd_micros>p.cap_usd_micros THEN
          RAISE EXCEPTION 'REFERENCE_PILOT_BUDGET_EXCEEDED'; END IF;
        SELECT q.* INTO pol FROM public.reference_cost_policy_head h
          JOIN public.reference_cost_policies q ON q.id=h.policy_id WHERE h.singleton;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_BUDGET_DISABLED'; END IF;
        SELECT * INTO pp FROM public.reference_cost_policy_providers
          WHERE policy_id=pol.id AND provider=e.provider;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_BUDGET_DISABLED'; END IF;
        SELECT coalesce(sum(CASE WHEN state='completed' THEN actual_usd_micros ELSE reserved_usd_micros END),0),
          coalesce(sum(CASE WHEN provider=e.provider THEN CASE WHEN state='completed' THEN actual_usd_micros
            ELSE reserved_usd_micros END ELSE 0 END),0) INTO search_used,provider_used
          FROM public.reference_cost_reservations WHERE tenant_id=t AND business_id=e.business_id
            AND provider_search_id=e.search_id;
        IF search_used+e.reserved_usd_micros>pol.per_search THEN
          RAISE EXCEPTION 'REFERENCE_SEARCH_BUDGET_EXCEEDED'; END IF;
        IF provider_used+e.reserved_usd_micros>pp.per_search THEN
          RAISE EXCEPTION 'REFERENCE_SEARCH_PROVIDER_BUDGET_EXCEEDED'; END IF;
        cm := date_trunc('month',clock_timestamp() AT TIME ZONE pol.timezone)::date;
        SELECT coalesce(sum(CASE WHEN month=cm THEN committed_usd_micros ELSE outstanding_usd_micros END),0)
          INTO monthly_used FROM public.reference_cost_monthly WHERE provider='all';
        IF monthly_used+e.reserved_usd_micros>pol.monthly_total THEN
          RAISE EXCEPTION 'REFERENCE_MONTHLY_BUDGET_EXCEEDED'; END IF;
        SELECT coalesce(sum(CASE WHEN month=cm THEN committed_usd_micros ELSE outstanding_usd_micros END),0)
          INTO monthly_used FROM public.reference_cost_monthly WHERE provider=e.provider;
        IF monthly_used+e.reserved_usd_micros>pp.monthly_total THEN
          RAISE EXCEPTION 'REFERENCE_MONTHLY_PROVIDER_BUDGET_EXCEEDED'; END IF;
        UPDATE public.reference_provider_pilots SET reserved_usd_micros=reserved_usd_micros+e.reserved_usd_micros
          WHERE id=e.pilot_id;
        INSERT INTO public.reference_cost_monthly(month,provider,committed_usd_micros,outstanding_usd_micros)
          VALUES(cm,'all',e.reserved_usd_micros,e.reserved_usd_micros),
                (cm,e.provider,e.reserved_usd_micros,e.reserved_usd_micros)
          ON CONFLICT(month,provider) DO UPDATE SET
            committed_usd_micros=reference_cost_monthly.committed_usd_micros+excluded.committed_usd_micros,
            outstanding_usd_micros=reference_cost_monthly.outstanding_usd_micros+excluded.outstanding_usd_micros;
        INSERT INTO public.reference_cost_reservations(id,tenant_id,business_id,actor_id,discovery_id,
          provider_search_id,pilot_id,effect_id,request_hash,provider,month,reserved_usd_micros,state,policy_id)
          VALUES(gen_random_uuid(),t,e.business_id,a,NULL,e.search_id,e.pilot_id,e.id,p_mac,e.provider,cm,
            e.reserved_usd_micros,'claimed',pol.id) RETURNING * INTO r;
        token := gen_random_uuid();
        UPDATE public.reference_provider_effects SET state='running',executor_token=token,updated_at=clock_timestamp()
          WHERE tenant_id=t AND business_id=e.business_id AND id=e.id;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,e.id,'reference.provider_cost_claimed',r.id);
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(gen_random_uuid(),t,'reference.provider_cost_changed',jsonb_build_object(
            'business_id',e.business_id::text,'actor_id',a::text,'operation_id',e.id::text));
        RETURN jsonb_build_object('created',true,'state','running','executor_token',token,'reservation_id',r.id);
      END $$""")
    op.execute(
        "ALTER FUNCTION public.reference_provider_claim(uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text) "
        "OWNER TO meu_braco_direito_reference_ledger"
    )
    op.execute("""REVOKE ALL ON FUNCTION
      public.reference_provider_claim(uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text) FROM PUBLIC""")
    op.execute(
        "GRANT EXECUTE ON FUNCTION "
        "public.reference_provider_claim(uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text) "
        "TO meu_braco_direito_correlator"
    )

    op.execute("""CREATE FUNCTION public.reference_provider_uncertain(p_effect uuid,p_token uuid)
      RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        e public.reference_provider_effects%ROWTYPE; r public.reference_cost_reservations%ROWTYPE;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_effect IS NULL OR p_token IS NULL THEN
          RAISE EXCEPTION 'REFERENCE_PROVIDER_INVALID'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO e FROM public.reference_provider_effects
          WHERE tenant_id=t AND actor_id=a AND id=p_effect FOR UPDATE;
        IF NOT FOUND OR e.executor_token IS DISTINCT FROM p_token OR e.state NOT IN ('running','uncertain') THEN
          RAISE EXCEPTION 'REFERENCE_PROVIDER_FENCE_INVALID'; END IF;
        IF e.state='uncertain' THEN RETURN e.state; END IF;
        SELECT * INTO r FROM public.reference_cost_reservations
          WHERE tenant_id=t AND actor_id=a AND effect_id=e.id FOR UPDATE;
        IF NOT FOUND OR r.state NOT IN ('claimed','uncertain') THEN
          RAISE EXCEPTION 'REFERENCE_RESERVATION_NOT_FOUND'; END IF;
        UPDATE public.reference_cost_reservations SET state='uncertain',updated_at=clock_timestamp()
          WHERE tenant_id=t AND id=r.id;
        UPDATE public.reference_provider_effects SET state='uncertain',updated_at=clock_timestamp()
          WHERE tenant_id=t AND business_id=e.business_id AND id=e.id;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,e.id,'reference.provider_cost_uncertain',r.id);
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(gen_random_uuid(),t,'reference.provider_cost_changed',jsonb_build_object(
            'business_id',e.business_id::text,'actor_id',a::text,'operation_id',e.id::text));
        RETURN 'uncertain';
      END $$""")
    op.execute(
        "ALTER FUNCTION public.reference_provider_uncertain(uuid,uuid) OWNER TO meu_braco_direito_reference_ledger"
    )
    op.execute("REVOKE ALL ON FUNCTION public.reference_provider_uncertain(uuid,uuid) FROM PUBLIC")
    op.execute(
        "GRANT EXECUTE ON FUNCTION public.reference_provider_uncertain(uuid,uuid) TO meu_braco_direito_correlator"
    )


def downgrade():
    op.execute(
        "LOCK TABLE reference_provider_effects,reference_provider_pilots,reference_provider_tariffs,"
        "reference_cost_reservations,"
        "outbox_events IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM reference_provider_effects) OR EXISTS(SELECT 1 FROM reference_provider_pilots)
        OR EXISTS(SELECT 1 FROM reference_provider_tariffs)
        OR EXISTS(SELECT 1 FROM reference_cost_reservations WHERE provider_search_id IS NOT NULL)
        OR EXISTS(SELECT 1 FROM outbox_events WHERE event_type IN
          ('reference.provider_effect_requested','reference.provider_cost_changed')) THEN
        RAISE EXCEPTION 'REFERENCE_PROVIDER_GUARD_PREVENTS_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("DROP FUNCTION public.reference_provider_uncertain(uuid,uuid)")
    op.execute(
        "DROP FUNCTION public.reference_provider_claim(uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text)"
    )
    op.execute("DROP POLICY reference_provider_cost_emit ON outbox_events")
    op.execute("DROP POLICY reference_provider_event_ledger ON outbox_events")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed'))""")
    op.execute("ALTER TABLE reference_cost_reservations DROP CONSTRAINT reference_cost_one_search")
    _replace_legacy_finish(protect_provider=False)
    op.execute("ALTER TABLE reference_cost_reservations DROP COLUMN provider_search_id,DROP COLUMN pilot_id")
    op.execute("ALTER TABLE reference_cost_reservations ALTER COLUMN discovery_id SET NOT NULL")
    op.execute("REVOKE SELECT,UPDATE(state) ON reference_provider_searches FROM meu_braco_direito_reference_ledger")
    op.execute("DROP POLICY reference_provider_search_ledger ON reference_provider_searches")
    op.execute("DROP TABLE reference_provider_effects")
    op.execute("DROP TABLE reference_provider_pilots")
    op.execute("DROP TABLE reference_provider_tariffs")
    op.execute("DROP FUNCTION public.reference_provider_tariff_immutable()")
