"""Admit one fenced Jev intent for a transient Google batch, without raw data."""

from alembic import op

revision = "0080_reference_jev_intent"
down_revision = "0079_reference_filtered_batch"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("LOCK TABLE reference_provider_effects,outbox_events IN ACCESS EXCLUSIVE MODE")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_jev_parent")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_jev_parent CHECK(
      (provider='google' AND parent_google_effect_id IS NULL AND
        (source_batch_mac IS NULL OR source_batch_mac ~ '^[0-9a-f]{64}$')) OR
      (provider='jev' AND parent_google_effect_id IS NOT NULL AND source_batch_mac IS NOT NULL
        AND source_batch_mac ~ '^[0-9a-f]{64}$'))""")
    op.execute("""ALTER TABLE reference_provider_effects ADD COLUMN request_event_id uuid,
      ADD FOREIGN KEY(tenant_id,request_event_id) REFERENCES outbox_events(tenant_id,id)""")
    op.execute("""CREATE UNIQUE INDEX reference_one_jev_intent_per_google
      ON reference_provider_effects(tenant_id,business_id,parent_google_effect_id) WHERE provider='jev'""")
    op.execute("""GRANT INSERT,UPDATE(source_batch_mac) ON reference_provider_effects
      TO meu_braco_direito_reference_ledger""")
    op.execute("""CREATE FUNCTION public.reference_jev_require_parent_batch() RETURNS trigger
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE source char(64);
      BEGIN
        IF NEW.provider='jev' AND OLD.state='pending' AND NEW.state='running' THEN
          SELECT g.source_batch_mac INTO source FROM public.reference_provider_effects g
            WHERE g.tenant_id=NEW.tenant_id AND g.business_id=NEW.business_id
              AND g.actor_id=NEW.actor_id AND g.id=NEW.parent_google_effect_id
              AND g.search_id=NEW.search_id AND g.pilot_id=NEW.pilot_id AND g.provider='google';
          IF NOT FOUND OR source IS DISTINCT FROM NEW.source_batch_mac THEN
            RAISE EXCEPTION 'REFERENCE_JEV_PARENT_INVALID'; END IF;
        END IF;
        RETURN NEW;
      END $$""")
    op.execute("""ALTER FUNCTION public.reference_jev_require_parent_batch()
      OWNER TO meu_braco_direito_reference_ledger""")
    op.execute("REVOKE ALL ON FUNCTION public.reference_jev_require_parent_batch() FROM PUBLIC")
    op.execute("""CREATE TRIGGER reference_jev_require_parent_batch BEFORE UPDATE OF state
      ON reference_provider_effects FOR EACH ROW EXECUTE FUNCTION public.reference_jev_require_parent_batch()""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    op.execute(f"""CREATE POLICY reference_jev_intent_event_emit ON outbox_events FOR INSERT
      TO meu_braco_direito_reference_ledger WITH CHECK(tenant_id={tenant}
      AND event_type='reference.provider_effect_requested' AND payload->>'actor_id'={actor}::text)""")
    op.execute("""CREATE FUNCTION public.reference_jev_intent(
      p_business uuid,p_search uuid,p_google uuid,p_google_event uuid,p_google_token uuid,
      p_jev uuid,p_jev_event uuid,p_mac text,p_key text,p_tariff text,p_credential text,
      p_charge text,p_amount bigint,p_batch text,p_context bigint)
      RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        g public.reference_provider_effects%ROWTYPE; e public.reference_provider_effects%ROWTYPE;
        tariff public.reference_provider_tariffs%ROWTYPE; active_owner boolean;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_search IS NULL OR p_google IS NULL
          OR p_google_event IS NULL OR p_google_token IS NULL OR p_jev IS NULL OR p_jev=p_google
          OR p_jev_event IS NULL OR p_mac IS NULL OR p_mac !~ '^[0-9a-f]{64}$'
          OR p_batch IS NULL OR p_batch !~ '^[0-9a-f]{64}$'
          OR p_key IS NULL OR p_key !~ '^[a-zA-Z0-9_.-]{1,64}$'
          OR p_tariff IS NULL OR p_tariff !~ '^[a-zA-Z0-9_.-]{1,64}$'
          OR p_credential IS NULL OR p_credential !~ '^[a-zA-Z0-9_.-]{1,64}$'
          OR p_charge IS NULL OR p_charge !~ '^jev-model:[a-zA-Z0-9_.-]{1,120}$'
          OR p_amount IS NULL OR p_amount NOT BETWEEN 1 AND 5000000 OR p_context IS NULL OR p_context<1 THEN
          RAISE EXCEPTION 'REFERENCE_JEV_INTENT_INVALID'; END IF;
        active_owner := public.lock_reference_cost_owner();
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO g FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_google AND provider='google' FOR UPDATE;
        IF NOT FOUND OR g.executor_token IS DISTINCT FROM p_google_token OR g.search_id IS DISTINCT FROM p_search THEN
          RAISE EXCEPTION 'REFERENCE_JEV_PARENT_INVALID'; END IF;
        IF NOT EXISTS(SELECT 1 FROM public.outbox_events o WHERE o.id=p_google_event AND o.tenant_id=t
          AND o.event_type='reference.provider_effect_requested' AND o.payload=jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',g.id::text)) THEN
          RAISE EXCEPTION 'REFERENCE_PROVIDER_EVENT_INVALID'; END IF;
        SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND id=p_jev AND actor_id=a AND provider='jev' FOR UPDATE;
        IF FOUND THEN
          IF e.search_id IS DISTINCT FROM p_search OR e.parent_google_effect_id IS DISTINCT FROM p_google
            OR e.pilot_id IS DISTINCT FROM g.pilot_id OR e.request_mac IS DISTINCT FROM p_mac
            OR e.key_version IS DISTINCT FROM p_key OR e.tariff_version IS DISTINCT FROM p_tariff
            OR e.credential_version IS DISTINCT FROM p_credential OR e.field_mask IS DISTINCT FROM p_charge
            OR e.reserved_usd_micros IS DISTINCT FROM p_amount OR e.source_batch_mac IS DISTINCT FROM p_batch
            OR g.source_batch_mac IS DISTINCT FROM p_batch OR e.request_event_id IS NULL OR
            NOT EXISTS(SELECT 1 FROM public.reference_provider_searches s WHERE s.tenant_id=t
              AND s.business_id=p_business AND s.actor_id=a AND s.id=p_search AND s.context_version=p_context) OR
            NOT EXISTS(SELECT 1 FROM public.outbox_events o WHERE o.id=e.request_event_id AND o.tenant_id=t
              AND o.event_type='reference.provider_effect_requested' AND o.payload=jsonb_build_object(
                'business_id',p_business::text,'actor_id',a::text,'operation_id',e.id::text)) THEN
            RAISE EXCEPTION 'REFERENCE_JEV_INTENT_CONFLICT'; END IF;
          RETURN e.request_event_id;
        END IF;
        IF NOT active_owner THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        IF g.state<>'running' OR (g.source_batch_mac IS NOT NULL AND g.source_batch_mac<>p_batch) THEN
          RAISE EXCEPTION 'REFERENCE_JEV_PARENT_INVALID'; END IF;
        PERFORM 1 FROM public.reference_provider_searches s WHERE s.tenant_id=t AND s.business_id=p_business
          AND s.actor_id=a AND s.id=p_search AND s.context_version=p_context AND s.state='pending' FOR SHARE;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_SEARCH_INACTIVE'; END IF;
        SELECT * INTO tariff FROM public.reference_provider_tariffs WHERE version=p_tariff FOR SHARE;
        IF NOT FOUND OR NOT tariff.active OR tariff.provider<>'jev' OR tariff.field_mask<>p_charge
          OR p_amount<tariff.minimum_reserved_usd_micros THEN
          RAISE EXCEPTION 'REFERENCE_PROVIDER_TARIFF_INVALID'; END IF;
        UPDATE public.reference_provider_effects SET source_batch_mac=p_batch,updated_at=clock_timestamp()
          WHERE tenant_id=t AND business_id=p_business AND id=g.id;
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(p_jev_event,t,'reference.provider_effect_requested',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_jev::text));
        INSERT INTO public.reference_provider_effects
          (id,tenant_id,business_id,actor_id,search_id,pilot_id,provider,request_mac,key_version,tariff_version,
           credential_version,field_mask,reserved_usd_micros,state,parent_google_effect_id,source_batch_mac,request_event_id)
          VALUES(p_jev,t,p_business,a,p_search,g.pilot_id,'jev',p_mac,p_key,p_tariff,p_credential,
            p_charge,p_amount,'pending',p_google,p_batch,p_jev_event);
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_jev,'reference.jev_intent_created',p_search);
        RETURN p_jev_event;
      END $$""")
    op.execute("""ALTER FUNCTION public.reference_jev_intent(
      uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,text,bigint)
      OWNER TO meu_braco_direito_reference_ledger""")
    op.execute("""REVOKE ALL ON FUNCTION public.reference_jev_intent(
      uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,text,bigint) FROM PUBLIC""")
    op.execute("""GRANT EXECUTE ON FUNCTION public.reference_jev_intent(
      uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,text,bigint)
      TO meu_braco_direito_correlator""")


