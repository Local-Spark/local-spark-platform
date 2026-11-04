"""Selected profile associations, durable analysis windows and derived learnings."""

from alembic import op

revision = "0108_reference_learning"
down_revision = "0107_reference_identity_review"
branch_labels = None
depends_on = None
_ROLE = "meu_braco_direito_reference_ledger"
_RUNTIME = "meu_braco_direito_app,meu_braco_direito_correlator"
_EVENTS = "'reference.learning_requested','reference.learning_completed','reference.learning_blocked','referen\
ce.learning_cancelled','reference.learning_selection_changed'"


def _function(sql, signature, roles):
    op.execute(sql)
    op.execute(f"ALTER FUNCTION public.{signature} OWNER TO {_ROLE}")
    op.execute(f"REVOKE ALL ON FUNCTION public.{signature} FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION public.{signature} TO {roles}")


def upgrade():
    t = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    op.execute("""CREATE TABLE reference_learning_associations(
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,reference_id uuid NOT NULL,
      version bigint NOT NULL CHECK(version>0),source text NOT NULL CHECK(source IN ('owner','suggested')),
      instagram_handle text CHECK(instagram_handle ~ '^[a-z0-9_]([a-z0-9_.]{0,28}[a-z0-9_])?$'),
      actor_id uuid NOT NULL REFERENCES user_accounts(id),accepted_at timestamptz NOT NULL,
      PRIMARY KEY(tenant_id,business_id,reference_id,version),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("""CREATE TABLE reference_learning_heads(
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,reference_id uuid NOT NULL,
      version bigint NOT NULL,selected boolean NOT NULL,
      PRIMARY KEY(tenant_id,business_id,reference_id),
      FOREIGN KEY(tenant_id,business_id,reference_id,version)
        REFERENCES reference_learning_associations(tenant_id,business_id,reference_id,version))""")
    op.execute("""ALTER TABLE reference_feed_windows ALTER COLUMN owner_reference_id DROP NOT NULL,
      ADD COLUMN reference_id uuid,ADD COLUMN instagram_handle text,ADD COLUMN accepted_at timestamptz,
      ADD COLUMN scheduled_at timestamptz,ADD COLUMN event_id uuid,ADD COLUMN blocked_reason text,
      ADD COLUMN status text NOT NULL DEFAULT 'pending'
        CHECK(status IN ('pending','blocked','completed','partial','unavailable','cancelled')),
      ADD FOREIGN KEY(tenant_id,business_id,reference_id,association_version)
        REFERENCES reference_learning_associations(tenant_id,business_id,reference_id,version),
      ADD FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id)
        DEFERRABLE INITIALLY DEFERRED,
      ADD CHECK((reference_id IS NULL AND instagram_handle IS NULL AND scheduled_at IS NULL AND event_id IS NULL)
        OR(reference_id IS NOT NULL AND instagram_handle IS NOT NULL AND scheduled_at IS NOT NULL
          AND accepted_at IS NOT NULL AND event_id IS NOT NULL)),
      ADD UNIQUE(tenant_id,business_id,reference_id,association_version,scheduled_at)""")
    op.execute("""CREATE TABLE reference_learning_results(
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,window_id uuid NOT NULL,
      reference_id uuid NOT NULL,association_version bigint NOT NULL,
      status text NOT NULL CHECK(status IN ('completed','partial','unavailable')),
      patterns jsonb NOT NULL CHECK(jsonb_typeof(patterns)='array' AND jsonb_array_length(patterns)<=10),
      posts integer NOT NULL CHECK(posts BETWEEN 0 AND 20),images integer NOT NULL CHECK(images>=0),
      coverage text NOT NULL CHECK(coverage IN ('unconfirmed','partial')),
      profile_name text CHECK(profile_name IS NULL OR (profile_name=btrim(profile_name)
        AND char_length(profile_name) BETWEEN 1 AND 200 AND octet_length(profile_name)<=800
        AND profile_name !~ '[[:cntrl:]]')),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),event_id uuid NOT NULL,
      PRIMARY KEY(tenant_id,business_id,window_id),
      FOREIGN KEY(tenant_id,business_id,window_id) REFERENCES reference_feed_windows(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,reference_id,association_version)
        REFERENCES reference_learning_associations(tenant_id,business_id,reference_id,version),
      FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id),
      CHECK((status='unavailable' AND patterns='[]'::jsonb) OR(status<>'unavailable' AND jsonb_array_length(pa\
tterns)>0)))""")
    for table in ("reference_learning_associations", "reference_learning_heads", "reference_learning_results"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY learning_ledger ON {table} TO {_ROLE} USING(tenant_id={t}) WITH CHECK(tenant_id={t})"
        )
        op.execute(f"GRANT SELECT,INSERT ON {table} TO {_ROLE}")
    op.execute(f"GRANT UPDATE(version,selected) ON reference_learning_heads TO {_ROLE}")
    op.execute(f"GRANT INSERT,UPDATE(status,blocked_reason) ON reference_feed_windows TO {_ROLE}")
    op.execute(f"GRANT INSERT ON reference_feed_effects TO {_ROLE}")
    op.execute(f"""CREATE POLICY reference_learning_resource_read ON reference_feed_resources
      FOR SELECT TO {_ROLE} USING(tenant_id={t} AND public.lock_reference_cost_owner() AND EXISTS(
        SELECT 1 FROM reference_feed_effects e JOIN reference_feed_windows w
          ON(w.tenant_id,w.business_id,w.id)=(e.tenant_id,e.business_id,e.window_id)
        WHERE(e.tenant_id,e.business_id,e.id)=(reference_feed_resources.tenant_id,
          reference_feed_resources.business_id,reference_feed_resources.effect_id) AND w.reference_id IS NOT NULL))""")

    op.execute("""ALTER TABLE reference_feed_effects DROP CONSTRAINT reference_feed_effects_state_check,
      DROP CONSTRAINT reference_feed_effects_check,
      ADD CHECK(state IN ('pending','running','uncertain','completed')),
      ADD CHECK((state='pending' AND executor_token IS NULL) OR
        (state IN ('running','uncertain','completed') AND executor_token IS NOT NULL))""")
    op.execute(f"""DO $$ DECLARE d text; BEGIN
      SELECT pg_get_constraintdef(oid) INTO d FROM pg_constraint WHERE conrelid='outbox_events'::regclass
        AND conname='outbox_events_event_type_check';
      EXECUTE 'ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check';
      EXECUTE 'ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check '||
        replace(d,'CHECK (','CHECK (event_type IN ({_EVENTS.replace(chr(39), chr(39) * 2)}) OR ');
      END $$""")
    op.execute(f"""CREATE POLICY learning_events ON outbox_events FOR INSERT TO {_ROLE}
      WITH CHECK(tenant_id={t} AND event_type IN ({_EVENTS})
        AND payload->>'actor_id'=current_setting('app.actor_id',true))""")
    op.execute(f"""CREATE POLICY learning_event_read ON outbox_events FOR SELECT TO {_ROLE}
      USING(tenant_id={t} AND event_type IN ({_EVENTS})
        AND payload->>'actor_id'=current_setting('app.actor_id',true))""")
    _function(_LOCK, "reference_learning_selection_lock(uuid)", _RUNTIME)
    _function(_CURRENT, "reference_current_learning_selection(uuid)", _ROLE)
    _function(_WINDOW, "reference_create_learning_window(uuid,uuid,bigint,timestamptz)", _ROLE)
    _function(_SYNC, "reference_sync_learning_selection(uuid,uuid)", _RUNTIME)
    _function(_ACTIVE, "reference_feed_window_active(uuid,uuid)", _RUNTIME)
    _function(_CAPTURE, "reference_capture_generation_context(uuid)", _RUNTIME)
    _function(_READ_STATUS, "reference_read_learning_status(uuid)", _RUNTIME)
    _function(_IS_CURRENT, "reference_generation_context_is_current(uuid,jsonb)", _RUNTIME)
    _function(_LOAD, "reference_learning_load(uuid,uuid,uuid)", "meu_braco_direito_correlator")
    _function(
        _CLAIM,
        "reference_learning_feed_claim(uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,uuid,bigint,text)",
        "meu_braco_direito_correlator",
    )
    _function(_AUTHORIZE, "reference_learning_feed_authorize(uuid,uuid,uuid,uuid,text)", "meu_braco_direito_correlator")
    _function(_BLOCK, "reference_learning_block(uuid,uuid,text)", "meu_braco_direito_correlator")
    _function(
        _FINISH,
        "reference_learning_finish(uuid,uuid,uuid,uuid,jsonb,text,integer,integer,text,text)",
        "meu_braco_direito_correlator",
    )
    op.execute("""GRANT EXECUTE ON FUNCTION
      reference_record_feed_resources(uuid,uuid,uuid,uuid,text,text,text,text,text,text),
      reference_feed_uncertain(uuid,uuid) TO meu_braco_direito_correlator""")
    _bind_writers()


_LOCK = """CREATE FUNCTION public.reference_learning_selection_lock(p_business uuid) RETURNS void
  LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
  BEGIN
    IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
    IF NOT EXISTS(SELECT 1 FROM public.businesses WHERE tenant_id=t AND id=p_business) THEN
      RAISE EXCEPTION 'REFERENCE_BUSINESS_NOT_FOUND'; END IF;
    INSERT INTO public.reference_real_heads(tenant_id,business_id,cycle_id) VALUES(t,p_business,NULL) ON CONFL\
