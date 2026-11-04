"""Resolve the explicitly saved shop address through fenced, costed jobs."""

from alembic import op

revision = "0103_business_geocoding"
down_revision = "0102_shared_search_budget"
branch_labels = None
depends_on = None

_ROLE = "meu_braco_direito_reference_ledger"
_CLAIM = "uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,bigint"
_EVENTS = (
    "'business.address_geocode_requested','business.address_geocode_completed','business.address_location_confirmed'"
)


def _function(sql, signature, role):
    op.execute(sql)
    op.execute(f"ALTER FUNCTION public.{signature} OWNER TO {_ROLE}")
    op.execute(f"REVOKE ALL ON FUNCTION public.{signature} FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION public.{signature} TO {role}")


def upgrade():
    t = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    a = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"tenant_id={t} AND EXISTS(SELECT 1 FROM memberships m JOIN user_accounts u ON u.id=m.actor_id "
        f"WHERE m.tenant_id={t} AND m.actor_id={a} AND m.role='owner' AND m.active AND u.active)"
    )
    op.execute("""CREATE TABLE business_address_geocodes (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,id uuid NOT NULL,actor_id uuid NOT NULL,
      address_version bigint NOT NULL,context_version bigint NOT NULL,operation_id uuid NOT NULL,
      event_id uuid NOT NULL,effect_id uuid NOT NULL,origin_id uuid NOT NULL,
      binding_mac char(64) NOT NULL CHECK(binding_mac ~ '^[0-9a-f]{64}$'),
      status text NOT NULL DEFAULT 'pending' CHECK(status IN
        ('pending','resolved','confirmation_required','not_found','uncertain')),
      candidates jsonb NOT NULL DEFAULT '[]'::jsonb CHECK(jsonb_typeof(candidates)='array'
        AND jsonb_array_length(candidates)<=100),
      chosen_candidate uuid,confirmation_operation uuid,confirmation_actor uuid,
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),completed_at timestamptz,
      PRIMARY KEY(tenant_id,business_id,id),UNIQUE(tenant_id,business_id,address_version),
      UNIQUE(tenant_id,business_id,operation_id),UNIQUE(tenant_id,business_id,effect_id),
      UNIQUE(tenant_id,business_id,origin_id),
      FOREIGN KEY(tenant_id,business_id,address_version)
        REFERENCES business_address_versions(tenant_id,business_id,version),
      FOREIGN KEY(tenant_id,business_id,context_version)
        REFERENCES business_context_versions(tenant_id,business_id,version),
      FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id),
      FOREIGN KEY(tenant_id,business_id,effect_id) REFERENCES reference_geocode_effects(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,origin_id) REFERENCES reference_geocode_origins(tenant_id,business_id,id),
      CHECK((status='resolved')=(chosen_candidate IS NOT NULL)),
      CHECK((confirmation_operation IS NULL)=(confirmation_actor IS NULL)))""")
    op.execute("ALTER TABLE business_address_geocodes ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE business_address_geocodes FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY address_geocode_owner ON business_address_geocodes FOR SELECT "
        f"TO meu_braco_direito_app USING({owner})"
    )
    op.execute(
        f"CREATE POLICY address_geocode_ledger ON business_address_geocodes TO {_ROLE} "
        f"USING(tenant_id={t}) WITH CHECK(tenant_id={t})"
    )
    op.execute(f"GRANT SELECT,INSERT,UPDATE ON business_address_geocodes TO {_ROLE}")
    op.execute(
        "GRANT SELECT(tenant_id,business_id,id,address_version,status,candidates,chosen_candidate) "
        "ON business_address_geocodes TO meu_braco_direito_app"
    )
    for table in ("business_address_heads", "business_address_versions"):
        op.execute(
            f"CREATE POLICY address_geocode_ledger ON {table} TO {_ROLE} USING(tenant_id={t}) WITH CHECK(tenant_id={t})"
        )
        op.execute(f"GRANT SELECT ON {table} TO {_ROLE}")
    op.execute(f"GRANT UPDATE(version) ON business_address_heads TO {_ROLE}")
    op.execute(f"GRANT INSERT ON reference_geocode_origins,reference_geocode_effects TO {_ROLE}")
    op.execute(f"""DO $$ DECLARE d text; BEGIN
      SELECT pg_get_constraintdef(oid) INTO d FROM pg_constraint
        WHERE conrelid='outbox_events'::regclass AND conname='outbox_events_event_type_check';
      EXECUTE 'ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check';
      EXECUTE 'ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check ' ||
        replace(d,'CHECK (','CHECK (event_type IN ({_EVENTS.replace(chr(39), chr(39) * 2)}) OR ');
      END $$""")
    op.execute(
        f"CREATE POLICY address_geocode_events ON outbox_events TO {_ROLE} "
        f"USING(tenant_id={t} AND event_type IN ({_EVENTS})) "
        f"WITH CHECK(tenant_id={t} AND event_type IN ({_EVENTS}) AND payload->>'actor_id'={a}::text)"
    )
    _function(
        _REQUEST,
        "business_address_geocode_request(uuid,uuid,bigint,bigint,uuid,uuid,uuid,uuid,uuid,text,text,text,text,\
text,text,bigint)",
        "meu_braco_direito_app",
    )
    _function(_LOAD, "business_address_geocode_load(uuid,uuid,uuid)", "meu_braco_direito_correlator")
    _function(_CLAIM_SQL, f"business_address_geocode_claim({_CLAIM})", "meu_braco_direito_correlator")
    _function(_UNCERTAIN, "business_address_geocode_uncertain(uuid,uuid)", "meu_braco_direito_correlator")
    _function(_COMPLETE, "business_address_geocode_complete(uuid,uuid,uuid,jsonb,uuid)", "meu_braco_direito_correlator")
    _function(_CONFIRM, "business_address_geocode_confirm(uuid,uuid,uuid,uuid,bigint)", "meu_braco_direito_app")
    _identity_upgrade()


