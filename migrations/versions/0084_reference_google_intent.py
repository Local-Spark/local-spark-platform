"""Admit one Google effect for an already admitted private provider search.

This migration does not admit a search or enable any provider. The actual HTTP
request remains behind the separately committed cost claim.
"""

from alembic import op

revision = "0084_reference_google_intent"
down_revision = "0083_reference_final_publication"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE UNIQUE INDEX reference_one_google_intent_per_search
      ON reference_provider_effects(tenant_id,business_id,search_id) WHERE provider='google'""")
    op.execute("""CREATE FUNCTION public.reference_google_intent(
      p_business uuid,p_search uuid,p_effect uuid,p_event uuid,p_pilot uuid,
      p_mac text,p_key text,p_tariff text,p_credential text,p_mask text,p_amount bigint,p_context bigint)
      RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        e public.reference_provider_effects%ROWTYPE; tariff public.reference_provider_tariffs%ROWTYPE;
        active_owner boolean;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_search IS NULL OR p_effect IS NULL
          OR p_event IS NULL OR p_pilot IS NULL OR p_mac IS NULL OR p_mac !~ '^[0-9a-f]{64}$'
          OR p_key IS NULL OR p_key !~ '^[a-zA-Z0-9_.-]{1,64}$'
          OR p_tariff IS NULL OR p_tariff !~ '^[a-zA-Z0-9_.-]{1,64}$'
          OR p_credential IS NULL OR p_credential !~ '^[a-zA-Z0-9_.-]{1,64}$'
          OR p_mask IS NULL OR length(p_mask) NOT BETWEEN 1 AND 4096
          OR p_amount IS NULL OR p_amount NOT BETWEEN 1 AND 5000000
          OR p_context IS NULL OR p_context < 1 THEN
          RAISE EXCEPTION 'REFERENCE_GOOGLE_INTENT_INVALID'; END IF;
        active_owner := public.lock_reference_cost_owner();
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_effect AND provider='google' FOR UPDATE;
        IF FOUND THEN
          IF e.search_id IS DISTINCT FROM p_search OR e.pilot_id IS DISTINCT FROM p_pilot
            OR e.request_mac IS DISTINCT FROM p_mac OR e.key_version IS DISTINCT FROM p_key
            OR e.tariff_version IS DISTINCT FROM p_tariff OR e.credential_version IS DISTINCT FROM p_credential
            OR e.field_mask IS DISTINCT FROM p_mask OR e.reserved_usd_micros IS DISTINCT FROM p_amount
            OR e.request_event_id IS NULL OR NOT EXISTS(SELECT 1 FROM public.reference_provider_searches s
              WHERE s.tenant_id=t AND s.business_id=p_business AND s.actor_id=a AND s.id=p_search
                AND s.context_version=p_context)
            OR NOT EXISTS(SELECT 1 FROM public.outbox_events o WHERE o.id=e.request_event_id AND o.tenant_id=t
              AND o.event_type='reference.provider_effect_requested' AND o.payload=jsonb_build_object(
                'business_id',p_business::text,'actor_id',a::text,'operation_id',e.id::text)) THEN
            RAISE EXCEPTION 'REFERENCE_GOOGLE_INTENT_CONFLICT'; END IF;
          RETURN e.request_event_id;
        END IF;
        IF NOT active_owner THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        PERFORM 1 FROM public.reference_provider_searches s WHERE s.tenant_id=t AND s.business_id=p_business
          AND s.actor_id=a AND s.id=p_search AND s.context_version=p_context AND s.state='pending' FOR SHARE;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_SEARCH_INACTIVE'; END IF;
        SELECT * INTO tariff FROM public.reference_provider_tariffs WHERE version=p_tariff FOR SHARE;
        IF NOT FOUND OR NOT tariff.active OR tariff.provider<>'google' OR tariff.field_mask<>p_mask
          OR p_amount<tariff.minimum_reserved_usd_micros THEN
          RAISE EXCEPTION 'REFERENCE_PROVIDER_TARIFF_INVALID'; END IF;
        PERFORM 1 FROM public.reference_provider_pilots WHERE id=p_pilot AND active FOR SHARE;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_PILOT_DISABLED'; END IF;
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(p_event,t,'reference.provider_effect_requested',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_effect::text));
        INSERT INTO public.reference_provider_effects
          (id,tenant_id,business_id,actor_id,search_id,pilot_id,provider,request_mac,key_version,tariff_version,
           credential_version,field_mask,reserved_usd_micros,state,request_event_id)
          VALUES(p_effect,t,p_business,a,p_search,p_pilot,'google',p_mac,p_key,p_tariff,p_credential,
            p_mask,p_amount,'pending',p_event);
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_effect,'reference.google_intent_created',p_search);
        RETURN p_event;
      END $$""")
    op.execute("""ALTER FUNCTION public.reference_google_intent(
      uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,bigint)
      OWNER TO meu_braco_direito_reference_ledger""")
    op.execute("""REVOKE ALL ON FUNCTION public.reference_google_intent(
      uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,bigint) FROM PUBLIC""")
    op.execute("""GRANT EXECUTE ON FUNCTION public.reference_google_intent(
      uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,bigint) TO meu_braco_direito_correlator""")


def downgrade():
    op.execute("LOCK TABLE reference_provider_effects IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM reference_provider_effects WHERE provider='google' AND request_event_id IS NOT NULL) THEN
        RAISE EXCEPTION 'REFERENCE_GOOGLE_INTENT_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF;
    END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("""DROP FUNCTION public.reference_google_intent(
      uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,bigint)""")
    op.execute("DROP INDEX reference_one_google_intent_per_search")