ICT DO NOTHING;
    PERFORM 1 FROM public.reference_real_heads WHERE tenant_id=t AND business_id=p_business FOR UPDATE;
    PERFORM 1 FROM public.owner_references WHERE tenant_id=t AND business_id=p_business AND removed_at IS NULL\
 FOR SHARE;
  END $$"""

_CURRENT = """CREATE FUNCTION public.reference_current_learning_selection(p_business uuid)
  RETURNS TABLE(reference_id uuid,source text,profile text,note text,score text,similarity text,accepted_at timestamptz)
  LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    SELECT r.id,'owner'::text,r.instagram_handle::text,r.note::text,NULL::text,NULL::text,r.created_at
      FROM public.owner_references r WHERE r.tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND r.business_id=p_business AND r.removed_at IS NULL
    UNION ALL
    SELECT c.place_id,'suggested'::text,coalesce(overridden.instagram_handle,profile.instagram_handle),
      NULL::text,c.reputation_score::text,
      (SELECT si.similarity_level FROM public.reference_publication_operations po
        JOIN public.reference_similarity_snapshot_items si ON(si.tenant_id,si.business_id,si.batch_id)=
          (po.tenant_id,po.business_id,po.batch_id) WHERE po.tenant_id=c.tenant_id AND po.business_id=c.business_id
          AND po.result_id=c.result_id AND si.candidate_id=c.id),
      greatest(coalesce((SELECT max(o.created_at) FROM public.reference_real_selection_operations o
        WHERE o.tenant_id=c.tenant_id AND o.business_id=c.business_id AND o.selection @>
          jsonb_build_array(jsonb_build_object('result_id',c.result_id,'candidate_id',c.id))),clock_timestamp()),
          overridden.created_at)
      FROM public.reference_real_selected selected JOIN public.reference_provider_result_candidates c
        ON(c.tenant_id,c.business_id,c.result_id,c.id,c.place_id)=
          (selected.tenant_id,selected.business_id,selected.result_id,selected.candidate_id,selected.place_id)
      LEFT JOIN public.reference_profile_override_heads oh ON(oh.tenant_id,oh.business_id,oh.place_identity)=
        (c.tenant_id,c.business_id,c.place_id)
      LEFT JOIN public.reference_profile_overrides overridden ON
        (overridden.tenant_id,overridden.business_id,overridden.place_identity,overridden.version)=
        (oh.tenant_id,oh.business_id,oh.place_identity,oh.version)
      LEFT JOIN LATERAL(SELECT po.instagram_handle FROM public.reference_provider_profile_options po
        WHERE(po.tenant_id,po.business_id,po.result_id,po.candidate_id)=(c.tenant_id,c.business_id,c.result_id,c.id)
        ORDER BY po.is_primary DESC,po.source_position LIMIT 1) profile ON true
      WHERE c.tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND c.business_id=p_business
  $$"""

_WINDOW = """CREATE FUNCTION public.reference_create_learning_window(p_business uuid,p_reference uuid,
  p_version bigint,p_due timestamptz) RETURNS uuid
  LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;
    association public.reference_learning_associations%ROWTYPE;existing uuid;new_window uuid;ev uuid;
  BEGIN
    SELECT * INTO association FROM public.reference_learning_associations WHERE tenant_id=t AND business_id=p_business
      AND reference_id=p_reference AND version=p_version;
    IF NOT FOUND OR association.instagram_handle IS NULL OR p_due IS NULL THEN RETURN NULL; END IF;
    SELECT id INTO existing FROM public.reference_feed_windows WHERE tenant_id=t AND business_id=p_business
      AND reference_id=p_reference AND association_version=p_version AND scheduled_at=p_due;
    IF FOUND THEN RETURN existing; END IF;
    new_window:=gen_random_uuid();ev:=gen_random_uuid();
    INSERT INTO public.reference_feed_windows(tenant_id,business_id,id,actor_id,owner_reference_id,association_version,
      reference_id,instagram_handle,accepted_at,scheduled_at,event_id)
      VALUES(t,p_business,new_window,a,CASE WHEN association.source='owner' THEN p_reference ELSE NULL END,p_version,
        p_reference,association.instagram_handle,association.accepted_at,p_due,ev);
    INSERT INTO public.outbox_events(id,tenant_id,event_type,payload) VALUES(ev,t,'reference.learning_requested',
      jsonb_build_object('business_id',p_business::text,'actor_id',a::text,'operation_id',new_window::text));
    INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
      VALUES(t,a,new_window,'reference.learning_scheduled',p_reference);
    RETURN new_window;
  END $$"""

_SYNC = """CREATE FUNCTION public.reference_sync_learning_selection(p_business uuid,p_operation uuid) RETURNS void
  LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;item record;
    head public.reference_learning_heads%ROWTYPE;prior public.reference_learning_associations%ROWTYPE;v bigint\
