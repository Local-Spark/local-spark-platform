"""Private, fenced recording of provider resource identities; no cleanup IO.

No runtime role can invoke the recorder or access the resource table. A future
coordinator must authenticate the actual provider response before recording it
and prove exclusive ownership before deleting anything.
"""

from alembic import op

revision = "0093_reference_feed_resources"
down_revision = "0092_reference_shortlist"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE reference_feed_resources (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,effect_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),operation_id uuid NOT NULL,event_id uuid NOT NULL,
      run_id text NOT NULL CHECK(run_id ~ '^[A-Za-z0-9_-]{1,64}$'),
      dataset_id text NOT NULL CHECK(dataset_id ~ '^[A-Za-z0-9_-]{1,64}$'),
      store_id text NOT NULL CHECK(store_id ~ '^[A-Za-z0-9_-]{1,64}$'),
      queue_id text NOT NULL CHECK(queue_id ~ '^[A-Za-z0-9_-]{1,64}$'),
      build_id text NOT NULL CHECK(build_id ~ '^[A-Za-z0-9_-]{1,64}$'),
      actor_build text NOT NULL CHECK(actor_build ~ '^[0-9]+[.][0-9]+[.][0-9]+$'),
      recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(tenant_id,business_id,effect_id), UNIQUE(tenant_id,business_id,operation_id),
      UNIQUE(tenant_id,business_id,run_id),
      FOREIGN KEY(tenant_id,business_id,effect_id) REFERENCES reference_feed_effects(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    op.execute("ALTER TABLE reference_feed_resources ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reference_feed_resources FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY reference_feed_resource_ledger ON reference_feed_resources
      TO meu_braco_direito_reference_ledger USING(tenant_id={tenant} AND actor_id={actor})
      WITH CHECK(tenant_id={tenant} AND actor_id={actor})""")
    op.execute("GRANT SELECT,INSERT ON reference_feed_resources TO meu_braco_direito_reference_ledger")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed',
       'reference.provider_effect_requested','reference.provider_cost_changed','reference.provider_effect_completed',
       'reference.provider_search_requested','reference.provider_search_cancelled','reference.real_selection_confirmed',
       'reference.private_shortlist_prepared','reference.feed_resources_recorded'))""")
    op.execute(f"""CREATE POLICY reference_feed_resource_event_emit ON outbox_events FOR INSERT
      TO meu_braco_direito_reference_ledger WITH CHECK(tenant_id={tenant}
        AND event_type='reference.feed_resources_recorded' AND payload->>'actor_id'={actor}::text)""")
    op.execute("""CREATE FUNCTION public.reference_record_feed_resources(
      p_business uuid,p_effect uuid,p_executor uuid,p_operation uuid,
      p_run text,p_dataset text,p_store text,p_queue text,p_build_id text,p_build text)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        e public.reference_feed_effects%ROWTYPE; prior public.reference_feed_resources%ROWTYPE;
        event_id uuid;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_effect IS NULL OR p_executor IS NULL
          OR p_operation IS NULL OR p_run IS NULL OR p_run !~ '^[A-Za-z0-9_-]{1,64}$'
          OR p_dataset IS NULL OR p_dataset !~ '^[A-Za-z0-9_-]{1,64}$'
          OR p_store IS NULL OR p_store !~ '^[A-Za-z0-9_-]{1,64}$'
          OR p_queue IS NULL OR p_queue !~ '^[A-Za-z0-9_-]{1,64}$'
          OR p_build_id IS NULL OR p_build_id !~ '^[A-Za-z0-9_-]{1,64}$'
          OR p_build IS NULL OR length(p_build)>64 OR p_build !~ '^[0-9]+[.][0-9]+[.][0-9]+$' THEN
          RAISE EXCEPTION 'REFERENCE_FEED_RESOURCE_INVALID'; END IF;
        -- Keep the same lock order as the feed cost and uncertainty functions.
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO e FROM public.reference_feed_effects
          WHERE tenant_id=t AND business_id=p_business AND actor_id=a AND id=p_effect FOR UPDATE;
        IF NOT FOUND OR e.executor_token IS DISTINCT FROM p_executor OR e.state NOT IN ('running','uncertain')
          OR e.actor_build IS DISTINCT FROM p_build THEN RAISE EXCEPTION 'REFERENCE_FEED_FENCE_INVALID'; END IF;
        IF NOT EXISTS(SELECT 1 FROM public.outbox_events o WHERE o.tenant_id=t AND o.id=e.event_id
          AND o.event_type='reference.provider_effect_requested' AND o.payload=jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_effect::text)) THEN
          RAISE EXCEPTION 'REFERENCE_FEED_EVENT_INVALID'; END IF;
        IF NOT EXISTS(SELECT 1 FROM public.reference_cost_reservations r WHERE r.tenant_id=t
          AND r.business_id=p_business AND r.actor_id=a AND r.feed_window_id=e.window_id AND r.effect_id=e.id
          AND r.pilot_id=e.pilot_id AND r.provider='apify' AND r.request_hash=e.request_mac
          AND r.reserved_usd_micros=e.reserved_usd_micros AND r.state IN ('claimed','uncertain')) THEN
          RAISE EXCEPTION 'REFERENCE_FEED_RESERVATION_INVALID'; END IF;
        SELECT * INTO prior FROM public.reference_feed_resources
          WHERE tenant_id=t AND business_id=p_business AND (effect_id=p_effect OR operation_id=p_operation);
        IF FOUND THEN
          IF prior.actor_id IS DISTINCT FROM a OR prior.effect_id IS DISTINCT FROM p_effect
            OR prior.operation_id IS DISTINCT FROM p_operation OR prior.run_id IS DISTINCT FROM p_run
            OR prior.dataset_id IS DISTINCT FROM p_dataset OR prior.store_id IS DISTINCT FROM p_store
            OR prior.queue_id IS DISTINCT FROM p_queue OR prior.build_id IS DISTINCT FROM p_build_id
            OR prior.actor_build IS DISTINCT FROM p_build THEN
            RAISE EXCEPTION 'REFERENCE_FEED_RESOURCE_CONFLICT'; END IF;
          RETURN jsonb_build_object('effect_id',p_effect,'operation_id',p_operation,'event_id',prior.event_id,
            'created',false);
        END IF;
        event_id := gen_random_uuid();
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(event_id,t,'reference.feed_resources_recorded',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_operation::text));
        BEGIN
          INSERT INTO public.reference_feed_resources
            (tenant_id,business_id,effect_id,actor_id,operation_id,event_id,run_id,dataset_id,store_id,queue_id,
             build_id,actor_build)
            VALUES(t,p_business,p_effect,a,p_operation,event_id,p_run,p_dataset,p_store,p_queue,p_build_id,p_build);
        EXCEPTION WHEN unique_violation THEN RAISE EXCEPTION 'REFERENCE_FEED_RESOURCE_CONFLICT'; END;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_operation,'reference.feed_resources_recorded',p_effect);
        RETURN jsonb_build_object('effect_id',p_effect,'operation_id',p_operation,'event_id',event_id,'created',true);
      END $$""")
    op.execute(
        "ALTER FUNCTION public.reference_record_feed_resources(uuid,uuid,uuid,uuid,text,text,text,text,text,text) "
        "OWNER TO meu_braco_direito_reference_ledger"
    )
    op.execute("""REVOKE ALL ON FUNCTION
      public.reference_record_feed_resources(uuid,uuid,uuid,uuid,text,text,text,text,text,text) FROM PUBLIC""")


def downgrade():
    op.execute("LOCK TABLE reference_feed_resources,outbox_events IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_feed_resources) OR
      EXISTS(SELECT 1 FROM outbox_events WHERE event_type='reference.feed_resources_recorded') THEN
      RAISE EXCEPTION 'REFERENCE_FEED_RESOURCES_PREVENT_AUTOMATIC_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute(
        "DROP FUNCTION public.reference_record_feed_resources(uuid,uuid,uuid,uuid,text,text,text,text,text,text)"
    )
    op.execute("DROP POLICY reference_feed_resource_event_emit ON outbox_events")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed',
       'reference.provider_effect_requested','reference.provider_cost_changed','reference.provider_effect_completed',
       'reference.provider_search_requested','reference.provider_search_cancelled','reference.real_selection_confirmed',
       'reference.private_shortlist_prepared'))""")
    op.execute("DROP TABLE reference_feed_resources")