_REQUEST = """CREATE FUNCTION public.business_address_geocode_request(
  p_business uuid,p_operation uuid,p_address bigint,p_context bigint,p_id uuid,p_origin uuid,p_effect uuid,
  p_event uuid,p_pilot uuid,p_mac text,p_binding text,p_key text,p_tariff text,p_credential text,p_class\
 text,p_amount bigint)
  RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
    prior public.business_address_geocodes%ROWTYPE; effect_event uuid;
  BEGIN
    IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'BUSINESS_OWNER_REQUIRED'; END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended('business-address:'||t::text||':'||p_business::text,100));
    SELECT * INTO prior FROM public.business_address_geocodes
      WHERE tenant_id=t AND business_id=p_business AND operation_id=p_operation;
    IF FOUND THEN
      IF prior.actor_id IS DISTINCT FROM a OR prior.address_version IS DISTINCT FROM p_address THEN
        RAISE EXCEPTION 'BUSINESS_ADDRESS_OPERATION_CONFLICT'; END IF;
      RETURN prior.id;
    END IF;
    PERFORM 1 FROM public.business_address_heads WHERE tenant_id=t AND business_id=p_business AND version=p_address;
    IF NOT FOUND THEN RAISE EXCEPTION 'BUSINESS_ADDRESS_VERSION_CONFLICT'; END IF;
    SELECT * INTO prior FROM public.business_address_geocodes
      WHERE tenant_id=t AND business_id=p_business AND address_version=p_address;
    IF FOUND THEN RETURN prior.id; END IF;
    PERFORM 1 FROM public.business_context_heads WHERE tenant_id=t AND business_id=p_business AND version=p_context
      FOR SHARE;
    IF NOT FOUND THEN RAISE EXCEPTION 'BUSINESS_ADDRESS_CONTEXT_REQUIRED'; END IF;
    effect_event := gen_random_uuid();
    INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
      VALUES(effect_event,t,'reference.provider_effect_requested',jsonb_build_object(
        'business_id',p_business::text,'actor_id',a::text,'operation_id',p_effect::text)),
        (p_event,t,'business.address_geocode_requested',jsonb_build_object(
        'business_id',p_business::text,'actor_id',a::text,'operation_id',p_id::text));
    INSERT INTO public.reference_geocode_origins(tenant_id,business_id,id,actor_id,context_version)
      VALUES(t,p_business,p_origin,a,p_context);
    INSERT INTO public.reference_geocode_effects(tenant_id,business_id,id,actor_id,origin_id,pilot_id,event_id,
      request_mac,key_version,tariff_version,credential_version,charge_class,reserved_usd_micros,state)
      VALUES(t,p_business,p_effect,a,p_origin,p_pilot,effect_event,p_mac,p_key,p_tariff,p_credential,p_class,p_\
amount,'pending');
    INSERT INTO public.business_address_geocodes(tenant_id,business_id,id,actor_id,address_version,context_version,
      operation_id,event_id,effect_id,origin_id,binding_mac)
      VALUES(t,p_business,p_id,a,p_address,p_context,p_operation,p_event,p_effect,p_origin,p_binding);
    INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
      VALUES(t,a,p_operation,'business.address_geocode_requested',p_business);
    RETURN p_id;
  END $$"""

_LOAD = """CREATE FUNCTION public.business_address_geocode_load(p_business uuid,p_id uuid,p_event uuid)
  RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid := nullif(current_setting('app.actor_id',true),'')::uuid; result jsonb;
  BEGIN
    IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'BUSINESS_OWNER_REQUIRED'; END IF;
    SELECT jsonb_build_object('id',g.id,'address_version',g.address_version,'context_version',g.context_version,
      'origin_id',g.origin_id,'effect_id',g.effect_id,'effect_event_id',e.event_id,'pilot_id',e.pilot_id,
      'binding_mac',g.binding_mac,'key_version',e.key_version,'tariff_version',e.tariff_version,
      'credential_version',e.credential_version,'reserved_usd_micros',e.reserved_usd_micros,
      'request_mac',e.request_mac,'status',g.status,'effect_state',e.state,'executor_token',e.executor_token,'a\
ddress',v.address)
      INTO result FROM public.business_address_geocodes g JOIN public.reference_geocode_effects e
        ON (e.tenant_id,e.business_id,e.id)=(g.tenant_id,g.business_id,g.effect_id)
      JOIN public.business_address_versions v ON (v.tenant_id,v.business_id,v.version)=
        (g.tenant_id,g.business_id,g.address_version)
      JOIN public.outbox_events o ON (o.tenant_id,o.id)=(g.tenant_id,g.event_id)
      WHERE g.tenant_id=t AND g.business_id=p_business AND g.actor_id=a AND g.id=p_id AND g.event_id=p_event
        AND o.event_type='business.address_geocode_requested' AND o.payload=jsonb_build_object(
          'business_id',p_business::text,'actor_id',a::text,'operation_id',p_id::text);
    IF result IS NULL THEN RAISE EXCEPTION 'BUSINESS_ADDRESS_GEOCODE_EVENT_INVALID'; END IF;
    RETURN result;
  END $$"""

