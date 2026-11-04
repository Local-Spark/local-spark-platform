"""Count all owners' reservations in the existing common provider claim."""

from alembic import op

revision = "0102_shared_search_budget"
down_revision = "0101_reference_publication"
branch_labels = None
depends_on = None

_ROLE = "meu_braco_direito_reference_lock"

_LEGACY_USAGE = """
        SELECT coalesce(sum(CASE WHEN state='completed' THEN actual_usd_micros ELSE reserved_usd_micros END),0),
          coalesce(sum(CASE WHEN provider=e.provider THEN CASE WHEN state='completed' THEN actual_usd_micros
            ELSE reserved_usd_micros END ELSE 0 END),0) INTO search_used,provider_used
          FROM public.reference_cost_reservations WHERE tenant_id=t AND business_id=e.business_id
            AND provider_search_id=e.search_id;
"""

_SHARED_USAGE = """        SELECT u.total_used,u.provider_used INTO search_used,provider_used
          FROM public.reference_search_cost_usage(e.business_id,e.search_id,e.provider) u;
"""

_CLAIM = """CREATE OR REPLACE FUNCTION public.reference_provider_claim(
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
{usage_query}        IF search_used+e.reserved_usd_micros>pol.per_search THEN
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
      END $$"""


def upgrade():
    op.execute("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))")
    op.execute(f"GRANT SELECT(actual_usd_micros) ON reference_cost_reservations TO {_ROLE}")
    op.execute("""CREATE FUNCTION public.reference_search_cost_usage(p_business uuid,p_search uuid,p_provider text)
      RETURNS TABLE(total_used numeric,provider_used numeric)
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
      BEGIN
        IF p_business IS NULL OR p_search IS NULL OR p_provider IS NULL
          OR p_provider NOT IN ('google','apify','jev') OR NOT public.lock_reference_cost_owner() THEN
          RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        IF NOT EXISTS(SELECT 1 FROM public.reference_provider_searches s
          WHERE s.tenant_id=t AND s.business_id=p_business AND s.id=p_search) THEN
          RAISE EXCEPTION 'REFERENCE_PROVIDER_SEARCH_INACTIVE'; END IF;
        RETURN QUERY SELECT
          coalesce(sum(CASE WHEN r.state='completed' THEN r.actual_usd_micros ELSE r.reserved_usd_micros END),0),
          coalesce(sum(CASE WHEN r.provider=p_provider THEN CASE WHEN r.state='completed'
            THEN r.actual_usd_micros ELSE r.reserved_usd_micros END ELSE 0 END),0)
          FROM public.reference_cost_reservations r
          WHERE r.tenant_id=t AND r.business_id=p_business AND r.provider_search_id=p_search;
      END $$""")
    op.execute(f"ALTER FUNCTION public.reference_search_cost_usage(uuid,uuid,text) OWNER TO {_ROLE}")
    op.execute("REVOKE ALL ON FUNCTION public.reference_search_cost_usage(uuid,uuid,text) FROM PUBLIC")
    op.execute(
        "GRANT EXECUTE ON FUNCTION public.reference_search_cost_usage(uuid,uuid,text) "
        "TO meu_braco_direito_reference_ledger"
    )
    op.execute(_CLAIM.replace("{usage_query}", _SHARED_USAGE))


def downgrade():
    op.execute("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))")
    op.execute(_CLAIM.replace("{usage_query}", _LEGACY_USAGE))
    op.execute("DROP FUNCTION public.reference_search_cost_usage(uuid,uuid,text)")
    op.execute(f"REVOKE SELECT(actual_usd_micros) ON reference_cost_reservations FROM {_ROLE}")