;changed boolean;ev uuid;
  BEGIN
    PERFORM public.reference_learning_selection_lock(p_business);
    IF p_operation IS NULL THEN RAISE EXCEPTION 'REFERENCE_LEARNING_OPERATION_REQUIRED'; END IF;
    UPDATE public.reference_learning_heads h SET selected=false WHERE h.tenant_id=t AND h.business_id=p_business
      AND h.selected AND NOT EXISTS(SELECT 1 FROM public.reference_current_learning_selection(p_business) c
        WHERE c.reference_id=h.reference_id);
    changed:=FOUND;
    FOR item IN SELECT * FROM public.reference_current_learning_selection(p_business) ORDER BY reference_id LOOP
      SELECT * INTO head FROM public.reference_learning_heads WHERE tenant_id=t AND business_id=p_business
        AND reference_id=item.reference_id;
      SELECT * INTO prior FROM public.reference_learning_associations WHERE tenant_id=t AND business_id=p_business
        AND reference_id=item.reference_id AND version=head.version;
      IF head.reference_id IS NOT NULL AND head.selected AND prior.instagram_handle IS NOT DISTINCT FROM item.\
profile THEN
        CONTINUE; END IF;
      changed:=true;v:=coalesce(head.version,0)+1;
      INSERT INTO public.reference_learning_associations(tenant_id,business_id,reference_id,version,source,
        instagram_handle,actor_id,accepted_at) VALUES(t,p_business,item.reference_id,v,item.source,item.profil\
e,a,item.accepted_at);
      INSERT INTO public.reference_learning_heads VALUES(t,p_business,item.reference_id,v,true)
        ON CONFLICT(tenant_id,business_id,reference_id) DO UPDATE SET version=excluded.version,selected=true;
      PERFORM public.reference_create_learning_window(p_business,item.reference_id,v,item.accepted_at);
    END LOOP;
    IF changed THEN
      ev:=gen_random_uuid();
      INSERT INTO public.outbox_events(id,tenant_id,event_type,payload) VALUES(ev,t,'reference.learning_select\
ion_changed',
        jsonb_build_object('business_id',p_business::text,'actor_id',a::text,'operation_id',p_operation::text));
      INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
        VALUES(t,a,ev,'reference.learning_selection_changed',p_business);
    END IF;
  END $$"""

_ACTIVE = """CREATE FUNCTION public.reference_feed_window_active(p_business uuid,p_window uuid) RETURNS boolean
  LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;w public.reference_feed_windows%ROWTYPE;
  BEGIN
    PERFORM public.reference_learning_selection_lock(p_business);
    SELECT * INTO w FROM public.reference_feed_windows WHERE tenant_id=t AND business_id=p_business AND id=p_w\