_CLAIM_SQL = """CREATE FUNCTION public.business_address_geocode_claim(
  p_business uuid,p_effect uuid,p_event uuid,p_origin uuid,p_pilot uuid,p_mac text,
  p_key text,p_tariff text,p_credential text,p_class text,p_amount bigint,p_context bigint)
  RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
  BEGIN
    IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'BUSINESS_OWNER_REQUIRED'; END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended('business-address:'||t::text||':'||p_business::text,100));
    PERFORM 1 FROM public.business_address_geocodes g JOIN public.business_address_heads h
      ON (h.tenant_id,h.business_id,h.version)=(g.tenant_id,g.business_id,g.address_version)
      WHERE g.tenant_id=t AND g.business_id=p_business AND g.effect_id=p_effect AND g.origin_id=p_origin
        AND g.actor_id=a AND g.context_version=p_context AND g.status='pending';
    IF NOT FOUND THEN RAISE EXCEPTION 'BUSINESS_ADDRESS_GEOCODE_STALE'; END IF;
    RETURN public.reference_geocode_claim_context_inner(p_business,p_effect,p_event,p_origin,p_pilot,p_mac,
      p_key,p_tariff,p_credential,p_class,p_amount,p_context);
  END $$"""

_UNCERTAIN = """CREATE FUNCTION public.business_address_geocode_uncertain(p_effect uuid,p_token uuid)
  RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
  BEGIN
    PERFORM 1 FROM public.business_address_geocodes WHERE tenant_id=t AND effect_id=p_effect AND actor_id=a;
    IF NOT FOUND THEN RAISE EXCEPTION 'BUSINESS_ADDRESS_GEOCODE_EVENT_INVALID'; END IF;
    PERFORM public.reference_geocode_uncertain(p_effect,p_token);
    UPDATE public.business_address_geocodes SET status='uncertain',completed_at=clock_timestamp()
      WHERE tenant_id=t AND effect_id=p_effect AND actor_id=a AND status='pending';
  END $$"""

_COMPLETE = """CREATE FUNCTION public.business_address_geocode_complete(
  p_business uuid,p_id uuid,p_token uuid,p_candidates jsonb,p_chosen uuid)
  RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
    g public.business_address_geocodes%ROWTYPE; c jsonb; result text;
  BEGIN
    IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'BUSINESS_OWNER_REQUIRED'; END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended('business-address:'||t::text||':'||p_business::text,100));
    SELECT * INTO g FROM public.business_address_geocodes
      WHERE tenant_id=t AND business_id=p_business AND id=p_id AND actor_id=a FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'BUSINESS_ADDRESS_GEOCODE_EVENT_INVALID'; END IF;
    PERFORM 1 FROM public.reference_geocode_effects WHERE tenant_id=t AND business_id=p_business
      AND id=g.effect_id AND executor_token=p_token AND state IN ('running','uncertain') FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_GEOCODE_FENCE_INVALID'; END IF;
    IF g.status<>'pending' THEN RETURN g.status; END IF;
    IF p_candidates IS NULL OR jsonb_typeof(p_candidates)<>'array' OR jsonb_array_length(p_candidates)>100 THEN
      RAISE EXCEPTION 'BUSINESS_ADDRESS_GEOCODE_RESULT_INVALID'; END IF;
    FOR c IN SELECT value FROM jsonb_array_elements(p_candidates) LOOP
      IF jsonb_typeof(c)<>'object' OR NOT c ?& ARRAY['id','latitude','longitude']
        OR c-ARRAY['id','latitude','longitude']<>'{}'::jsonb
        OR jsonb_typeof(c->'id')<>'string' OR (c->>'id')::uuid IS NULL
        OR jsonb_typeof(c->'latitude')<>'number' OR jsonb_typeof(c->'longitude')<>'number'
        OR (c->>'latitude')::numeric NOT BETWEEN -90 AND 90 OR (c->>'longitude')::numeric NOT BETWEEN -180 AND 180 THEN
        RAISE EXCEPTION 'BUSINESS_ADDRESS_GEOCODE_RESULT_INVALID'; END IF;
    END LOOP;
    IF (SELECT count(DISTINCT value->>'id') FROM jsonb_array_elements(p_candidates))<>jsonb_array_length(p_candidates)
      OR (p_chosen IS NOT NULL AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(p_candidates)
        WHERE value->>'id'=p_chosen::text)) THEN RAISE EXCEPTION 'BUSINESS_ADDRESS_GEOCODE_RESULT_INVALID'; END IF;
    result := CASE WHEN p_chosen IS NOT NULL THEN 'resolved' WHEN jsonb_array_length(p_candidates)=0
      THEN 'not_found' ELSE 'confirmation_required' END;
    -- A successful response proves a result, not the final supplier invoice.
    PERFORM public.reference_geocode_uncertain(g.effect_id,p_token);
    UPDATE public.business_address_geocodes SET status=result,candidates=p_candidates,chosen_candidate=p_chosen,
      completed_at=clock_timestamp() WHERE tenant_id=t AND business_id=p_business AND id=p_id;
    INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
      VALUES(t,a,p_id,'business.address_geocode_completed',p_business);
    INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
      VALUES(gen_random_uuid(),t,'business.address_geocode_completed',jsonb_build_object(
        'business_id',p_business::text,'actor_id',a::text,'operation_id',p_id::text));
    RETURN result;
  END $$"""

