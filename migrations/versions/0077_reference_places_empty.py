"""Fenced, durable empty-result commit; never persists raw provider data."""

from alembic import op

revision = "0077_reference_places_empty"
down_revision = "0076_reference_provider_guard"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_state_check")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_check")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_effects_state_check
      CHECK(state IN ('pending','running','uncertain','completed_empty'))""")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_effects_check CHECK(
      (state='pending' AND executor_token IS NULL) OR
      (state IN ('running','uncertain','completed_empty') AND executor_token IS NOT NULL))""")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed',
       'reference.provider_effect_requested','reference.provider_cost_changed','reference.provider_effect_completed'))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    op.execute(f"""CREATE POLICY reference_provider_effect_completed_emit ON outbox_events FOR INSERT
      TO meu_braco_direito_reference_ledger WITH CHECK(tenant_id={tenant}
      AND event_type='reference.provider_effect_completed' AND payload->>'actor_id'={actor}::text)""")
    op.execute("""CREATE FUNCTION public.reference_provider_complete_empty(p_effect uuid,p_event uuid,p_token uuid)
      RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        e public.reference_provider_effects%ROWTYPE; r public.reference_cost_reservations%ROWTYPE;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_effect IS NULL OR p_event IS NULL OR p_token IS NULL THEN
          RAISE EXCEPTION 'REFERENCE_PROVIDER_INVALID'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO e FROM public.reference_provider_effects
          WHERE tenant_id=t AND actor_id=a AND id=p_effect FOR UPDATE;
        IF NOT FOUND OR e.executor_token IS DISTINCT FROM p_token THEN
          RAISE EXCEPTION 'REFERENCE_PROVIDER_FENCE_INVALID'; END IF;
        IF NOT EXISTS(SELECT 1 FROM public.outbox_events o WHERE o.id=p_event AND o.tenant_id=t
          AND o.event_type='reference.provider_effect_requested' AND o.payload=jsonb_build_object(
            'business_id',e.business_id::text,'actor_id',a::text,'operation_id',e.id::text)) THEN
          RAISE EXCEPTION 'REFERENCE_PROVIDER_EVENT_INVALID'; END IF;
        IF e.state='completed_empty' THEN RETURN e.state; END IF;
        IF e.state<>'running' THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_FENCE_INVALID'; END IF;
        PERFORM 1 FROM public.reference_provider_searches s WHERE s.tenant_id=t AND s.business_id=e.business_id
          AND s.id=e.search_id AND s.actor_id=a AND s.state='pending' FOR SHARE;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_SEARCH_INACTIVE'; END IF;
        SELECT * INTO r FROM public.reference_cost_reservations
          WHERE tenant_id=t AND actor_id=a AND effect_id=e.id FOR UPDATE;
        IF NOT FOUND OR r.state<>'claimed' OR r.provider_search_id IS DISTINCT FROM e.search_id
          OR r.pilot_id IS DISTINCT FROM e.pilot_id THEN RAISE EXCEPTION 'REFERENCE_RESERVATION_NOT_FOUND'; END IF;
        UPDATE public.reference_cost_reservations SET state='uncertain',updated_at=clock_timestamp()
          WHERE tenant_id=t AND id=r.id;
        UPDATE public.reference_provider_effects SET state='completed_empty',updated_at=clock_timestamp()
          WHERE tenant_id=t AND business_id=e.business_id AND id=e.id;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,e.id,'reference.provider_empty_completed',r.id);
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(gen_random_uuid(),t,'reference.provider_effect_completed',jsonb_build_object(
            'business_id',e.business_id::text,'actor_id',a::text,'operation_id',e.id::text));
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(gen_random_uuid(),t,'reference.provider_cost_changed',jsonb_build_object(
            'business_id',e.business_id::text,'actor_id',a::text,'operation_id',e.id::text));
        RETURN 'completed_empty';
      END $$""")
    op.execute("""ALTER FUNCTION public.reference_provider_complete_empty(uuid,uuid,uuid)
      OWNER TO meu_braco_direito_reference_ledger""")
    op.execute("REVOKE ALL ON FUNCTION public.reference_provider_complete_empty(uuid,uuid,uuid) FROM PUBLIC")
    op.execute("""GRANT EXECUTE ON FUNCTION public.reference_provider_complete_empty(uuid,uuid,uuid)
      TO meu_braco_direito_correlator""")


def downgrade():
    op.execute("LOCK TABLE reference_provider_effects,outbox_events IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM reference_provider_effects WHERE state='completed_empty') OR
         EXISTS(SELECT 1 FROM outbox_events WHERE event_type='reference.provider_effect_completed') THEN
        RAISE EXCEPTION 'REFERENCE_PROVIDER_EMPTY_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF;
    END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("DROP FUNCTION public.reference_provider_complete_empty(uuid,uuid,uuid)")
    op.execute("DROP POLICY reference_provider_effect_completed_emit ON outbox_events")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed',
       'reference.provider_effect_requested','reference.provider_cost_changed'))""")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_state_check")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_check")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_effects_state_check
      CHECK(state IN ('pending','running','uncertain'))""")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_effects_check CHECK(
      (state='pending' AND executor_token IS NULL) OR
      (state IN ('running','uncertain') AND executor_token IS NOT NULL))""")