indow FOR SHARE;
    RETURN w.id IS NOT NULL AND w.actor_id=a AND w.reference_id IS NOT NULL AND w.scheduled_at<=clock_timestamp()
      AND w.status IN ('pending','blocked','completed','partial','unavailable')
      AND EXISTS(SELECT 1 FROM public.reference_learning_heads h JOIN public.reference_learning_associations v
        ON(v.tenant_id,v.business_id,v.reference_id,v.version)=(h.tenant_id,h.business_id,h.reference_id,h.version)
        JOIN public.reference_current_learning_selection(p_business) c ON c.reference_id=h.reference_id
        WHERE h.tenant_id=t AND h.business_id=p_business AND h.reference_id=w.reference_id
          AND h.version=w.association_version AND h.selected AND v.instagram_handle=w.instagram_handle
          AND c.profile=w.instagram_handle);
  END $$"""

_CAPTURE = """CREATE FUNCTION public.reference_capture_generation_context(p_business uuid) RETURNS jsonb
  LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    item record;learn public.reference_learning_results%ROWTYPE;last_window public.reference_feed_windows%ROWTYPE;
    selected jsonb:='[]'::jsonb;learnings jsonb:='[]'::jsonb;state text;
  BEGIN
    PERFORM public.reference_sync_learning_selection(p_business,gen_random_uuid());
    FOR item IN SELECT c.*,h.version FROM public.reference_current_learning_selection(p_business) c
      JOIN public.reference_learning_heads h ON h.tenant_id=t AND h.business_id=p_business
        AND h.reference_id=c.reference_id AND h.selected ORDER BY c.reference_id LOOP
      SELECT * INTO learn FROM public.reference_learning_results WHERE tenant_id=t AND business_id=p_business
        AND reference_id=item.reference_id AND association_version=item.version AND status IN ('completed','partial')
        ORDER BY created_at DESC,window_id DESC LIMIT 1;
      SELECT * INTO last_window FROM public.reference_feed_windows WHERE tenant_id=t AND business_id=p_business
        AND reference_id=item.reference_id AND association_version=item.version
        AND scheduled_at<=clock_timestamp() ORDER BY scheduled_at DESC LIMIT 1;
      state:=CASE WHEN learn.window_id IS NOT NULL THEN learn.status
        WHEN item.profile IS NULL OR last_window.status IN ('blocked','unavailable') THEN 'unavailable'
        WHEN EXISTS(SELECT 1 FROM reference_feed_effects e WHERE e.tenant_id=t AND e.business_id=p_business
          AND e.window_id=last_window.id AND e.state='uncertain' AND NOT EXISTS(
            SELECT 1 FROM reference_feed_resources r WHERE(r.tenant_id,r.business_id,r.effect_id)=
              (e.tenant_id,e.business_id,e.id))) THEN 'unavailable' 
        WHEN EXISTS(SELECT 1 FROM public.reference_feed_effects e WHERE e.tenant_id=t AND e.business_id=p_business
          AND e.window_id=last_window.id) THEN 'pending' ELSE 'not_requested' END;
      selected:=selected||jsonb_build_array(jsonb_build_object('reference_id',item.reference_id,
        'association_version',item.version,'source',item.source,'instagram_handle',item.profile,'note',item.note,
        'score',item.score,'similarity',item.similarity,'analysis_status',state));
      IF learn.window_id IS NOT NULL THEN
        learnings:=learnings||jsonb_build_array(jsonb_build_object('reference_id',item.reference_id,
          'association_version',item.version,'analysis_id',learn.window_id,'source','instagram_feed',
          'status',learn.status,'patterns',learn.patterns)); END IF;
    END LOOP;
    RETURN jsonb_build_object('version',1,'selected',selected,'learnings',learnings);
  END $$"""

_IS_CURRENT = """CREATE FUNCTION public.reference_generation_context_is_current(p_business uuid,p_versions jsonb)
  RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;item jsonb;
  BEGIN
    PERFORM public.reference_learning_selection_lock(p_business);
    IF jsonb_typeof(p_versions) IS DISTINCT FROM 'array' THEN RETURN false; END IF;
    FOR item IN SELECT value FROM jsonb_array_elements(p_versions) LOOP
      IF jsonb_typeof(item) IS DISTINCT FROM 'object' OR NOT item ?& ARRAY['reference_id','association_version']
        OR item-ARRAY['reference_id','association_version']<>'{}'::jsonb THEN RETURN false; END IF;
      IF NOT EXISTS(SELECT 1 FROM public.reference_learning_heads h
        JOIN public.reference_learning_associations v ON(v.tenant_id,v.business_id,v.reference_id,v.version)=
          (h.tenant_id,h.business_id,h.reference_id,h.version)
        JOIN public.reference_current_learning_selection(p_business) c ON c.reference_id=h.reference_id
        WHERE h.tenant_id=t AND h.business_id=p_business AND h.reference_id=(item->>'reference_id')::uuid
          AND h.version=(item->>'association_version')::bigint AND h.selected
          AND v.instagram_handle IS NOT DISTINCT FROM c.profile) THEN RETURN false; END IF;
    END LOOP;
    RETURN true;
  EXCEPTION WHEN invalid_text_representation OR numeric_value_out_of_range THEN RETURN false;
  END $$"""

_LOAD = """CREATE FUNCTION public.reference_learning_load(p_business uuid,p_window uuid,p_event uuid) RETURNS jsonb
  LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;w public.reference_feed_windows%ROWTYPE;
    e public.reference_feed_effects%ROWTYPE;resource public.reference_feed_resources%ROWTYPE;feed jsonb;
  BEGIN
    PERFORM public.reference_learning_selection_lock(p_business);
    SELECT * INTO w FROM public.reference_feed_windows WHERE tenant_id=t AND business_id=p_business
      AND id=p_window AND actor_id=a FOR UPDATE;
    IF NOT FOUND OR w.reference_id IS NULL OR w.event_id IS DISTINCT FROM p_event OR NOT EXISTS(
      SELECT 1 FROM public.outbox_events o WHERE o.tenant_id=t AND o.id=p_event
        AND o.event_type='reference.learning_requested' AND o.payload=jsonb_build_object(
          'business_id',p_business::text,'actor_id',a::text,'operation_id',p_window::text)) THEN
      RAISE EXCEPTION 'REFERENCE_LEARNING_EVENT_INVALID'; END IF;
    IF w.status IN ('pending','blocked') AND NOT public.reference_generation_context_is_current(p_business,
      jsonb_build_array(jsonb_build_object('reference_id',w.reference_id,'association_version',w.association_v\
ersion))) THEN
      UPDATE public.reference_feed_windows SET status='cancelled' WHERE tenant_id=t AND business_id=p_business\
 AND id=w.id;
      w.status:='cancelled';
      INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
        VALUES(t,a,p_window,'reference.learning_cancelled',w.reference_id);
      INSERT INTO public.outbox_events(id,tenant_id,event_type,payload) VALUES(gen_random_uuid(),t,'reference.\
learning_cancelled',
        jsonb_build_object('business_id',p_business::text,'actor_id',a::text,'operation_id',p_window::text));
    END IF;
    SELECT * INTO e FROM public.reference_feed_effects WHERE tenant_id=t AND business_id=p_business AND window\
_id=p_window
      AND actor_id=a ORDER BY id LIMIT 1;
    IF FOUND THEN
      SELECT * INTO resource FROM public.reference_feed_resources WHERE tenant_id=t AND business_id=p_business
        AND effect_id=e.id;
      feed:=jsonb_build_object('effect',e.id,'event',e.event_id,'pilot',e.pilot_id,'state',e.state,
        'executor_token',e.executor_token,'key_version',e.key_version,'tariff_version',e.tariff_version,
        'credential_version',e.credential_version,'build',e.actor_build,'reserved_usd_micros',e.reserved_usd_micros,
        'request_mac',e.request_mac,'run',CASE WHEN resource.effect_id IS NULL THEN NULL ELSE
          jsonb_build_object('run_id',resource.run_id,'dataset_id',resource.dataset_id,'store_id',resource.store_id,
            'queue_id',resource.queue_id,'build_id',resource.build_id,'actor_build',resource.actor_build) END);
    END IF;
    RETURN jsonb_build_object('tenant',t,'business',p_business,'actor',a,'window',w.id,'event',w.event_id,
      'reference',w.reference_id,'association_version',w.association_version,'profile',w.instagram_handle,
      'accepted_at',w.accepted_at,'scheduled_at',w.scheduled_at,'state',w.status,'feed',feed);
  END $$"""

_CLAIM = """CREATE FUNCTION public.reference_learning_feed_claim(p_business uuid,p_window uuid,p_effect uuid,
  p_event uuid,p_pilot uuid,p_mac text,p_key text,p_tariff text,p_credential text,p_build text,p_amount bigint,
  p_reference uuid,p_version bigint,p_profile text)
  RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;w public.reference_feed_windows%ROWTYPE;
    e public.reference_feed_effects%ROWTYPE;result jsonb;
  BEGIN
    IF NOT public.reference_feed_window_active(p_business,p_window) THEN
      RAISE EXCEPTION 'REFERENCE_FEED_REFERENCE_INVALID'; END IF;
    SELECT * INTO w FROM public.reference_feed_windows WHERE tenant_id=t AND business_id=p_business AND id=p_w\