_CONFIRM = """CREATE FUNCTION public.business_address_geocode_confirm(
  p_business uuid,p_id uuid,p_operation uuid,p_candidate uuid,p_address bigint)
  RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
    g public.business_address_geocodes%ROWTYPE;
  BEGIN
    IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'BUSINESS_OWNER_REQUIRED'; END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended('business-address:'||t::text||':'||p_business::text,100));
    SELECT * INTO g FROM public.business_address_geocodes WHERE tenant_id=t AND business_id=p_business
      AND id=p_id AND address_version=p_address FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'BUSINESS_ADDRESS_GEOCODE_EVENT_INVALID'; END IF;
    IF g.confirmation_operation IS NOT NULL THEN
      IF g.confirmation_operation IS DISTINCT FROM p_operation OR g.confirmation_actor IS DISTINCT FROM a
        OR g.chosen_candidate IS DISTINCT FROM p_candidate THEN
        RAISE EXCEPTION 'BUSINESS_ADDRESS_OPERATION_CONFLICT'; END IF;
      RETURN;
    END IF;
    PERFORM 1 FROM public.business_address_heads WHERE tenant_id=t AND business_id=p_business AND version=p_address;
    IF NOT FOUND THEN RAISE EXCEPTION 'BUSINESS_ADDRESS_VERSION_CONFLICT'; END IF;
    IF p_operation IS NULL OR g.status<>'confirmation_required' OR p_candidate IS NULL OR NOT EXISTS(
      SELECT 1 FROM jsonb_array_elements(g.candidates) WHERE value->>'id'=p_candidate::text) THEN
      RAISE EXCEPTION 'BUSINESS_ADDRESS_GEOCODE_CONFIRMATION_INVALID'; END IF;
    UPDATE public.business_address_geocodes SET status='resolved',chosen_candidate=p_candidate,
      confirmation_actor=a,confirmation_operation=p_operation,candidates=(SELECT jsonb_agg(value)
        FROM jsonb_array_elements(g.candidates) WHERE value->>'id'=p_candidate::text) WHERE tenant_id=t AND\
 business_id=p_business AND id=p_id;
    INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
      VALUES(t,a,p_operation,'business.address_location_confirmed',p_business);
    INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
      VALUES(gen_random_uuid(),t,'business.address_location_confirmed',jsonb_build_object(
        'business_id',p_business::text,'actor_id',a::text,'operation_id',p_operation::text));
  END $$"""