def downgrade():
    op.execute("LOCK TABLE reference_provider_effects,outbox_events IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM reference_provider_effects WHERE request_event_id IS NOT NULL OR
          (provider='google' AND source_batch_mac IS NOT NULL)) THEN
        RAISE EXCEPTION 'REFERENCE_JEV_INTENT_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF;
    END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("""DROP FUNCTION public.reference_jev_intent(
      uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,text,bigint)""")
    op.execute("DROP TRIGGER reference_jev_require_parent_batch ON reference_provider_effects")
    op.execute("DROP FUNCTION public.reference_jev_require_parent_batch()")
    op.execute("DROP POLICY reference_jev_intent_event_emit ON outbox_events")
    op.execute("""REVOKE INSERT,UPDATE(source_batch_mac) ON reference_provider_effects
      FROM meu_braco_direito_reference_ledger""")
    op.execute("DROP INDEX reference_one_jev_intent_per_google")
    op.execute("ALTER TABLE reference_provider_effects DROP COLUMN request_event_id")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_jev_parent")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_jev_parent CHECK(
      (provider='google' AND parent_google_effect_id IS NULL AND source_batch_mac IS NULL) OR
      (provider='jev' AND parent_google_effect_id IS NOT NULL AND source_batch_mac IS NOT NULL
        AND source_batch_mac ~ '^[0-9a-f]{64}$'))""")