indow FOR UPDATE;
    IF w.status NOT IN ('pending','blocked') OR p_effect IS NULL OR p_event IS NULL
      OR w.reference_id IS DISTINCT FROM p_reference OR w.association_version IS DISTINCT FROM p_version
      OR w.instagram_handle IS DISTINCT FROM p_profile THEN
      RAISE EXCEPTION 'REFERENCE_FEED_INTENT_INVALID'; END IF;
    SELECT * INTO e FROM public.reference_feed_effects WHERE tenant_id=t AND business_id=p_business AND window\
_id=p_window;
    IF FOUND THEN
      IF e.id IS DISTINCT FROM p_effect OR e.actor_id IS DISTINCT FROM a OR e.event_id IS DISTINCT FROM p_event
        OR e.pilot_id IS DISTINCT FROM p_pilot OR e.request_mac IS DISTINCT FROM p_mac
        OR e.key_version IS DISTINCT FROM p_key OR e.tariff_version IS DISTINCT FROM p_tariff
        OR e.credential_version IS DISTINCT FROM p_credential OR e.actor_build IS DISTINCT FROM p_build
        OR e.reserved_usd_micros IS DISTINCT FROM p_amount THEN RAISE EXCEPTION 'REFERENCE_FEED_INTENT_CONFLIC\
T'; END IF;
    ELSE
      INSERT INTO public.outbox_events(id,tenant_id,event_type,payload) VALUES(p_event,t,'reference.provider_e\
ffect_requested',
        jsonb_build_object('business_id',p_business::text,'actor_id',a::text,'operation_id',p_effect::text));
      INSERT INTO public.reference_feed_effects(tenant_id,business_id,id,actor_id,window_id,pilot_id,event_id,\
request_mac,
        key_version,tariff_version,credential_version,actor_build,reserved_usd_micros,state)
        VALUES(t,p_business,p_effect,a,p_window,p_pilot,p_event,p_mac,p_key,p_tariff,p_credential,p_build,p_am\
ount,'pending');
    END IF;
    result:=public.reference_feed_claim(p_business,p_effect,p_event,p_window,p_pilot,p_mac,p_key,p_tariff,p_cr\
edential,p_build,p_amount);
    UPDATE public.reference_feed_windows SET status='pending',blocked_reason=NULL WHERE tenant_id=t AND busine\
ss_id=p_business
      AND id=p_window;
    RETURN result;
  END $$"""

_AUTHORIZE = """CREATE FUNCTION public.reference_learning_feed_authorize(p_business uuid,p_window uuid,p_effect uuid,
  p_token uuid,p_run text) RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;
  BEGIN
    IF NOT public.reference_feed_window_active(p_business,p_window) THEN RETURN false; END IF;
    RETURN EXISTS(SELECT 1 FROM public.reference_feed_effects e JOIN public.reference_feed_resources r
      ON(r.tenant_id,r.business_id,r.effect_id)=(e.tenant_id,e.business_id,e.id)
      WHERE e.tenant_id=t AND e.business_id=p_business AND e.id=p_effect AND e.window_id=p_window AND e.actor_id=a
        AND e.executor_token=p_token AND e.state IN ('running','uncertain') AND r.run_id=p_run);
  END $$"""

_BLOCK = """CREATE FUNCTION public.reference_learning_block(p_business uuid,p_window uuid,p_reason text) RETURNS void
  LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;w public.reference_feed_windows%ROWTYPE;ev uuid;
  BEGIN
    IF p_reason IS NULL OR p_reason NOT IN ('configuration','budget') OR NOT public.reference_feed_window_acti\
ve(p_business,p_window) THEN
      RAISE EXCEPTION 'REFERENCE_LEARNING_BLOCK_INVALID'; END IF;
    SELECT * INTO w FROM public.reference_feed_windows WHERE tenant_id=t AND business_id=p_business AND id=p_w\
indow FOR UPDATE;
    IF w.status NOT IN ('pending','blocked') OR EXISTS(SELECT 1 FROM public.reference_feed_effects e
      WHERE e.tenant_id=t AND e.business_id=p_business AND e.window_id=p_window) THEN
      RAISE EXCEPTION 'REFERENCE_LEARNING_BLOCK_INVALID'; END IF;
    IF w.status='blocked' AND w.blocked_reason=p_reason THEN RETURN; END IF;
    UPDATE public.reference_feed_windows SET status='blocked',blocked_reason=p_reason
      WHERE tenant_id=t AND business_id=p_business AND id=p_window;
    ev:=gen_random_uuid();
    INSERT INTO public.outbox_events(id,tenant_id,event_type,payload) VALUES(ev,t,'reference.learning_blocked',
      jsonb_build_object('business_id',p_business::text,'actor_id',a::text,'operation_id',p_window::text));
    INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
      VALUES(t,a,ev,'reference.learning_blocked',w.reference_id);
  END $$"""

_FINISH = """CREATE FUNCTION public.reference_learning_finish(p_business uuid,p_window uuid,p_effect uuid,p_token uuid,
  p_patterns jsonb,p_status text,p_posts integer,p_images integer,p_coverage text,p_profile_name text DEFAULT \
NULL) RETURNS jsonb
  LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;w public.reference_feed_windows%ROWTYPE;
    prior public.reference_learning_results%ROWTYPE;ev uuid;next_due timestamptz;next_window uuid;next_slot integer;
  BEGIN
    IF NOT public.reference_feed_window_active(p_business,p_window) THEN
      RAISE EXCEPTION 'REFERENCE_FEED_REFERENCE_INVALID'; END IF;
    SELECT * INTO w FROM public.reference_feed_windows WHERE tenant_id=t AND business_id=p_business AND id=p_w\
indow FOR UPDATE;
    PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
    SELECT * INTO prior FROM public.reference_learning_results WHERE tenant_id=t AND business_id=p_business AN\