def downgrade():
    op.execute("LOCK TABLE business_address_geocodes,reference_provider_searches IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security=off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM business_address_geocodes) OR
      EXISTS(SELECT 1 FROM reference_provider_searches WHERE business_identity_mac IS NOT NULL) THEN
      RAISE EXCEPTION 'BUSINESS_GEOCODING_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security=on")
    _identity_downgrade()
    for signature in (
        "business_address_geocode_confirm(uuid,uuid,uuid,uuid,bigint)",
        "business_address_geocode_complete(uuid,uuid,uuid,jsonb,uuid)",
        "business_address_geocode_uncertain(uuid,uuid)",
        f"business_address_geocode_claim({_CLAIM})",
        "business_address_geocode_load(uuid,uuid,uuid)",
        "business_address_geocode_request(uuid,uuid,bigint,bigint,uuid,uuid,uuid,uuid,uuid,text,text,text,text,\
text,text,bigint)",
    ):
        op.execute(f"DROP FUNCTION public.{signature}")
    op.execute("DROP POLICY address_geocode_events ON outbox_events")
    op.execute("DROP TABLE business_address_geocodes")
    op.execute(f"REVOKE INSERT ON reference_geocode_origins,reference_geocode_effects FROM {_ROLE}")
    for table in ("business_address_heads", "business_address_versions"):
        op.execute(f"DROP POLICY address_geocode_ledger ON {table}")
        op.execute(f"REVOKE SELECT ON {table} FROM {_ROLE}")
    op.execute(f"REVOKE UPDATE(version) ON business_address_heads FROM {_ROLE}")


_ADMISSION = """CREATE OR REPLACE FUNCTION public.reference_admit_provider_search(
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
          OR NOT ((doc#>>'{preferences,reference_search,origin,method}'='device'
            AND jsonb_typeof(doc#>'{preferences,reference_search,origin,coordinates}')='object') OR
            (doc#>>'{preferences,reference_search,origin,method}'='manual' AND EXISTS(
              SELECT 1 FROM public.business_address_heads ah JOIN public.business_address_versions av
                USING(tenant_id,business_id,version) JOIN public.business_address_geocodes ag
                ON (ag.tenant_id,ag.business_id,ag.address_version)=(ah.tenant_id,ah.business_id,ah.version)
                WHERE ah.tenant_id=t AND ah.business_id=p_business AND ag.status='resolved'
                AND av.address=jsonb_strip_nulls(doc#>'{preferences,reference_search,origin,address}'))))
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
      END $$"""

_CONTEXT_LOADER = """CREATE OR REPLACE FUNCTION public.reference_load_search_context(p_business uuid,p_search\
 uuid,p_event uuid)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        s public.reference_provider_searches%ROWTYPE; doc jsonb; point jsonb; version bigint;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_search IS NULL OR p_event IS NULL THEN
          RAISE EXCEPTION 'REFERENCE_CONTEXT_LOAD_INVALID'; END IF;
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        SELECT h.version,v.document INTO version,doc FROM public.business_context_heads h
          JOIN public.business_context_versions v
            ON (v.tenant_id,v.business_id,v.version)=(h.tenant_id,h.business_id,h.version)
          WHERE h.tenant_id=t AND h.business_id=p_business FOR SHARE OF h;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_CONTEXT_LOAD_INVALID'; END IF;
        SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_search AND state='pending' AND radius_occupied FOR SHARE;
        IF NOT FOUND OR s.cycle_id IS NULL OR s.request_event_id IS DISTINCT FROM p_event
          OR s.identity_key_version IS NULL OR NOT EXISTS(SELECT 1 FROM public.outbox_events o
            WHERE o.tenant_id=t AND o.id=p_event AND o.event_type='reference.provider_search_requested'
              AND o.payload=jsonb_build_object('business_id',p_business::text,'actor_id',a::text,
                'operation_id',s.operation_id::text)) THEN
          RAISE EXCEPTION 'REFERENCE_CONTEXT_LOAD_INVALID'; END IF;
        IF version IS DISTINCT FROM s.context_version
          OR doc#>>'{preferences,reference_search,scope}' IS DISTINCT FROM 'local'
          OR doc#>'{preferences,reference_search,radius_km}' IS DISTINCT FROM to_jsonb(s.radius_km)
          OR doc#>>'{preferences,reference_search,origin,method}' NOT IN ('device','manual')
          OR jsonb_typeof(doc#>'{preferences,business_terms}') IS DISTINCT FROM 'array' THEN
          RAISE EXCEPTION 'REFERENCE_CONTEXT_LOAD_INVALID'; END IF;
        PERFORM public.reference_assert_business_identity(p_business,p_search);
        IF doc#>>'{preferences,reference_search,origin,method}'='manual' THEN
          SELECT value INTO point FROM public.business_address_geocodes ag,
            LATERAL jsonb_array_elements(ag.candidates)
            WHERE ag.tenant_id=t AND ag.business_id=p_business AND ag.origin_id=s.geocode_origin_id
              AND ag.status='resolved' AND value->>'id'=ag.chosen_candidate::text;
          IF point IS NULL THEN RAISE EXCEPTION 'REFERENCE_CONTEXT_LOAD_INVALID'; END IF;
        ELSE
          point := doc#>'{preferences,reference_search,origin,coordinates}';
          IF point->'confirmed' IS DISTINCT FROM 'true'::jsonb THEN
            RAISE EXCEPTION 'REFERENCE_CONTEXT_LOAD_INVALID'; END IF;
        END IF;
        RETURN jsonb_build_object('operation_id',s.operation_id,'context_version',s.context_version,
          'radius_km',s.radius_km,'identity_key_version',s.identity_key_version,'request_mac',s.request_mac,
          'latitude',point->'latitude',
          'longitude',point->'longitude',
          'business_terms',doc#>'{preferences,business_terms}',
          'business_description',doc#>'{preferences,business_characteristics}');
      END $$"""

_PREPARE_IDENTITY = """CREATE FUNCTION public.reference_prepare_business_identity(p_business uuid)
  RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
    own_name text;own_row bigint;av bigint;addr jsonb;doc jsonb;cv bigint;origin uuid;
  BEGIN
    IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
    INSERT INTO public.reference_real_heads(tenant_id,business_id) VALUES(t,p_business) ON CONFLICT DO NOTHING;
    PERFORM 1 FROM public.reference_real_heads WHERE tenant_id=t AND business_id=p_business FOR UPDATE;
    SELECT h.version,v.document INTO cv,doc FROM public.business_context_heads h
      JOIN public.business_context_versions v USING(tenant_id,business_id,version)
      WHERE h.tenant_id=t AND h.business_id=p_business FOR SHARE OF h;
    IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_SEARCH_CONTEXT_INVALID'; END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended('business-address:'||t::text||':'||p_business::text,100));
    SELECT name,row_version INTO own_name,own_row FROM public.businesses
      WHERE tenant_id=t AND id=p_business FOR SHARE;
    SELECT h.version,v.address INTO av,addr FROM public.business_address_heads h
      JOIN public.business_address_versions v USING(tenant_id,business_id,version)
      WHERE h.tenant_id=t AND h.business_id=p_business;
    IF own_name IS NULL OR av IS NULL THEN RAISE EXCEPTION 'REFERENCE_BUSINESS_ADDRESS_REQUIRED'; END IF;
    IF doc#>>'{preferences,reference_search,origin,method}'='manual' THEN
      SELECT origin_id INTO origin FROM public.business_address_geocodes
        WHERE tenant_id=t AND business_id=p_business AND address_version=av AND status='resolved';
      IF origin IS NULL OR addr IS DISTINCT FROM\
 jsonb_strip_nulls(doc#>'{preferences,reference_search,origin,address}') THEN
        RAISE EXCEPTION 'REFERENCE_BUSINESS_LOCATION_REQUIRED'; END IF;
    END IF;
    RETURN jsonb_build_object('name',own_name,'row_version',own_row,'address_version',av,'address',addr,
      'location_version',CASE WHEN origin IS NULL THEN NULL ELSE av END,'origin_id',origin,'context_version',cv);
  END $$"""

_BOUND_ADMISSION = """CREATE FUNCTION public.reference_admit_bound_search(
  p_business uuid,p_search uuid,p_operation uuid,p_event uuid,p_mac text,p_key text,p_context bigint,p_radius smallint,
  p_identity text,p_name text,p_row bigint,p_address bigint,p_location bigint,p_origin uuid)
  RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid := nullif(current_setting('app.actor_id',true),'')::uuid; current_identity jsonb; result jsonb;
    s public.reference_provider_searches%ROWTYPE;
  BEGIN
    current_identity := public.reference_prepare_business_identity(p_business);
    IF (current_identity->>'context_version')::bigint IS DISTINCT FROM p_context THEN
      RAISE EXCEPTION 'REFERENCE_SEARCH_CONTEXT_INVALID'; END IF;
    IF p_identity IS NULL OR p_identity !~ '^[0-9a-f]{64}$'
      OR current_identity->>'name' IS DISTINCT FROM p_name
      OR (current_identity->>'row_version')::bigint IS DISTINCT FROM p_row
      OR (current_identity->>'address_version')::bigint IS DISTINCT FROM p_address
      OR (current_identity->>'location_version')::bigint IS DISTINCT FROM p_location
      OR (current_identity->>'origin_id')::uuid IS DISTINCT FROM p_origin THEN
      RAISE EXCEPTION 'REFERENCE_BUSINESS_IDENTITY_STALE'; END IF;
    result :=\
 public.reference_admit_provider_search(p_business,p_search,p_operation,p_event,p_mac,p_key,p_context,p_radius);
    SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
      AND id=p_search AND actor_id=a FOR UPDATE;
    IF (result->>'created')::boolean THEN
      UPDATE public.reference_provider_searches SET business_name=p_name,business_row_version=p_row,
        business_address_version=p_address,business_location_version=p_location,business_identity_mac=p_identity,
        geocode_origin_id=p_origin WHERE tenant_id=t AND business_id=p_business AND id=p_search;
    ELSIF s.business_identity_mac IS DISTINCT FROM p_identity OR s.business_name IS DISTINCT FROM p_name
      OR s.business_address_version IS DISTINCT FROM p_address OR s.geocode_origin_id IS DISTINCT FROM p_origin THEN
      RAISE EXCEPTION 'REFERENCE_BUSINESS_IDENTITY_STALE';
    END IF;
    RETURN result;
  END $$"""

_ASSERT_IDENTITY = """CREATE FUNCTION public.reference_assert_business_identity(p_business uuid,p_search uuid)
  RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid := nullif(current_setting('app.actor_id',true),'')::uuid; i jsonb;
    s public.reference_provider_searches%ROWTYPE;
  BEGIN
    i := public.reference_prepare_business_identity(p_business);
    SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
      AND id=p_search AND actor_id=a;
    IF NOT FOUND OR s.business_identity_mac IS NULL OR s.business_name IS DISTINCT FROM i->>'name'
      OR s.business_row_version IS DISTINCT FROM (i->>'row_version')::bigint
      OR s.business_address_version IS DISTINCT FROM (i->>'address_version')::bigint
      OR s.business_location_version IS DISTINCT FROM (i->>'location_version')::bigint
      OR s.geocode_origin_id IS DISTINCT FROM (i->>'origin_id')::uuid
      OR s.context_version IS DISTINCT FROM (i->>'context_version')::bigint THEN
      RAISE EXCEPTION 'REFERENCE_BUSINESS_IDENTITY_STALE'; END IF;
  END $$"""

_LOAD_IDENTITY = """CREATE FUNCTION public.reference_load_business_identity(p_business uuid,p_search uuid)
  RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid; result jsonb;
  BEGIN
    PERFORM public.reference_assert_business_identity(p_business,p_search);
    SELECT jsonb_build_object('name',s.business_name,'row_version',s.business_row_version,
      'address_version',s.business_address_version,'location_version',s.business_location_version,
      'address',v.address,'context_version',s.context_version,'mac',s.business_identity_mac,
      'key_version',s.identity_key_version) INTO result FROM public.reference_provider_searches s
      JOIN public.business_address_versions v ON (v.tenant_id,v.business_id,v.version)=
        (s.tenant_id,s.business_id,s.business_address_version)
      WHERE s.tenant_id=t AND s.business_id=p_business AND s.id=p_search;
    RETURN result;
  END $$"""


def _identity_upgrade():
    t = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    op.execute(
        f"CREATE POLICY reference_business_identity ON businesses TO {_ROLE} "
        f"USING(tenant_id={t}) WITH CHECK(tenant_id={t})"
    )
    op.execute(f"GRANT SELECT(id,tenant_id,name,row_version),UPDATE(name) ON businesses TO {_ROLE}")
    op.execute("""ALTER TABLE reference_provider_searches ADD COLUMN business_name text,
      ADD COLUMN business_row_version bigint,ADD COLUMN business_address_version bigint,
      ADD COLUMN business_location_version bigint,ADD COLUMN business_identity_mac char(64),
      ADD COLUMN geocode_origin_id uuid,
      ADD CHECK((business_identity_mac IS NULL AND business_name IS NULL AND business_row_version IS NULL
          AND business_address_version IS NULL AND business_location_version IS NULL AND geocode_origin_id IS NULL)
        OR (business_identity_mac IS NOT NULL AND business_name IS NOT NULL AND business_row_version IS NOT NULL
          AND business_address_version IS NOT NULL AND business_identity_mac ~ '^[0-9a-f]{64}$' AND\
 length(business_name) BETWEEN 1 AND 120
          AND business_row_version>0 AND business_address_version>0)),
      ADD FOREIGN KEY(tenant_id,business_id,business_address_version)
        REFERENCES business_address_versions(tenant_id,business_id,version),
      ADD FOREIGN KEY(tenant_id,business_id,geocode_origin_id)
        REFERENCES reference_geocode_origins(tenant_id,business_id,id)""")
    op.execute(
        f"GRANT UPDATE(business_name,business_row_version,business_address_version,business_location_version,"
        f"business_identity_mac,geocode_origin_id) ON reference_provider_searches TO {_ROLE}"
    )
    op.execute(_ADMISSION)
    op.execute(
        "REVOKE ALL ON FUNCTION public.reference_admit_provider_search(uuid,uuid,uuid,uuid,text,text,bigint,smallint) "
        "FROM PUBLIC,meu_braco_direito_app"
    )
    _function(_PREPARE_IDENTITY, "reference_prepare_business_identity(uuid)", "meu_braco_direito_app")
    _function(
        _BOUND_ADMISSION,
        "reference_admit_bound_search(uuid,uuid,uuid,uuid,text,text,bigint,smallint,text,text,bigint,bigint,big\
int,uuid)",
        "meu_braco_direito_app",
    )
    _function(_ASSERT_IDENTITY, "reference_assert_business_identity(uuid,uuid)", _ROLE)
    _function(_LOAD_IDENTITY, "reference_load_business_identity(uuid,uuid)", "meu_braco_direito_correlator")
    op.execute(_CONTEXT_LOADER)
    for name, signature in (
        ("reference_google_intent", "uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,bigint"),
        ("reference_jev_intent", "uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,text,bigint"),
        ("reference_google_claim", "uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text"),
        ("reference_jev_claim", "uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text,uuid,uuid,text,bigint"),
        ("reference_reco_claim", "uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text,uuid,uuid,uuid,text,bigint"),
    ):
        op.execute(f"""DO $$ DECLARE d text; BEGIN
          SELECT pg_get_functiondef('public.{name}({signature})'::regprocedure) INTO d;
          EXECUTE replace(d,'SELECT version INTO current_version FROM public.business_context_heads',
            'IF EXISTS(SELECT 1 FROM public.reference_provider_searches WHERE tenant_id=t AND\
 business_id=p_business AND id=p_search AND cycle_id IS NOT NULL) THEN PERFORM\
 public.reference_assert_business_identity(p_business,p_search); END IF; SELECT version INTO current_version\
 FROM public.business_context_heads');
          END $$""")
    # Keep the existing publication transaction and executor fences; add the identity check before its financial lock.
    op.execute("""DO $$ DECLARE d text; BEGIN
      SELECT\
 pg_get_functiondef('public.reference_publish_shortlist(uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,jsonb\
)'::regprocedure) INTO d;
      IF position('PERFORM pg_advisory_xact_lock(hashtextextended(''reference-cost-guard'',70));' IN d)=0 THEN
        RAISE EXCEPTION 'REFERENCE_PUBLICATION_SIGNATURE_CHANGED'; END IF;
      EXECUTE replace(d,'PERFORM pg_advisory_xact_lock(hashtextextended(''reference-cost-guard'',70));',
        'PERFORM public.reference_assert_business_identity(p_business,p_search); PERFORM\
 pg_advisory_xact_lock(hashtextextended(''reference-cost-guard'',70));');
      END $$""")
    # The origin is charged once, but every search using it accounts for that acquisition in its per-search cap.
    op.execute(
        "GRANT SELECT(geocode_origin_id) ON reference_provider_searches,reference_cost_reservations "
        "TO meu_braco_direito_reference_lock"
    )
    op.execute("""DO $$ DECLARE d text; BEGIN
      SELECT pg_get_functiondef('public.reference_search_cost_usage(uuid,uuid,text)'::regprocedure) INTO d;
      IF position('AND r.provider_search_id=p_search' IN d)=0 THEN RAISE EXCEPTION\
 'REFERENCE_USAGE_SIGNATURE_CHANGED'; END IF;
      EXECUTE replace(d,'AND r.provider_search_id=p_search',
        'AND (r.provider_search_id=p_search OR r.geocode_origin_id=(SELECT s.geocode_origin_id FROM\
 public.reference_provider_searches s WHERE s.tenant_id=t AND s.business_id=p_business AND s.id=p_search))');
      END $$""")


_ORIGINAL_ADMISSION = """CREATE OR REPLACE FUNCTION public.reference_admit_provider_search(
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
      END $$"""


_ORIGINAL_LOADER = """CREATE OR REPLACE FUNCTION public.reference_load_search_context(p_business uuid,p_search\
 uuid,p_event uuid)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        s public.reference_provider_searches%ROWTYPE; doc jsonb; version bigint;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_search IS NULL OR p_event IS NULL THEN
          RAISE EXCEPTION 'REFERENCE_CONTEXT_LOAD_INVALID'; END IF;
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        SELECT h.version,v.document INTO version,doc FROM public.business_context_heads h
          JOIN public.business_context_versions v
            ON (v.tenant_id,v.business_id,v.version)=(h.tenant_id,h.business_id,h.version)
          WHERE h.tenant_id=t AND h.business_id=p_business FOR SHARE OF h;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_CONTEXT_LOAD_INVALID'; END IF;
        SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_search AND state='pending' AND radius_occupied FOR SHARE;
        IF NOT FOUND OR s.cycle_id IS NULL OR s.request_event_id IS DISTINCT FROM p_event
          OR s.identity_key_version IS NULL OR NOT EXISTS(SELECT 1 FROM public.outbox_events o
            WHERE o.tenant_id=t AND o.id=p_event AND o.event_type='reference.provider_search_requested'
              AND o.payload=jsonb_build_object('business_id',p_business::text,'actor_id',a::text,
                'operation_id',s.operation_id::text)) THEN
          RAISE EXCEPTION 'REFERENCE_CONTEXT_LOAD_INVALID'; END IF;
        IF version IS DISTINCT FROM s.context_version
          OR doc#>>'{preferences,reference_search,scope}' IS DISTINCT FROM 'local'
          OR doc#>'{preferences,reference_search,radius_km}' IS DISTINCT FROM to_jsonb(s.radius_km)
          OR doc#>>'{preferences,reference_search,origin,method}' IS DISTINCT FROM 'device'
          OR doc#>'{preferences,reference_search,origin,coordinates,confirmed}' IS DISTINCT FROM 'true'::jsonb
          OR jsonb_typeof(doc#>'{preferences,reference_search,origin,coordinates,latitude}') IS DISTINCT FROM 'number'
          OR jsonb_typeof(doc#>'{preferences,reference_search,origin,coordinates,longitude}') IS DISTINCT FROM 'number'
          OR jsonb_typeof(doc#>'{preferences,business_terms}') IS DISTINCT FROM 'array' THEN
          RAISE EXCEPTION 'REFERENCE_CONTEXT_LOAD_INVALID'; END IF;
        RETURN jsonb_build_object('operation_id',s.operation_id,'context_version',s.context_version,
          'radius_km',s.radius_km,'identity_key_version',s.identity_key_version,'request_mac',s.request_mac,
          'latitude',doc#>'{preferences,reference_search,origin,coordinates,latitude}',
          'longitude',doc#>'{preferences,reference_search,origin,coordinates,longitude}',
          'business_terms',doc#>'{preferences,business_terms}',
          'business_description',doc#>'{preferences,business_characteristics}');
      END $$"""


def _identity_downgrade():
    op.execute(_ORIGINAL_ADMISSION)
    op.execute(_ORIGINAL_LOADER)
    op.execute(
        "GRANT EXECUTE ON FUNCTION\
 public.reference_admit_provider_search(uuid,uuid,uuid,uuid,text,text,bigint,smallint) TO meu_braco_direito_app"
    )
    # Strip only the exact statement introduced above, preserving earlier fences.
    for name, signature in (
        ("reference_google_intent", "uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,bigint"),
        ("reference_jev_intent", "uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,text,bigint"),
        ("reference_google_claim", "uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text"),
        ("reference_jev_claim", "uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text,uuid,uuid,text,bigint"),
        ("reference_reco_claim", "uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text,uuid,uuid,uuid,text,bigint"),
    ):
        op.execute(f"""DO $$ DECLARE d text; BEGIN
          SELECT pg_get_functiondef('public.{name}({signature})'::regprocedure) INTO d;
          EXECUTE replace(d,
            'IF EXISTS(SELECT 1 FROM public.reference_provider_searches WHERE tenant_id=t AND\
 business_id=p_business AND id=p_search AND cycle_id IS NOT NULL) THEN PERFORM\
 public.reference_assert_business_identity(p_business,p_search); END IF; ', '');
          END $$""")
    op.execute("""DO $$ DECLARE d text; BEGIN
      SELECT\
 pg_get_functiondef('public.reference_publish_shortlist(uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,jsonb\
)'::regprocedure) INTO d;
      EXECUTE replace(d,'PERFORM public.reference_assert_business_identity(p_business,p_search); ', '');
      SELECT pg_get_functiondef('public.reference_search_cost_usage(uuid,uuid,text)'::regprocedure) INTO d;
      EXECUTE replace(d,
        'AND (r.provider_search_id=p_search OR r.geocode_origin_id=(SELECT s.geocode_origin_id FROM\
 public.reference_provider_searches s WHERE s.tenant_id=t AND s.business_id=p_business AND s.id=p_search))',
        'AND r.provider_search_id=p_search');
      END $$""")
    for signature in (
        "reference_load_business_identity(uuid,uuid)",
        "reference_assert_business_identity(uuid,uuid)",
        "reference_admit_bound_search(uuid,uuid,uuid,uuid,text,text,bigint,smallint,text,text,bigint,bigint,big\
int,uuid)",
        "reference_prepare_business_identity(uuid)",
    ):
        op.execute(f"DROP FUNCTION public.{signature}")
    op.execute(
        "ALTER TABLE reference_provider_searches DROP COLUMN business_name,DROP COLUMN business_row_version,"
        "DROP COLUMN business_address_version,DROP COLUMN business_location_version,DROP COLUMN business_identity_mac,"
        "DROP COLUMN geocode_origin_id"
    )
    op.execute("REVOKE SELECT(geocode_origin_id) ON reference_cost_reservations FROM meu_braco_direito_reference_lock")
    op.execute("DROP POLICY reference_business_identity ON businesses")
    op.execute(f"REVOKE SELECT(id,tenant_id,name,row_version),UPDATE(name) ON businesses FROM {_ROLE}")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute(
        "ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN\
 ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested','\
reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_change\
d','reference.provider_effect_requested','reference.provider_cost_changed','reference.provider_effect_completed\
','reference.provider_search_requested','reference.provider_search_cancelled','reference.real_selection_confirm\
ed','reference.private_shortlist_prepared','reference.feed_resources_recorded','reference.contacts_not_dispatch\
ed','reference.contacts_retry_authorized','reference.similarity_snapshot_recorded','business.address_saved','re\
ference.results_published'))"
    )
