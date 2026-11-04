"""Inactive manual-origin geocoding effects using the common pilot ledger.

No runtime principal can create or claim these rows. Provider replies, derived
coordinates and formatted addresses are intentionally absent from this schema.
"""

from alembic import op

revision = "0090_reference_geocoding_ledger"
down_revision = "0089_reference_reco_guard"
branch_labels = None
depends_on = None

_CLAIM = "uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,bigint"


def upgrade():
    op.execute("""CREATE TABLE reference_geocode_origins (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),context_version bigint NOT NULL CHECK(context_version>0),
      PRIMARY KEY(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,context_version)
        REFERENCES business_context_versions(tenant_id,business_id,version))""")
    op.execute("""CREATE TABLE reference_geocode_effects (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),origin_id uuid NOT NULL,
      pilot_id uuid NOT NULL REFERENCES reference_provider_pilots(id),event_id uuid NOT NULL,
      request_mac char(64) NOT NULL CHECK(request_mac ~ '^[0-9a-f]{64}$'),
      key_version text NOT NULL CHECK(key_version ~ '^[a-zA-Z0-9_.-]{1,64}$'),
      tariff_version text NOT NULL,
      credential_version text NOT NULL CHECK(credential_version ~ '^[a-zA-Z0-9_.-]{1,64}$'),
      charge_class text NOT NULL CHECK(charge_class LIKE 'geocode-v4:results.%'),
      reserved_usd_micros bigint NOT NULL CHECK(reserved_usd_micros BETWEEN 1 AND 5000000),
      state text NOT NULL CHECK(state IN ('pending','running','uncertain')),executor_token uuid,
      PRIMARY KEY(tenant_id,business_id,id),UNIQUE(tenant_id,id),UNIQUE(tenant_id,business_id,origin_id),
      FOREIGN KEY(tenant_id,business_id,origin_id) REFERENCES reference_geocode_origins(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id),
      CHECK((state='pending' AND executor_token IS NULL) OR
        (state IN ('running','uncertain') AND executor_token IS NOT NULL)))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    for table in ("reference_geocode_origins", "reference_geocode_effects"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY reference_geocode_ledger ON {table} TO meu_braco_direito_reference_ledger
          USING(tenant_id={tenant}) WITH CHECK(tenant_id={tenant})""")
        op.execute(f"GRANT SELECT ON {table} TO meu_braco_direito_reference_ledger")
    op.execute("GRANT UPDATE(context_version) ON reference_geocode_origins TO meu_braco_direito_reference_ledger")
    op.execute("GRANT UPDATE(state,executor_token) ON reference_geocode_effects TO meu_braco_direito_reference_ledger")
    op.execute("ALTER TABLE reference_cost_reservations DROP CONSTRAINT reference_cost_one_search")
    op.execute("""ALTER TABLE reference_cost_reservations ADD COLUMN geocode_origin_id uuid,
      ADD CONSTRAINT reference_cost_one_search CHECK (
        (discovery_id IS NOT NULL AND provider_search_id IS NULL AND feed_window_id IS NULL
          AND geocode_origin_id IS NULL AND pilot_id IS NULL) OR
        (discovery_id IS NULL AND provider_search_id IS NOT NULL AND feed_window_id IS NULL
          AND geocode_origin_id IS NULL AND pilot_id IS NOT NULL) OR
        (discovery_id IS NULL AND provider_search_id IS NULL AND feed_window_id IS NOT NULL
          AND geocode_origin_id IS NULL AND pilot_id IS NOT NULL) OR
        (discovery_id IS NULL AND provider_search_id IS NULL AND feed_window_id IS NULL
          AND geocode_origin_id IS NOT NULL AND pilot_id IS NOT NULL)),
      ADD FOREIGN KEY(tenant_id,business_id,geocode_origin_id)
        REFERENCES reference_geocode_origins(tenant_id,business_id,id)""")
    op.execute("ALTER TABLE reference_provider_tariffs DROP CONSTRAINT reference_provider_tariff_charge_class")
    op.execute("""ALTER TABLE reference_provider_tariffs ADD CONSTRAINT reference_provider_tariff_charge_class CHECK(
      (provider='google' AND (field_mask LIKE 'places.%' OR field_mask LIKE 'geocode-v4:results.%')) OR
      (provider='jev' AND field_mask ~ '^jev-model:[a-zA-Z0-9_.-]{1,120}$') OR
      (provider='apify' AND field_mask ~ '^apify-instagram-feed:[0-9]+[.][0-9]+[.][0-9]+$'))""")
    op.execute("ALTER FUNCTION public.reference_cost_finish(uuid,bigint) RENAME TO reference_cost_finish_feed_inner")
    op.execute(
        "REVOKE ALL ON FUNCTION public.reference_cost_finish_feed_inner(uuid,bigint) "
        "FROM PUBLIC,meu_braco_direito_correlator"
    )
    op.execute("""CREATE FUNCTION public.reference_cost_finish(p_id uuid,p_actual bigint) RETURNS jsonb
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid; origin uuid;
      BEGIN
        SELECT geocode_origin_id INTO origin FROM public.reference_cost_reservations WHERE tenant_id=t AND id=p_id;
        IF origin IS NOT NULL THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_FENCE_REQUIRED'; END IF;
        RETURN public.reference_cost_finish_feed_inner(p_id,p_actual);
      END $$""")
    op.execute("ALTER FUNCTION public.reference_cost_finish(uuid,bigint) OWNER TO meu_braco_direito_reference_ledger")
    op.execute("REVOKE ALL ON FUNCTION public.reference_cost_finish(uuid,bigint) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION public.reference_cost_finish(uuid,bigint) TO meu_braco_direito_correlator")
    op.execute("""CREATE FUNCTION public.reference_geocode_claim(
      p_business uuid,p_effect uuid,p_event uuid,p_origin uuid,p_pilot uuid,p_mac text,
      p_key text,p_tariff text,p_credential text,p_class text,p_amount bigint,p_context bigint)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        e public.reference_geocode_effects%ROWTYPE; pilot public.reference_provider_pilots%ROWTYPE;
        tariff public.reference_provider_tariffs%ROWTYPE; pol public.reference_cost_policies%ROWTYPE;
        pp public.reference_cost_policy_providers%ROWTYPE; r public.reference_cost_reservations%ROWTYPE;
        cm date; used numeric; token uuid;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_effect IS NULL OR p_event IS NULL
          OR p_origin IS NULL OR p_pilot IS NULL OR p_mac IS NULL OR p_mac !~ '^[0-9a-f]{64}$'
          OR p_context IS NULL OR p_context<1 THEN RAISE EXCEPTION 'REFERENCE_GEOCODE_INTENT_INVALID'; END IF;
        SELECT * INTO e FROM public.reference_geocode_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_effect;
        IF NOT FOUND OR e.origin_id IS DISTINCT FROM p_origin OR e.pilot_id IS DISTINCT FROM p_pilot
          OR e.event_id IS DISTINCT FROM p_event OR e.request_mac IS DISTINCT FROM p_mac
          OR e.key_version IS DISTINCT FROM p_key OR e.tariff_version IS DISTINCT FROM p_tariff
          OR e.credential_version IS DISTINCT FROM p_credential OR e.charge_class IS DISTINCT FROM p_class
          OR e.reserved_usd_micros IS DISTINCT FROM p_amount OR NOT EXISTS(
            SELECT 1 FROM public.reference_geocode_origins o WHERE o.tenant_id=t AND o.business_id=p_business
              AND o.actor_id=a AND o.id=p_origin AND o.context_version=p_context) THEN
          RAISE EXCEPTION 'REFERENCE_GEOCODE_INTENT_INVALID'; END IF;
        IF e.state<>'pending' THEN RETURN jsonb_build_object('created',false,'state',e.state); END IF;
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO e FROM public.reference_geocode_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_effect FOR UPDATE;
        IF e.state<>'pending' THEN RETURN jsonb_build_object('created',false,'state',e.state); END IF;
        PERFORM 1 FROM public.reference_geocode_origins WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_origin AND context_version=p_context FOR SHARE;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_GEOCODE_INTENT_INVALID'; END IF;
        IF NOT EXISTS(SELECT 1 FROM public.outbox_events o WHERE o.id=p_event AND o.tenant_id=t
          AND o.event_type='reference.provider_effect_requested' AND o.payload=jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_effect::text)) THEN
          RAISE EXCEPTION 'REFERENCE_PROVIDER_EVENT_INVALID'; END IF;
        SELECT * INTO tariff FROM public.reference_provider_tariffs WHERE version=p_tariff FOR SHARE;
        IF NOT FOUND OR NOT tariff.active OR tariff.provider<>'google' OR tariff.field_mask IS DISTINCT FROM p_class
          OR p_amount<tariff.minimum_reserved_usd_micros THEN
          RAISE EXCEPTION 'REFERENCE_PROVIDER_TARIFF_INVALID'; END IF;
        SELECT * INTO pilot FROM public.reference_provider_pilots WHERE id=p_pilot FOR UPDATE;
        IF NOT FOUND OR NOT pilot.active THEN RAISE EXCEPTION 'REFERENCE_PILOT_DISABLED'; END IF;
        IF pilot.reserved_usd_micros+p_amount>pilot.cap_usd_micros THEN
          RAISE EXCEPTION 'REFERENCE_PILOT_BUDGET_EXCEEDED'; END IF;
        SELECT q.* INTO pol FROM public.reference_cost_policy_head h
          JOIN public.reference_cost_policies q ON q.id=h.policy_id WHERE h.singleton;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_BUDGET_DISABLED'; END IF;
        SELECT * INTO pp FROM public.reference_cost_policy_providers WHERE policy_id=pol.id AND provider='google';
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_BUDGET_DISABLED'; END IF;
        SELECT coalesce(sum(CASE WHEN state='completed' THEN actual_usd_micros ELSE reserved_usd_micros END),0)
          INTO used FROM public.reference_cost_reservations WHERE tenant_id=t AND business_id=p_business
            AND geocode_origin_id=p_origin;
        IF used+p_amount>least(pol.per_search,pp.per_search) THEN
          RAISE EXCEPTION 'REFERENCE_SEARCH_BUDGET_EXCEEDED'; END IF;
        cm := date_trunc('month',clock_timestamp() AT TIME ZONE pol.timezone)::date;
        SELECT coalesce(sum(CASE WHEN month=cm THEN committed_usd_micros ELSE outstanding_usd_micros END),0)
          INTO used FROM public.reference_cost_monthly WHERE provider='all';
        IF used+p_amount>pol.monthly_total THEN RAISE EXCEPTION 'REFERENCE_MONTHLY_BUDGET_EXCEEDED'; END IF;
        SELECT coalesce(sum(CASE WHEN month=cm THEN committed_usd_micros ELSE outstanding_usd_micros END),0)
          INTO used FROM public.reference_cost_monthly WHERE provider='google';
        IF used+p_amount>pp.monthly_total THEN RAISE EXCEPTION 'REFERENCE_MONTHLY_PROVIDER_BUDGET_EXCEEDED'; END IF;
        UPDATE public.reference_provider_pilots SET reserved_usd_micros=reserved_usd_micros+p_amount WHERE id=p_pilot;
        INSERT INTO public.reference_cost_monthly(month,provider,committed_usd_micros,outstanding_usd_micros)
          VALUES(cm,'all',p_amount,p_amount),(cm,'google',p_amount,p_amount)
          ON CONFLICT(month,provider) DO UPDATE SET
            committed_usd_micros=reference_cost_monthly.committed_usd_micros+excluded.committed_usd_micros,
            outstanding_usd_micros=reference_cost_monthly.outstanding_usd_micros+excluded.outstanding_usd_micros;
        INSERT INTO public.reference_cost_reservations(id,tenant_id,business_id,actor_id,discovery_id,
          provider_search_id,feed_window_id,geocode_origin_id,pilot_id,effect_id,request_hash,provider,month,
          reserved_usd_micros,state,policy_id)
          VALUES(gen_random_uuid(),t,p_business,a,NULL,NULL,NULL,p_origin,p_pilot,p_effect,p_mac,'google',cm,p_amount,
            'claimed',pol.id) RETURNING * INTO r;
        token := gen_random_uuid();
        UPDATE public.reference_geocode_effects SET state='running',executor_token=token
          WHERE tenant_id=t AND business_id=p_business AND id=p_effect;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_effect,'reference.geocode_cost_claimed',r.id);
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(gen_random_uuid(),t,'reference.provider_cost_changed',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_effect::text));
        RETURN jsonb_build_object('created',true,'state','running','executor_token',token);
      END $$""")
    op.execute(f"ALTER FUNCTION public.reference_geocode_claim({_CLAIM}) OWNER TO meu_braco_direito_reference_ledger")
    op.execute(f"REVOKE ALL ON FUNCTION public.reference_geocode_claim({_CLAIM}) FROM PUBLIC")
    op.execute("""CREATE FUNCTION public.reference_geocode_uncertain(p_effect uuid,p_token uuid) RETURNS void
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        e public.reference_geocode_effects%ROWTYPE;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_effect IS NULL OR p_token IS NULL THEN
          RAISE EXCEPTION 'REFERENCE_GEOCODE_FENCE_INVALID'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO e FROM public.reference_geocode_effects WHERE tenant_id=t AND actor_id=a
          AND id=p_effect FOR UPDATE;
        IF NOT FOUND OR e.executor_token IS DISTINCT FROM p_token OR e.state NOT IN ('running','uncertain') THEN
          RAISE EXCEPTION 'REFERENCE_GEOCODE_FENCE_INVALID'; END IF;
        IF e.state='uncertain' THEN RETURN; END IF;
        UPDATE public.reference_geocode_effects SET state='uncertain' WHERE tenant_id=t AND business_id=e.business_id
          AND id=e.id;
        UPDATE public.reference_cost_reservations SET state='uncertain',updated_at=clock_timestamp()
          WHERE tenant_id=t AND business_id=e.business_id AND actor_id=a AND geocode_origin_id=e.origin_id
            AND effect_id=e.id AND state='claimed';
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_RESERVATION_NOT_FOUND'; END IF;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,e.id,'reference.geocode_cost_uncertain',e.origin_id);
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(gen_random_uuid(),t,'reference.provider_cost_changed',jsonb_build_object(
            'business_id',e.business_id::text,'actor_id',a::text,'operation_id',e.id::text));
      END $$""")
    op.execute(
        "ALTER FUNCTION public.reference_geocode_uncertain(uuid,uuid) OWNER TO meu_braco_direito_reference_ledger"
    )
    op.execute("REVOKE ALL ON FUNCTION public.reference_geocode_uncertain(uuid,uuid) FROM PUBLIC")