D window_id=p_window;
    IF NOT EXISTS(SELECT 1 FROM public.reference_feed_effects e LEFT JOIN public.reference_feed_resources r
      ON(r.tenant_id,r.business_id,r.effect_id)=(e.tenant_id,e.business_id,e.id)
      WHERE e.tenant_id=t AND e.business_id=p_business AND e.id=p_effect AND e.window_id=p_window
        AND e.actor_id=a AND e.executor_token=p_token AND (
          (r.effect_id IS NOT NULL AND (e.state IN ('running','uncertain') OR
            (e.state='completed' AND prior.window_id IS NOT NULL))) OR
          (r.effect_id IS NULL AND p_status='unavailable' AND p_patterns='[]'::jsonb
            AND p_posts=0 AND p_images=0 AND p_profile_name IS NULL AND
            (e.state IN ('running','uncertain') OR(e.state='completed' AND prior.window_id IS NOT NULL))))) THEN
      RAISE EXCEPTION 'REFERENCE_FEED_FENCE_INVALID'; END IF;
    IF prior.window_id IS NOT NULL THEN
      IF prior.patterns IS DISTINCT FROM p_patterns OR prior.status IS DISTINCT FROM p_status
        OR prior.posts IS DISTINCT FROM p_posts OR prior.images IS DISTINCT FROM p_images
        OR prior.coverage IS DISTINCT FROM p_coverage OR prior.profile_name IS DISTINCT FROM p_profile_name TH\
EN RAISE EXCEPTION 'REFERENCE_LEARNING_RESULT_CONFLICT'; END IF;
      RETURN jsonb_build_object('state',prior.status,'window_id',p_window);
    END IF;
    IF p_status IS NULL OR p_status NOT IN ('completed','partial','unavailable')
      OR jsonb_typeof(p_patterns) IS DISTINCT FROM 'array' OR jsonb_array_length(p_patterns)>10
      OR p_posts IS NULL OR p_posts NOT BETWEEN 0 AND 20 OR p_images IS NULL OR p_images<0
      OR p_coverage IS NULL OR p_coverage NOT IN ('unconfirmed','partial')
      OR (p_profile_name IS NOT NULL AND (p_profile_name<>btrim(p_profile_name)
        OR char_length(p_profile_name) NOT BETWEEN 1 AND 200 OR octet_length(p_profile_name)>800
        OR p_profile_name ~ '[[:cntrl:]]'))
      OR (p_status='unavailable') IS DISTINCT FROM (jsonb_array_length(p_patterns)=0)
      OR (p_status='partial' AND p_coverage<>'partial') THEN RAISE EXCEPTION 'REFERENCE_LEARNING_RESULT_INVALI\
D'; END IF;
    IF EXISTS(SELECT 1 FROM jsonb_array_elements(p_patterns) pattern
      WHERE jsonb_typeof(pattern) IS DISTINCT FROM 'object' OR NOT pattern ?& ARRAY['dimension','observation']
        OR pattern-ARRAY['dimension','observation']<>'{}'::jsonb OR NOT EXISTS(
          SELECT 1 FROM public.reference_post_effects effect CROSS JOIN(VALUES ('editorial','tone','friendly',\
'Tom acolhedor e próximo.'),
            ('editorial','tone','professional','Tom profissional e informativo.'),
            ('editorial','tone','direct','Tom direto e objetivo.'),
            ('editorial','tone','playful','Tom leve e bem-humorado.'),
            ('editorial','tone','inspirational','Tom inspirador.'),
            ('editorial','theme','product','Apresentação de produtos ou serviços.'),
            ('editorial','theme','offer','Divulgação de ofertas.'),
            ('editorial','theme','education','Conteúdo educativo e dicas.'),
            ('editorial','theme','process','Bastidores e processos.'),
            ('editorial','theme','customer','Experiências de clientes.'),
            ('editorial','theme','team','Apresentação da equipe.'),
            ('editorial','theme','community','Relação com a comunidade.'),
            ('editorial','theme','seasonal','Temas sazonais e datas.'),
            ('visual','format','photo','Uso de fotografia.'),
            ('visual','format','text_card','Uso de cards com texto.'),
            ('visual','format','infographic','Uso de infográficos ou diagramas.'),
            ('visual','format','collage','Uso de colagens e montagens.'),
            ('visual','format','illustration','Uso de ilustrações.'),
            ('visual','palette','warm','Predomínio de cores quentes.'),
            ('visual','palette','cool','Predomínio de cores frias.'),
            ('visual','palette','neutral','Predomínio de cores neutras.'),
            ('visual','palette','vibrant','Uso de cores vibrantes.'),
            ('visual','palette','monochrome','Uso de paleta monocromática.'),
            ('visual','lighting','natural','Iluminação com aparência natural.'),
            ('visual','lighting','soft','Iluminação suave.'),
            ('visual','lighting','studio','Iluminação com aparência de estúdio.'),
            ('visual','lighting','contrast','Iluminação de alto contraste.'),
            ('visual','composition','closeup','Enquadramentos próximos e detalhes.'),
            ('visual','composition','wide','Enquadramentos amplos.'),
            ('visual','composition','centered','Composição com assunto centralizado.'),
            ('visual','composition','minimal','Composição com espaço livre.'),
            ('visual','composition','grid','Composição organizada em blocos.'),
            ('visual','text_density','none','Imagens sem texto sobreposto.'),
            ('visual','text_density','sparse','Pouco texto sobreposto.'),
            ('visual','text_density','dominant','Texto ocupa parte expressiva da imagem.'),
            ('visual','subject','product','Destaque visual para produtos.'),
            ('visual','subject','people','Destaque visual para pessoas.'),
            ('visual','subject','space','Destaque visual para ambientes.'),
            ('visual','subject','process','Destaque visual para processos.'),
            ('visual','subject','abstract','Destaque visual para formas e elementos abstratos.'))
            vocabulary(dimension,question,choice,observation)
          WHERE effect.tenant_id=t AND effect.business_id=p_business AND effect.window_id=p_window
            AND effect.actor_id=a AND effect.state='completed' AND effect.choices->>vocabulary.question=vocabu\
lary.choice
            AND pattern->>'dimension'=vocabulary.dimension AND pattern->>'observation'=vocabulary.observation)) THEN
      RAISE EXCEPTION 'REFERENCE_LEARNING_PATTERN_UNPROVED'; END IF;
    IF EXISTS(SELECT 1 FROM reference_feed_effects e WHERE e.tenant_id=t AND e.business_id=p_business
      AND e.id=p_effect AND e.state='running' AND NOT EXISTS(SELECT 1 FROM reference_feed_resources r
        WHERE(r.tenant_id,r.business_id,r.effect_id)=(e.tenant_id,e.business_id,e.id))) THEN
      PERFORM public.reference_feed_uncertain(p_effect,p_token); END IF;
    ev:=gen_random_uuid();
    INSERT INTO public.outbox_events(id,tenant_id,event_type,payload) VALUES(ev,t,'reference.learning_completed',
      jsonb_build_object('business_id',p_business::text,'actor_id',a::text,'operation_id',p_window::text));
    INSERT INTO public.reference_learning_results(tenant_id,business_id,window_id,reference_id,association_version,
      status,patterns,posts,images,coverage,profile_name,event_id)
      VALUES(t,p_business,p_window,w.reference_id,w.association_version,p_status,p_patterns,p_posts,p_images,p\
_coverage,p_profile_name,ev);
    UPDATE public.reference_feed_windows SET status=p_status,blocked_reason=NULL
      WHERE tenant_id=t AND business_id=p_business AND id=p_window;
    UPDATE public.reference_feed_effects SET state='completed' WHERE tenant_id=t AND business_id=p_business AN\
