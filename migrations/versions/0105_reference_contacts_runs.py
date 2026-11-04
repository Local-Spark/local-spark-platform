"""Persist Apify run identities and reconcile authenticated run costs."""

from alembic import op

revision = "0105_reference_contacts_runs"
down_revision = "0104_reference_profile_overrides"
branch_labels = None
depends_on = None

_ROLE = "meu_braco_direito_reference_ledger"


def upgrade():
    op.execute("""DO $$ DECLARE expression text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO expression FROM pg_constraint
        WHERE conrelid='public.outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE public.outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE public.outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' ||
        expression || ') OR event_type=''reference.contacts_run_recorded'')';
    END $$""")
    op.execute(f"""CREATE POLICY contacts_run_event ON outbox_events FOR INSERT TO {_ROLE}
      WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND event_type='reference.contacts_run_recorded'
        AND payload->>'actor_id'=nullif(current_setting('app.actor_id',true),''))""")
    op.execute("""CREATE TABLE reference_contacts_runs (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,effect_id uuid NOT NULL,actor_id uuid NOT NULL,
      run_id text NOT NULL CHECK(run_id ~ '^[A-Za-z0-9_-]{1,64}$'),
      metadata jsonb NOT NULL CHECK(jsonb_typeof(metadata)='object'),
      reported_cost_usd_micros bigint CHECK(reported_cost_usd_micros>=0),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(tenant_id,business_id,effect_id),UNIQUE(run_id),
      FOREIGN KEY(tenant_id,business_id,effect_id) REFERENCES reference_provider_effects(tenant_id,business_id,id))""")
    op.execute("ALTER TABLE reference_contacts_runs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reference_contacts_runs FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY contacts_run_executor ON reference_contacts_runs TO {_ROLE}
      USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND
            actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)
      WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND
            actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)""")
    op.execute(f"GRANT SELECT,INSERT,UPDATE(reported_cost_usd_micros) ON reference_contacts_runs TO {_ROLE}")
    op.execute("""CREATE FUNCTION public.reference_contacts_record_run(
      p_business uuid,p_effect uuid,p_token uuid,p_metadata jsonb) RETURNS void
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;
        e public.reference_provider_effects%ROWTYPE;prior jsonb;item text;
      BEGIN
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_effect AND provider='apify' FOR UPDATE;
        IF e.id IS NULL OR e.executor_token IS DISTINCT FROM p_token
          OR e.state NOT IN ('running','uncertain','completed_published','failed_definitive')
          OR NOT EXISTS(SELECT 1 FROM public.reference_contacts_effect_links WHERE tenant_id=t
            AND business_id=p_business AND effect_id=e.id) THEN
          RAISE EXCEPTION 'CONTACTS_EXECUTOR_FENCE_INVALID'; END IF;
        IF jsonb_typeof(p_metadata) IS DISTINCT FROM 'object' OR NOT p_metadata ?&
          ARRAY['run_id','dataset_id','build_id','build_number','provider_actor_id','key_value_store_id','request_queue_id']
          OR p_metadata-ARRAY['run_id','dataset_id','build_id','build_number','provider_actor_id',
            'key_value_store_id','request_queue_id']<>'{}'::jsonb THEN
          RAISE EXCEPTION 'CONTACTS_RUN_INVALID'; END IF;
        FOREACH item IN ARRAY ARRAY['run_id','dataset_id','build_id','provider_actor_id',
          'key_value_store_id','request_queue_id'] LOOP
          IF jsonb_typeof(p_metadata->item) IS DISTINCT FROM 'string'
            OR p_metadata->>item !~ '^[A-Za-z0-9_-]{1,64}$' THEN RAISE EXCEPTION 'CONTACTS_RUN_INVALID'; END IF;
        END LOOP;
        IF p_metadata->>'build_number' !~ '^[0-9]+[.][0-9]+[.][0-9]+$'
          OR e.field_mask IS DISTINCT FROM 'apify-place-contacts:'||(p_metadata->>'build_number') THEN
          RAISE EXCEPTION 'CONTACTS_RUN_INVALID'; END IF;
        SELECT metadata INTO prior FROM public.reference_contacts_runs
          WHERE tenant_id=t AND business_id=p_business AND effect_id=p_effect;
        IF FOUND THEN
          IF prior IS DISTINCT FROM p_metadata THEN RAISE EXCEPTION 'CONTACTS_RUN_CONFLICT'; END IF;
          RETURN;
        END IF;
        INSERT INTO public.reference_contacts_runs(tenant_id,business_id,effect_id,actor_id,run_id,metadata)
          VALUES(t,p_business,p_effect,a,p_metadata->>'run_id',p_metadata);
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_effect,'reference.contacts_run_recorded',p_effect);
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(gen_random_uuid(),t,'reference.contacts_run_recorded',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_effect::text));
      END $$""")
    op.execute("""CREATE FUNCTION public.reference_contacts_load_run(p_business uuid,p_effect uuid) RETURNS jsonb
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;result jsonb;
      BEGIN
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        SELECT jsonb_build_object('metadata',r.metadata,'executor_token',e.executor_token,
          'reported_cost_usd_micros',r.reported_cost_usd_micros) INTO result
          FROM public.reference_contacts_runs r JOIN public.reference_provider_effects e
            ON (e.tenant_id,e.business_id,e.id)=(r.tenant_id,r.business_id,r.effect_id)
          WHERE r.tenant_id=t AND r.business_id=p_business AND r.effect_id=p_effect AND r.actor_id=a;
        RETURN result;
      END $$""")
    op.execute("""CREATE FUNCTION public.reference_contacts_record_cost(
      p_business uuid,p_effect uuid,p_token uuid,p_run text,p_actual bigint) RETURNS void
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;
        e public.reference_provider_effects%ROWTYPE;r public.reference_cost_reservations%ROWTYPE;
        old_cost bigint;changed integer;
      BEGIN
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_effect AND provider='apify' FOR UPDATE;
        IF e.id IS NULL OR e.executor_token IS DISTINCT FROM p_token
          OR e.state NOT IN ('running','uncertain','completed_published','failed_definitive') THEN
          RAISE EXCEPTION 'CONTACTS_EXECUTOR_FENCE_INVALID'; END IF;
        SELECT reported_cost_usd_micros INTO old_cost FROM public.reference_contacts_runs
          WHERE tenant_id=t AND business_id=p_business AND effect_id=p_effect AND run_id=p_run FOR UPDATE;
        IF NOT FOUND THEN RAISE EXCEPTION 'CONTACTS_RUN_INVALID'; END IF;
        SELECT * INTO r FROM public.reference_cost_reservations WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND effect_id=p_effect AND provider='apify' FOR UPDATE;
        IF r.id IS NULL OR p_actual IS NULL OR p_actual<0 OR p_actual>r.reserved_usd_micros THEN
          RAISE EXCEPTION 'CONTACTS_RECEIPT_INVALID'; END IF;
        IF old_cost IS NOT NULL THEN
          IF old_cost IS DISTINCT FROM p_actual OR r.state<>'completed' OR r.actual_usd_micros<>p_actual THEN
            RAISE EXCEPTION 'CONTACTS_RECEIPT_CONFLICT'; END IF;
          RETURN;
        END IF;
        IF r.state NOT IN ('claimed','uncertain') THEN RAISE EXCEPTION 'CONTACTS_RECEIPT_CONFLICT'; END IF;
        UPDATE public.reference_provider_pilots
          SET reserved_usd_micros=reserved_usd_micros-r.reserved_usd_micros+p_actual
          WHERE id=r.pilot_id AND reserved_usd_micros>=r.reserved_usd_micros;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_MONTHLY_INCONSISTENT'; END IF;
        UPDATE public.reference_cost_monthly
          SET committed_usd_micros=committed_usd_micros-r.reserved_usd_micros+p_actual,
              outstanding_usd_micros=outstanding_usd_micros-r.reserved_usd_micros
          WHERE month=r.month AND provider IN ('all','apify')
            AND committed_usd_micros>=r.reserved_usd_micros AND outstanding_usd_micros>=r.reserved_usd_micros;
        GET DIAGNOSTICS changed=ROW_COUNT;
        IF changed<>2 THEN RAISE EXCEPTION 'REFERENCE_MONTHLY_INCONSISTENT'; END IF;
        UPDATE public.reference_cost_reservations SET state='completed',actual_usd_micros=p_actual,
          updated_at=clock_timestamp() WHERE tenant_id=t AND id=r.id;
        UPDATE public.reference_contacts_runs SET reported_cost_usd_micros=p_actual
          WHERE tenant_id=t AND business_id=p_business AND effect_id=p_effect;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_effect,'reference.contacts_cost_reported',r.id);
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(gen_random_uuid(),t,'reference.provider_cost_changed',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_effect::text));
      END $$""")
    for signature in (
        "reference_contacts_record_run(uuid,uuid,uuid,jsonb)",
        "reference_contacts_load_run(uuid,uuid)",
        "reference_contacts_record_cost(uuid,uuid,uuid,text,bigint)",
    ):
        op.execute(f"ALTER FUNCTION public.{signature} OWNER TO {_ROLE}")
        op.execute(f"REVOKE ALL ON FUNCTION public.{signature} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION public.{signature} TO meu_braco_direito_correlator")


def downgrade():
    op.execute("LOCK TABLE reference_contacts_runs IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security=off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_contacts_runs)
      OR EXISTS(SELECT 1 FROM outbox_events WHERE event_type='reference.contacts_run_recorded') THEN
      RAISE EXCEPTION 'CONTACTS_RUNS_REQUIRE_FORWARD_RECOVERY'; END IF; END $$""")
    op.execute("SET LOCAL row_security=on")
    op.execute("DROP FUNCTION public.reference_contacts_record_cost(uuid,uuid,uuid,text,bigint)")
    op.execute("DROP FUNCTION public.reference_contacts_load_run(uuid,uuid)")
    op.execute("DROP FUNCTION public.reference_contacts_record_run(uuid,uuid,uuid,jsonb)")
    op.execute("DROP TABLE reference_contacts_runs")
    op.execute("DROP POLICY contacts_run_event ON outbox_events")
    # Replace the extra alternative by an already allowed event, restoring the
    # accepted set without depending on another migration's constraint text.
    op.execute("""DO $$ DECLARE expression text; BEGIN
      SELECT replace(pg_get_expr(conbin,conrelid),
        '''reference.contacts_run_recorded''::text','''reference.provider_effect_completed''::text')
        INTO expression FROM pg_constraint WHERE conrelid='public.outbox_events'::regclass
          AND conname='outbox_events_event_type_check';
      ALTER TABLE public.outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE public.outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK (' ||
        expression || ')';
    END $$""")