def downgrade():
    op.execute(
        "LOCK TABLE reference_geocode_effects,reference_geocode_origins,reference_cost_reservations "
        "IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_geocode_effects) OR
      EXISTS(SELECT 1 FROM reference_geocode_origins) OR EXISTS(SELECT 1 FROM reference_cost_reservations
      WHERE geocode_origin_id IS NOT NULL) OR EXISTS(SELECT 1 FROM reference_provider_tariffs
      WHERE provider='google' AND field_mask LIKE 'geocode-v4:%') THEN
      RAISE EXCEPTION 'REFERENCE_GEOCODE_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute(f"DROP FUNCTION public.reference_geocode_claim({_CLAIM})")
    op.execute("DROP FUNCTION public.reference_geocode_uncertain(uuid,uuid)")
    op.execute("DROP FUNCTION public.reference_cost_finish(uuid,bigint)")
    op.execute("ALTER FUNCTION public.reference_cost_finish_feed_inner(uuid,bigint) RENAME TO reference_cost_finish")
    op.execute("REVOKE ALL ON FUNCTION public.reference_cost_finish(uuid,bigint) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION public.reference_cost_finish(uuid,bigint) TO meu_braco_direito_correlator")
    op.execute("ALTER TABLE reference_provider_tariffs DROP CONSTRAINT reference_provider_tariff_charge_class")
    op.execute("""ALTER TABLE reference_provider_tariffs ADD CONSTRAINT reference_provider_tariff_charge_class CHECK(
      (provider='google' AND field_mask LIKE 'places.%') OR
      (provider='jev' AND field_mask ~ '^jev-model:[a-zA-Z0-9_.-]{1,120}$') OR
      (provider='apify' AND field_mask ~ '^apify-instagram-feed:[0-9]+[.][0-9]+[.][0-9]+$'))""")
    op.execute("ALTER TABLE reference_cost_reservations DROP CONSTRAINT reference_cost_one_search")
    op.execute("ALTER TABLE reference_cost_reservations DROP COLUMN geocode_origin_id")
    op.execute("""ALTER TABLE reference_cost_reservations ADD CONSTRAINT reference_cost_one_search CHECK (
      (discovery_id IS NOT NULL AND provider_search_id IS NULL AND feed_window_id IS NULL AND pilot_id IS NULL) OR
      (discovery_id IS NULL AND provider_search_id IS NOT NULL AND feed_window_id IS NULL AND pilot_id IS NOT NULL) OR
      (discovery_id IS NULL AND provider_search_id IS NULL AND feed_window_id IS NOT NULL AND pilot_id IS NOT NULL))""")
    op.execute("DROP TABLE reference_geocode_effects,reference_geocode_origins")