D id=p_effect;
    next_slot:=greatest(1,floor(((extract(year FROM clock_timestamp() AT TIME ZONE 'UTC')-
      extract(year FROM w.accepted_at AT TIME ZONE 'UTC'))*12+
      extract(month FROM clock_timestamp() AT TIME ZONE 'UTC')-
      extract(month FROM w.accepted_at AT TIME ZONE 'UTC'))/6)::integer);
    next_due:=((w.accepted_at AT TIME ZONE 'UTC')+(next_slot*6)*interval '1 month') AT TIME ZONE 'UTC';
    WHILE next_due<=clock_timestamp() LOOP
      next_slot:=next_slot+1;
      next_due:=((w.accepted_at AT TIME ZONE 'UTC')+(next_slot*6)*interval '1 month') AT TIME ZONE 'UTC'; END LOOP;
    next_window:=public.reference_create_learning_window(p_business,w.reference_id,w.association_version,next_due);
    INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
      VALUES(t,a,p_window,'reference.learning_completed',w.reference_id);
    RETURN jsonb_build_object('state',p_status,'window_id',p_window,'next_window_id',next_window,'next_due_at'\
,next_due);
  END $$"""

_LEGACY_PROFILE_CHECK = """        PERFORM 1 FROM public.owner_references x WHERE x.tenant_id=t AND x.business\
_id=p_business
          AND x.id=w.owner_reference_id AND x.actor_id=a AND x.removed_at IS NULL FOR SHARE;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_FEED_REFERENCE_INVALID'; END IF;"""
_ACTIVE_PROFILE_CHECK = (
    """        IF w.reference_id IS NULL THEN
"""
    + _LEGACY_PROFILE_CHECK
    + """
        ELSIF NOT public.reference_feed_window_active(p_business,p_window) THEN
          RAISE EXCEPTION 'REFERENCE_FEED_REFERENCE_INVALID'; END IF;"""
)


def _replace(signature, old, new):
    old = old.replace("'", "''")
    new = new.replace("'", "''")
    op.execute(f"""DO $$ DECLARE d text; BEGIN
      SELECT pg_get_functiondef('public.{signature}'::regprocedure) INTO d;
      IF position('{old}' IN d)=0 THEN RAISE EXCEPTION 'REFERENCE_LEARNING_WRITER_SIGNATURE_CHANGED'; END IF;
      EXECUTE replace(d,'{old}','{new}'); END $$""")


def _bind_writers():
    _replace(
        "reference_feed_claim(uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint)",
        _LEGACY_PROFILE_CHECK,
        _ACTIVE_PROFILE_CHECK,
    )
    _replace(
        "reference_confirm_real_selection(uuid,uuid,uuid[],uuid[])",
        "RETURN result;",
        "PERFORM public.reference_sync_learning_selection(p_business,p_operation); RETURN result;",
    )
    _replace(
        "reference_save_profile_override(uuid,uuid,uuid,bigint,uuid,uuid,text)",
        "RETURN reply;",
        "PERFORM public.reference_sync_learning_selection(p_business,p_operation); RETURN reply;",
    )


