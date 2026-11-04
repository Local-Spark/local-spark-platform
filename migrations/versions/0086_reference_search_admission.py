"""Private real-search cycle and admission, without provider dispatch."""

from alembic import op

revision = "0086_reference_search_admission"
down_revision = "0085_reference_claim_event_fence"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE reference_real_cycles (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,id uuid NOT NULL,
      confirmed_at timestamptz,locked_until timestamptz,
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(tenant_id,business_id,id),
      CHECK((confirmed_at IS NULL)=(locked_until IS NULL)),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("""CREATE TABLE reference_real_heads (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,cycle_id uuid,
      PRIMARY KEY(tenant_id,business_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id),
      FOREIGN KEY(tenant_id,business_id,cycle_id) REFERENCES reference_real_cycles(tenant_id,business_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    for table in ("reference_real_cycles", "reference_real_heads"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY owner_read ON {table} FOR SELECT TO meu_braco_direito_app "
            f"USING(tenant_id={tenant} AND {owner})"
        )
        op.execute(
            f"CREATE POLICY ledger_access ON {table} TO meu_braco_direito_reference_ledger "
            f"USING(tenant_id={tenant}) WITH CHECK(tenant_id={tenant})"
        )
        op.execute(f"GRANT SELECT ON {table} TO meu_braco_direito_app")
    op.execute("GRANT SELECT,INSERT ON reference_real_cycles TO meu_braco_direito_reference_ledger")
    op.execute("GRANT SELECT,INSERT,UPDATE(cycle_id) ON reference_real_heads TO meu_braco_direito_reference_ledger")
    op.execute("""ALTER TABLE reference_provider_searches ADD COLUMN cycle_id uuid,
      ADD COLUMN radius_km smallint CHECK(radius_km IN (5,20,50)), ADD COLUMN request_event_id uuid,
      ADD COLUMN identity_key_version text CHECK(identity_key_version ~ '^[a-zA-Z0-9_.-]{1,64}$'),
      ADD COLUMN radius_occupied boolean NOT NULL DEFAULT true,
      ADD COLUMN cancel_operation_id uuid, ADD COLUMN cancel_event_id uuid,
      ADD CHECK((cycle_id IS NULL)=(radius_km IS NULL)),
      ADD CHECK((cycle_id IS NULL)=(identity_key_version IS NULL)),
      ADD CHECK((cancel_operation_id IS NULL)=(cancel_event_id IS NULL)),
      ADD CHECK(radius_occupied OR (state='cancelled' AND cancel_operation_id IS NOT NULL)),
      ADD FOREIGN KEY(tenant_id,business_id,cycle_id) REFERENCES reference_real_cycles(tenant_id,business_id,id),
      ADD FOREIGN KEY(tenant_id,request_event_id) REFERENCES outbox_events(tenant_id,id),
      ADD FOREIGN KEY(tenant_id,cancel_event_id) REFERENCES outbox_events(tenant_id,id)""")
    op.execute("""CREATE UNIQUE INDEX reference_real_one_radius_per_cycle
      ON reference_provider_searches(tenant_id,business_id,cycle_id,radius_km)
      WHERE cycle_id IS NOT NULL AND radius_occupied""")
    op.execute("GRANT INSERT ON reference_provider_searches TO meu_braco_direito_reference_ledger")
    op.execute("""GRANT UPDATE(radius_occupied,cancel_operation_id,cancel_event_id)
      ON reference_provider_searches TO meu_braco_direito_reference_ledger""")
    op.execute(f"""CREATE POLICY reference_admission_context_head ON business_context_heads
      FOR SELECT TO meu_braco_direito_reference_ledger USING(tenant_id={tenant})""")
    op.execute(f"""CREATE POLICY reference_admission_context_head_lock ON business_context_heads
      FOR UPDATE TO meu_braco_direito_reference_ledger USING(tenant_id={tenant}) WITH CHECK(tenant_id={tenant})""")
    op.execute(f"""CREATE POLICY reference_admission_context_version ON business_context_versions
      FOR SELECT TO meu_braco_direito_reference_ledger USING(tenant_id={tenant})""")
    op.execute(
        "GRANT SELECT(tenant_id,business_id,version),UPDATE(version) ON business_context_heads "
        "TO meu_braco_direito_reference_ledger"
    )
    op.execute(
        "GRANT SELECT(tenant_id,business_id,version,document) ON business_context_versions "
        "TO meu_braco_direito_reference_ledger"
    )
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed',
       'reference.provider_effect_requested','reference.provider_cost_changed','reference.provider_effect_completed',
       'reference.provider_search_requested','reference.provider_search_cancelled'))""")
    op.execute(f"""CREATE POLICY reference_provider_search_event_emit ON outbox_events FOR INSERT
      TO meu_braco_direito_reference_ledger WITH CHECK(tenant_id={tenant}
        AND event_type IN ('reference.provider_search_requested','reference.provider_search_cancelled')
        AND payload->>'actor_id'={actor}::text)""")
    op.execute("""CREATE FUNCTION public.reference_admit_provider_search(
      p_business uuid,p_search uuid,p_operation uuid,p_event uuid,p_mac text,p_key text,
      p_context bigint,p_radius smallint)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        s public.reference_provider_searches%ROWTYPE; head public.reference_real_heads%ROWTYPE;
        cycle public.reference_real_cycles%ROWTYPE; doc jsonb; version bigint;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_search IS NULL OR p_operation IS NULL
          OR p_event IS NULL OR p_mac IS NULL OR p_mac !~ '^[0-9a-f]{64}$'
          OR p_key IS NULL OR p_key !~ '^[a-zA-Z0-9_.-]{1,64}$'
          OR p_context IS NULL OR p_context<1 OR p_radius IS NULL OR p_radius NOT IN (5,20,50) THEN
          RAISE EXCEPTION 'REFERENCE_SEARCH_ADMISSION_INVALID'; END IF;
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        INSERT INTO public.reference_real_heads(tenant_id,business_id) VALUES(t,p_business) ON CONFLICT DO NOTHING;
        SELECT * INTO head FROM public.reference_real_heads WHERE tenant_id=t AND business_id=p_business FOR UPDATE;
        SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
          AND operation_id=p_operation;
        IF FOUND THEN
          IF s.actor_id IS DISTINCT FROM a OR s.id IS DISTINCT FROM p_search OR s.request_mac IS DISTINCT FROM p_mac
            OR s.context_version IS DISTINCT FROM p_context OR s.radius_km IS DISTINCT FROM p_radius
            OR s.identity_key_version IS DISTINCT FROM p_key
            OR s.request_event_id IS NULL THEN RAISE EXCEPTION 'REFERENCE_SEARCH_ADMISSION_CONFLICT'; END IF;
          RETURN jsonb_build_object('search_id',s.id,'cycle_id',s.cycle_id,'event_id',s.request_event_id,
            'state',s.state,'created',false);
        END IF;
        SELECT h.version,v.document INTO version,doc FROM public.business_context_heads h
          JOIN public.business_context_versions v
            ON (v.tenant_id,v.business_id,v.version)=(h.tenant_id,h.business_id,h.version)
          WHERE h.tenant_id=t AND h.business_id=p_business FOR SHARE OF h;
        IF NOT FOUND OR version IS DISTINCT FROM p_context
          OR doc#>>'{preferences,reference_search,scope}' IS DISTINCT FROM 'local'
          OR doc#>'{preferences,reference_search,radius_km}' IS DISTINCT FROM to_jsonb(p_radius)
          OR doc#>>'{preferences,reference_search,origin,method}' IS DISTINCT FROM 'device'
          OR jsonb_typeof(doc#>'{preferences,reference_search,origin,coordinates}') IS DISTINCT FROM 'object'
          OR jsonb_typeof(doc#>'{preferences,business_terms}') IS DISTINCT FROM 'array'
          OR jsonb_array_length(doc#>'{preferences,business_terms}')=0 THEN
          RAISE EXCEPTION 'REFERENCE_SEARCH_CONTEXT_INVALID'; END IF;
        IF head.cycle_id IS NOT NULL THEN
          SELECT * INTO cycle FROM public.reference_real_cycles
            WHERE tenant_id=t AND business_id=p_business AND id=head.cycle_id;
        END IF;
        IF head.cycle_id IS NULL OR (cycle.locked_until IS NOT NULL AND cycle.locked_until<=clock_timestamp()) THEN
          cycle.id := gen_random_uuid();
          INSERT INTO public.reference_real_cycles(tenant_id,business_id,id) VALUES(t,p_business,cycle.id);
          UPDATE public.reference_real_heads SET cycle_id=cycle.id WHERE tenant_id=t AND business_id=p_business;
        END IF;
        IF EXISTS(SELECT 1 FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
          AND cycle_id=cycle.id AND radius_km=p_radius AND radius_occupied) THEN
          RAISE EXCEPTION 'REFERENCE_RADIUS_ALREADY_SEARCHED'; END IF;
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(p_event,t,'reference.provider_search_requested',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_operation::text));
        INSERT INTO public.reference_provider_searches
          (id,tenant_id,business_id,actor_id,operation_id,context_version,request_mac,state,cycle_id,radius_km,
           request_event_id,identity_key_version)
          VALUES(p_search,t,p_business,a,p_operation,p_context,p_mac,'pending',cycle.id,p_radius,p_event,p_key);
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_operation,'reference.provider_search_admitted',p_search);
        RETURN jsonb_build_object('search_id',p_search,'cycle_id',cycle.id,'event_id',p_event,
          'state','pending','created',true);
      END $$""")
    op.execute(
        "ALTER FUNCTION public.reference_admit_provider_search(uuid,uuid,uuid,uuid,text,text,bigint,smallint) "
        "OWNER TO meu_braco_direito_reference_ledger"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION public.reference_admit_provider_search(uuid,uuid,uuid,uuid,text,text,bigint,smallint) "
        "FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION public.reference_admit_provider_search("
        "uuid,uuid,uuid,uuid,text,text,bigint,smallint) "
        "TO meu_braco_direito_app"
    )
    op.execute("""CREATE FUNCTION public.reference_cancel_unstarted_search(
      p_business uuid,p_search uuid,p_operation uuid)
      RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        s public.reference_provider_searches%ROWTYPE; event_id uuid;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_search IS NULL OR p_operation IS NULL THEN
          RAISE EXCEPTION 'REFERENCE_SEARCH_CANCELLATION_INVALID'; END IF;
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_search FOR UPDATE;
        IF NOT FOUND OR s.cycle_id IS NULL THEN RAISE EXCEPTION 'REFERENCE_SEARCH_CANCELLATION_INVALID'; END IF;
        IF s.cancel_operation_id IS NOT NULL THEN
          IF s.cancel_operation_id IS DISTINCT FROM p_operation OR s.state<>'cancelled' OR s.radius_occupied THEN
            RAISE EXCEPTION 'REFERENCE_SEARCH_CANCELLATION_CONFLICT'; END IF;
          RETURN s.cancel_event_id;
        END IF;
        IF s.state<>'pending' OR EXISTS(SELECT 1 FROM public.reference_provider_effects
          WHERE tenant_id=t AND business_id=p_business AND search_id=p_search) THEN
          RAISE EXCEPTION 'REFERENCE_SEARCH_ALREADY_STARTED'; END IF;
        event_id := gen_random_uuid();
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(event_id,t,'reference.provider_search_cancelled',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_operation::text));
        UPDATE public.reference_provider_searches SET state='cancelled',radius_occupied=false,
          cancel_operation_id=p_operation,cancel_event_id=event_id
          WHERE tenant_id=t AND business_id=p_business AND id=p_search;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_operation,'reference.provider_search_cancelled',p_search);
        RETURN event_id;
      END $$""")
    op.execute(
        "ALTER FUNCTION public.reference_cancel_unstarted_search(uuid,uuid,uuid) "
        "OWNER TO meu_braco_direito_reference_ledger"
    )
    op.execute("REVOKE ALL ON FUNCTION public.reference_cancel_unstarted_search(uuid,uuid,uuid) FROM PUBLIC")
    # No runtime grant: a future trusted recovery coordinator must prove when
    # cancellation is appropriate and make the choice visible to the caller.


def downgrade():
    op.execute("LOCK TABLE reference_real_cycles,reference_provider_searches,outbox_events IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM reference_real_cycles) OR EXISTS(SELECT 1 FROM reference_provider_searches
        WHERE cycle_id IS NOT NULL OR request_event_id IS NOT NULL) OR EXISTS(SELECT 1 FROM outbox_events
        WHERE event_type IN ('reference.provider_search_requested','reference.provider_search_cancelled')) THEN
        RAISE EXCEPTION 'REFERENCE_SEARCH_ADMISSION_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF;
    END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("DROP FUNCTION public.reference_cancel_unstarted_search(uuid,uuid,uuid)")
    op.execute("DROP FUNCTION public.reference_admit_provider_search(uuid,uuid,uuid,uuid,text,text,bigint,smallint)")
    op.execute("DROP POLICY reference_provider_search_event_emit ON outbox_events")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed',
       'reference.provider_effect_requested','reference.provider_cost_changed','reference.provider_effect_completed'))""")
    op.execute(
        "REVOKE SELECT(tenant_id,business_id,version,document) ON business_context_versions "
        "FROM meu_braco_direito_reference_ledger"
    )
    op.execute(
        "REVOKE SELECT(tenant_id,business_id,version),UPDATE(version) ON business_context_heads "
        "FROM meu_braco_direito_reference_ledger"
    )
    op.execute("DROP POLICY reference_admission_context_version ON business_context_versions")
    op.execute("DROP POLICY reference_admission_context_head_lock ON business_context_heads")
    op.execute("DROP POLICY reference_admission_context_head ON business_context_heads")
    op.execute("REVOKE INSERT ON reference_provider_searches FROM meu_braco_direito_reference_ledger")
    op.execute("""REVOKE UPDATE(radius_occupied,cancel_operation_id,cancel_event_id)
      ON reference_provider_searches FROM meu_braco_direito_reference_ledger""")
    op.execute("DROP INDEX reference_real_one_radius_per_cycle")
    op.execute(
        "ALTER TABLE reference_provider_searches DROP COLUMN cycle_id, DROP COLUMN radius_km, "
        "DROP COLUMN request_event_id, DROP COLUMN identity_key_version, DROP COLUMN radius_occupied, "
        "DROP COLUMN cancel_operation_id, DROP COLUMN cancel_event_id"
    )
    op.execute("DROP TABLE reference_real_heads,reference_real_cycles")