def downgrade():
    op.execute("LOCK TABLE reference_learning_associations,reference_feed_windows IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security=off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_learning_associations)
      OR EXISTS(SELECT 1 FROM reference_feed_windows WHERE reference_id IS NOT NULL)
      OR EXISTS(SELECT 1 FROM reference_learning_results) THEN
      RAISE EXCEPTION 'REFERENCE_LEARNING_PREVENTS_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security=on")
    _replace(
        "reference_feed_claim(uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint)",
        _ACTIVE_PROFILE_CHECK,
        _LEGACY_PROFILE_CHECK,
    )
    _replace(
        "reference_confirm_real_selection(uuid,uuid,uuid[],uuid[])",
        "PERFORM public.reference_sync_learning_selection(p_business,p_operation); RETURN result;",
        "RETURN result;",
    )
    _replace(
        "reference_save_profile_override(uuid,uuid,uuid,bigint,uuid,uuid,text)",
        "PERFORM public.reference_sync_learning_selection(p_business,p_operation); RETURN reply;",
        "RETURN reply;",
    )
    for signature in (
        "reference_learning_finish(uuid,uuid,uuid,uuid,jsonb,text,integer,integer,text,text)",
        "reference_learning_block(uuid,uuid,text)",
        "reference_learning_feed_authorize(uuid,uuid,uuid,uuid,text)",
        "reference_learning_feed_claim(uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,uuid,bigint,text)",
        "reference_learning_load(uuid,uuid,uuid)",
        "reference_generation_context_is_current(uuid,jsonb)",
        "reference_capture_generation_context(uuid)",
        "reference_read_learning_status(uuid)",
        "reference_feed_window_active(uuid,uuid)",
        "reference_sync_learning_selection(uuid,uuid)",
        "reference_create_learning_window(uuid,uuid,bigint,timestamptz)",
        "reference_current_learning_selection(uuid)",
        "reference_learning_selection_lock(uuid)",
    ):
        op.execute(f"DROP FUNCTION public.{signature}")
    op.execute("""REVOKE EXECUTE ON FUNCTION
      reference_record_feed_resources(uuid,uuid,uuid,uuid,text,text,text,text,text,text),
      reference_feed_uncertain(uuid,uuid) FROM meu_braco_direito_correlator""")
    op.execute("DROP POLICY reference_learning_resource_read ON reference_feed_resources")
    op.execute("DROP TABLE reference_learning_results")
    op.execute("""ALTER TABLE reference_feed_windows DROP COLUMN reference_id,DROP COLUMN instagram_handle,
      DROP COLUMN accepted_at,DROP COLUMN scheduled_at,DROP COLUMN event_id,DROP COLUMN status,DROP COLUMN blo\
cked_reason,
      ALTER COLUMN owner_reference_id SET NOT NULL""")
    op.execute("DROP TABLE reference_learning_heads,reference_learning_associations")
    op.execute("""ALTER TABLE reference_feed_effects DROP CONSTRAINT reference_feed_effects_state_check,
      DROP CONSTRAINT reference_feed_effects_check,
      ADD CHECK(state IN ('pending','running','uncertain')),
      ADD CHECK((state='pending' AND executor_token IS NULL) OR(state IN ('running','uncertain') AND executor_\
token IS NOT NULL))""")
    op.execute(f"REVOKE INSERT ON reference_feed_windows,reference_feed_effects FROM {_ROLE}")
    op.execute("DROP POLICY learning_events ON outbox_events")
    op.execute("DROP POLICY learning_event_read ON outbox_events")
    op.execute("""DO $$ DECLARE d text; events text; BEGIN
      SELECT pg_get_constraintdef(oid) INTO d FROM pg_constraint WHERE conrelid='outbox_events'::regclass
        AND conname='outbox_events_event_type_check';
      SELECT string_agg(DISTINCT quote_literal(m[1]),',') INTO events FROM regexp_matches(d,$pattern$'([^']+)'\
$pattern$,'g') m
        WHERE m[1] NOT IN ('reference.learning_requested','reference.learning_completed','reference.learning_b\
locked','reference.learning_cancelled','reference.learning_selection_changed');
      IF events IS NULL THEN RAISE EXCEPTION 'REFERENCE_OUTBOX_CONSTRAINT_INVALID'; END IF;
      EXECUTE 'ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check';
      EXECUTE 'ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN ('|\
|events||'))';
      END $$""")


_READ_STATUS = """CREATE FUNCTION public.reference_read_learning_status(p_business uuid) RETURNS jsonb
  LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;value jsonb;
  BEGIN
    IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
    IF NOT EXISTS(SELECT 1 FROM public.businesses WHERE tenant_id=t AND id=p_business) THEN
      RAISE EXCEPTION 'REFERENCE_BUSINESS_NOT_FOUND'; END IF;
    PERFORM 1 FROM public.reference_real_heads WHERE tenant_id=t AND business_id=p_business FOR SHARE;
    PERFORM 1 FROM public.owner_references WHERE tenant_id=t AND business_id=p_business AND removed_at IS NULL\
 FOR SHARE;
    SELECT coalesce(jsonb_agg(jsonb_build_object('reference_id',c.reference_id,'association_version',h.version,
      'source',c.source,'instagram_handle',c.profile,'profile_name',named.profile_name,
      'patterns',coalesce(learn.patterns,'[]'::jsonb),
      'analysis_status',CASE WHEN learn.window_id IS NOT NULL THEN learn.status
        WHEN c.profile IS NULL OR due.status IN ('blocked','unavailable')
          OR(feed.state='uncertain' AND NOT feed.has_run) THEN 'unavailable'
        WHEN EXISTS(SELECT 1 FROM public.reference_feed_effects e WHERE e.tenant_id=t AND e.business_id=p_business
          AND e.window_id=due.id) THEN 'pending' ELSE 'not_requested' END,
      'update_status',CASE WHEN feed.state='uncertain' AND NOT feed.has_run THEN NULL
        WHEN due.status='blocked' THEN 'waiting'
        WHEN due.status='pending' THEN CASE WHEN EXISTS(SELECT 1 FROM public.reference_feed_effects e
          WHERE e.tenant_id=t AND e.business_id=p_business AND e.window_id=due.id) THEN 'running' ELSE 'waiting' END
        WHEN upcoming.id IS NOT NULL THEN 'scheduled' ELSE NULL END,
      'last_analyzed_at',learn.created_at,'next_analysis_at',
        CASE WHEN feed.state='uncertain' AND NOT feed.has_run THEN NULL ELSE upcoming.scheduled_at END)
        ORDER BY c.reference_id),'\
[]'::jsonb)
      INTO value FROM public.reference_current_learning_selection(p_business) c
      LEFT JOIN public.reference_learning_heads h ON h.tenant_id=t AND h.business_id=p_business
        AND h.reference_id=c.reference_id AND h.selected
      LEFT JOIN LATERAL(SELECT * FROM public.reference_learning_results l WHERE l.tenant_id=t
        AND l.business_id=p_business AND l.reference_id=c.reference_id AND l.association_version=h.version
        AND l.status IN ('completed','partial') ORDER BY l.created_at DESC,l.window_id DESC LIMIT 1) learn ON true
      LEFT JOIN LATERAL(SELECT l.profile_name FROM public.reference_learning_results l WHERE l.tenant_id=t
        AND l.business_id=p_business AND l.reference_id=c.reference_id AND l.association_version=h.version
        AND l.profile_name IS NOT NULL ORDER BY l.created_at DESC,l.window_id DESC LIMIT 1) named ON true
      LEFT JOIN LATERAL(SELECT * FROM public.reference_feed_windows w WHERE w.tenant_id=t
        AND w.business_id=p_business AND w.reference_id=c.reference_id AND w.association_version=h.version
        AND w.scheduled_at<=clock_timestamp() ORDER BY w.scheduled_at DESC LIMIT 1) due ON true
      LEFT JOIN LATERAL(SELECT e.state,EXISTS(SELECT 1 FROM reference_feed_resources r
        WHERE(r.tenant_id,r.business_id,r.effect_id)=(e.tenant_id,e.business_id,e.id)) AS has_run
        FROM reference_feed_effects e WHERE e.tenant_id=t AND e.business_id=p_business
          AND e.window_id=due.id LIMIT 1) feed ON true
      LEFT JOIN LATERAL(SELECT * FROM public.reference_feed_windows w WHERE w.tenant_id=t
        AND w.business_id=p_business AND w.reference_id=c.reference_id AND w.association_version=h.version
        AND w.status IN ('pending','blocked') ORDER BY w.scheduled_at LIMIT 1) upcoming ON true;
    RETURN jsonb_build_object('references',value);
  END $$"""
