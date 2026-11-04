"""Resolve own-business ambiguity before ranking; resume the same durable search."""

from alembic import op

revision = "0107_reference_identity_review"
down_revision = "0106_reference_execution"
branch_labels = None
depends_on = None

_ROLE = "meu_braco_direito_reference_ledger"
_RECORD = "uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,jsonb"
_EVENTS = "'reference.own_business_match_recorded','reference.search_reviewed','reference.radius_expanded'"


def _function(sql, signature, roles):
    op.execute(sql)
    op.execute(f"ALTER FUNCTION public.{signature} OWNER TO {_ROLE}")
    op.execute(f"REVOKE ALL ON FUNCTION public.{signature} FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION public.{signature} TO {roles}")


def upgrade():
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    op.execute("""CREATE TABLE reference_own_business_reviews (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,search_id uuid NOT NULL,batch_id uuid NOT NULL,
      original_actor uuid NOT NULL,request_hash char(64) NOT NULL CHECK(request_hash ~ '^[0-9a-f]{64}$'),
      status text NOT NULL CHECK(status IN ('awaiting_confirmation','resolved')),
      possible_place_ids text[] NOT NULL CHECK(cardinality(possible_place_ids)<=20
        AND array_position(possible_place_ids,NULL) IS NULL),excluded_place_id text,
      confirmation_operation uuid,confirmed_by uuid,event_id uuid NOT NULL,confirmation_event_id uuid,
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),confirmed_at timestamptz,
      PRIMARY KEY(tenant_id,business_id,search_id),UNIQUE(tenant_id,business_id,confirmation_operation),
      FOREIGN KEY(tenant_id,business_id,search_id) REFERENCES reference_provider_searches(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,batch_id) REFERENCES reference_filtered_batches(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id),
      FOREIGN KEY(tenant_id,confirmation_event_id) REFERENCES outbox_events(tenant_id,id),
      CHECK(excluded_place_id IS NULL OR (status='resolved' AND length(excluded_place_id) BETWEEN 1 AND 2048)),
      CHECK((confirmation_operation IS NULL AND confirmed_by IS NULL AND confirmation_event_id IS NULL)
        OR (status='resolved' AND confirmation_operation IS NOT NULL AND confirmed_by IS NOT NULL
          AND confirmation_event_id IS NOT NULL AND confirmed_at IS NOT NULL)))""")
    op.execute("ALTER TABLE reference_own_business_reviews ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reference_own_business_reviews FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY own_review_ledger ON reference_own_business_reviews TO {_ROLE} "
        f"USING(tenant_id={tenant}) WITH CHECK(tenant_id={tenant})"
    )
    op.execute(f"GRANT SELECT,INSERT,UPDATE ON reference_own_business_reviews TO {_ROLE}")
    owner = "public.lock_reference_cost_owner()"
    access = (
        f"tenant_id={tenant} AND {owner} AND EXISTS(SELECT 1 FROM reference_own_business_reviews r "
        "WHERE (r.tenant_id,r.business_id,r.search_id)=(reference_provider_searches.tenant_id,"
        "reference_provider_searches.business_id,reference_provider_searches.id))"
    )
    op.execute(
        f"CREATE POLICY own_review_search_read ON reference_provider_searches FOR SELECT TO {_ROLE} USING({access})"
    )
    op.execute(
        f"CREATE POLICY own_review_search_lock ON reference_provider_searches FOR UPDATE TO {_ROLE} "
        f"USING({access}) WITH CHECK({access})"
    )

    op.execute(f"""DO $$ DECLARE d text; BEGIN
      SELECT pg_get_constraintdef(oid) INTO d FROM pg_constraint WHERE conrelid='outbox_events'::regclass
        AND conname='outbox_events_event_type_check';
      EXECUTE 'ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check';
      EXECUTE 'ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check ' ||
        replace(d,'CHECK (','CHECK (event_type IN ({_EVENTS.replace(chr(39), chr(39) * 2)}) OR ');
      END $$""")
    # The event wakes the original execution. Its author may be another active owner.
    op.execute(f"""CREATE POLICY own_review_events ON outbox_events FOR INSERT TO {_ROLE}
      WITH CHECK(tenant_id={tenant} AND event_type IN ({_EVENTS}) AND EXISTS(
        SELECT 1 FROM reference_provider_searches s WHERE s.tenant_id={tenant}
          AND s.business_id=(payload->>'business_id')::uuid AND s.actor_id=(payload->>'actor_id')::uuid
          AND s.operation_id=(payload->>'operation_id')::uuid))""")
    _function(
        _READ, "reference_read_own_business_review(uuid,uuid)", "meu_braco_direito_app,meu_braco_direito_correlator"
    )
    _function(_RECORD_SQL, f"reference_record_own_business_match({_RECORD})", "meu_braco_direito_correlator")
    _function(
        _ATOMIC_COMMIT,
        "reference_filtered_commit_with_identity(uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,bigint,json\
b,jsonb,jsonb)",
        "meu_braco_direito_correlator",
    )
    _function(_CONFIRM, "reference_confirm_own_business_review(uuid,uuid,uuid,text)", "meu_braco_direito_app")
    _function(_ASSERT, "reference_assert_own_business_resolved(uuid,uuid)", _ROLE)
    op.execute(_SHORTLIST)
    op.execute("""DO $$ DECLARE d text; BEGIN
      SELECT\
 pg_get_functiondef('public.reference_publish_shortlist(uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,json\
b)'::regprocedure) INTO d;
      IF position('PERFORM public.reference_assert_business_identity(p_business,p_search);' IN d)=0 THEN
        RAISE EXCEPTION 'REFERENCE_PUBLICATION_IDENTITY_SIGNATURE_CHANGED'; END IF;
      EXECUTE replace(d,'PERFORM public.reference_assert_business_identity(p_business,p_search);',
        'PERFORM public.reference_assert_own_business_resolved(p_business,p_search);');
      END $$""")
    _families_upgrade()


_READ = """CREATE FUNCTION public.reference_read_own_business_review(p_business uuid,p_search uuid)
  RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    s public.reference_provider_searches%ROWTYPE;r public.reference_own_business_reviews%ROWTYPE;
  BEGIN
    IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_REQUIRED'; END IF;
    SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business AND\
 id=p_search;
    IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_SEARCH_NOT_FOUND'; END IF;
    SELECT * INTO r FROM public.reference_own_business_reviews
      WHERE tenant_id=t AND business_id=p_business AND search_id=p_search;
    RETURN jsonb_build_object('search_id',p_search,'status',coalesce(r.status,'pending'),
      'candidates',coalesce((SELECT jsonb_agg(jsonb_build_object('place_id',value))
        FROM unnest(r.possible_place_ids) value),'[]'::jsonb),'excluded_place_id',r.excluded_place_id);
  END $$"""

_RECORD_SQL = """CREATE FUNCTION public.reference_record_own_business_match(
  p_business uuid,p_search uuid,p_batch uuid,p_google uuid,p_google_event uuid,p_google_token uuid,
  p_jev uuid,p_jev_event uuid,p_jev_token uuid,p_source text,p_match jsonb)
  RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;
    s public.reference_provider_searches%ROWTYPE;b public.reference_filtered_batches%ROWTYPE;
    g public.reference_provider_effects%ROWTYPE;j public.reference_provider_effects%ROWTYPE;
    r public.reference_own_business_reviews%ROWTYPE;fingerprint text;possible text[];excluded text;status\
 text;event_id uuid;
  BEGIN
    IF jsonb_typeof(p_match) IS DISTINCT FROM 'object' OR NOT p_match ?& ARRAY['status','place_ids']
      OR p_match-ARRAY['status','place_ids']<>'{}'::jsonb OR jsonb_typeof(p_match->'status') IS DISTINCT FROM\
 'string' OR p_match->>'status' NOT IN ('absent','review','identified')
      OR jsonb_typeof(p_match->'place_ids') IS DISTINCT FROM 'array' OR jsonb_array_length(p_match->'place_ids')>20
      OR EXISTS(SELECT 1 FROM jsonb_array_elements(p_match->'place_ids') WHERE jsonb_typeof(value)<>'string'
        OR length(value#>>'{}') NOT BETWEEN 1 AND 2048 OR value#>>'{}'<>btrim(value#>>'{}'))
      OR (p_match->>'status'='identified' AND jsonb_array_length(p_match->'place_ids')<>1)
      OR (p_match->>'status'='absent' AND jsonb_array_length(p_match->'place_ids')<>0)
      OR (p_match->>'status'='review' AND jsonb_array_length(p_match->'place_ids')=0) THEN
      RAISE EXCEPTION 'REFERENCE_OWN_MATCH_INVALID'; END IF;
    PERFORM public.reference_assert_business_identity(p_business,p_search);
    SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
      AND actor_id=a AND id=p_search FOR UPDATE;
    SELECT * INTO b FROM public.reference_filtered_batches WHERE tenant_id=t AND business_id=p_business
      AND actor_id=a AND id=p_batch AND search_id=p_search;
    SELECT * INTO g FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business AND id=p_google;
    SELECT * INTO j FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business AND id=p_jev;
    IF s.id IS NULL OR b.id IS NULL OR b.google_effect_id IS DISTINCT FROM p_google OR b.jev_effect_id IS\
 DISTINCT FROM p_jev
      OR b.context_version IS DISTINCT FROM s.context_version OR b.source_batch_mac IS DISTINCT FROM p_source\
 OR g.search_id IS DISTINCT FROM p_search
      OR j.search_id IS DISTINCT FROM p_search OR g.request_event_id IS DISTINCT FROM p_google_event
      OR j.request_event_id IS DISTINCT FROM p_jev_event OR g.executor_token IS DISTINCT FROM p_google_token
      OR j.executor_token IS DISTINCT FROM p_jev_token OR g.provider IS DISTINCT FROM 'google'
      OR j.provider IS DISTINCT FROM 'jev' OR g.state IS DISTINCT FROM 'completed_filtered'
      OR j.state IS DISTINCT FROM 'completed_filtered' THEN RAISE EXCEPTION\
 'REFERENCE_OWN_MATCH_SOURCE_INVALID'; END IF;
    fingerprint:=encode(sha256(convert_to(p_match::text||p_source,'UTF8')),'hex');
    SELECT * INTO r FROM public.reference_own_business_reviews
      WHERE tenant_id=t AND business_id=p_business AND search_id=p_search;
    IF FOUND THEN
      IF r.batch_id IS DISTINCT FROM p_batch OR r.request_hash IS DISTINCT FROM fingerprint THEN
        RAISE EXCEPTION 'REFERENCE_OWN_MATCH_CONFLICT'; END IF;
      RETURN public.reference_read_own_business_review(p_business,p_search);
    END IF;
    IF s.state<>'pending' THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_SEARCH_INACTIVE'; END IF;
    -- Only potentially publishable candidates need a customer's own-listing decision.
    SELECT coalesce(array_agg(c.place_id ORDER BY c.candidate_id),ARRAY[]::text[]) INTO possible
      FROM public.reference_filtered_batch_candidates c WHERE c.tenant_id=t AND c.business_id=p_business
        AND c.batch_id=p_batch AND c.place_id IN (SELECT value FROM jsonb_array_elements_text(p_match->'place_ids'));
    status:=CASE WHEN p_match->>'status'='review' AND cardinality(possible)>0
      THEN 'awaiting_confirmation' ELSE 'resolved' END;
    IF p_match->>'status'='identified' AND cardinality(possible)=1 THEN excluded:=possible[1]; END IF;
    IF status='resolved' THEN possible:=ARRAY[]::text[]; END IF;
    event_id:=gen_random_uuid();
    INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)\
 VALUES(event_id,t,'reference.own_business_match_recorded',
      jsonb_build_object('business_id',p_business::text,'actor_id',s.actor_id::text,'operation_id',s.operation\
_id::text));
    INSERT INTO\
 public.reference_own_business_reviews(tenant_id,business_id,search_id,batch_id,original_actor,request_hash,
      status,possible_place_ids,excluded_place_id,event_id)
      VALUES(t,p_business,p_search,p_batch,a,fingerprint,status,possible,excluded,event_id);
    INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
      VALUES(t,a,s.operation_id,'reference.own_business_match_recorded',p_search);
    RETURN public.reference_read_own_business_review(p_business,p_search);
  END $$"""

_CONFIRM = """CREATE FUNCTION public.reference_confirm_own_business_review(
  p_business uuid,p_search uuid,p_operation uuid,p_place text)
  RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;i jsonb;
    s public.reference_provider_searches%ROWTYPE;r\
 public.reference_own_business_reviews%ROWTYPE;confirmation_event uuid;
  BEGIN
    i:=public.reference_prepare_business_identity(p_business);
    SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business AND\
 id=p_search FOR UPDATE;
    SELECT * INTO r FROM public.reference_own_business_reviews
      WHERE tenant_id=t AND business_id=p_business AND search_id=p_search FOR UPDATE;
    IF s.id IS NULL OR r.search_id IS NULL THEN RAISE EXCEPTION 'REFERENCE_SEARCH_NOT_FOUND'; END IF;
    IF r.confirmation_operation IS NOT NULL THEN
      IF r.confirmation_operation IS DISTINCT FROM p_operation OR r.confirmed_by IS DISTINCT FROM a
        OR r.excluded_place_id IS DISTINCT FROM p_place THEN RAISE EXCEPTION 'REFERENCE_OWN_REVIEW_CONFLICT'; END IF;
      RETURN public.reference_read_own_business_review(p_business,p_search);
    END IF;
    IF s.business_identity_mac IS NULL OR s.business_name IS DISTINCT FROM i->>'name'
      OR s.business_row_version IS DISTINCT FROM (i->>'row_version')::bigint
      OR s.business_address_version IS DISTINCT FROM (i->>'address_version')::bigint
      OR s.business_location_version IS DISTINCT FROM (i->>'location_version')::bigint
      OR s.geocode_origin_id IS DISTINCT FROM (i->>'origin_id')::uuid
      OR s.context_version IS DISTINCT FROM (i->>'context_version')::bigint THEN
      RAISE EXCEPTION 'REFERENCE_BUSINESS_IDENTITY_STALE'; END IF;
    IF p_operation IS NULL OR r.status<>'awaiting_confirmation' OR s.state<>'pending'
      OR (p_place IS NOT NULL AND NOT p_place=ANY(r.possible_place_ids)) THEN
      RAISE EXCEPTION 'REFERENCE_OWN_REVIEW_INVALID'; END IF;
    confirmation_event:=gen_random_uuid();
    INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)\
 VALUES(confirmation_event,t,'reference.search_reviewed',
      jsonb_build_object('business_id',p_business::text,'actor_id',s.actor_id::text,'operation_id',s.operation\
_id::text));
    UPDATE public.reference_own_business_reviews SET status='resolved',possible_place_ids=ARRAY[]::text[],
      excluded_place_id=p_place,confirmation_operation=p_operation,confirmed_by=a,confirmation_event_id=confir\
mation_event,
      confirmed_at=clock_timestamp() WHERE tenant_id=t AND business_id=p_business AND search_id=p_search;
    INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
      VALUES(t,a,p_operation,'reference.own_business_review_confirmed',p_search);
    RETURN public.reference_read_own_business_review(p_business,p_search);
  END $$"""

_ASSERT = """CREATE FUNCTION public.reference_assert_own_business_resolved(p_business uuid,p_search uuid)
  RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    r public.reference_own_business_reviews%ROWTYPE;
  BEGIN
    PERFORM public.reference_assert_business_identity(p_business,p_search);
    SELECT * INTO r FROM public.reference_own_business_reviews
      WHERE tenant_id=t AND business_id=p_business AND search_id=p_search FOR SHARE;
    IF NOT FOUND OR r.status<>'resolved' THEN RAISE EXCEPTION 'REFERENCE_OWN_REVIEW_REQUIRED'; END IF;
    IF r.excluded_place_id IS NOT NULL AND EXISTS(SELECT 1 FROM public.reference_private_shortlist sl
      JOIN public.reference_filtered_batch_candidates c USING(tenant_id,business_id,batch_id,candidate_id)
      WHERE sl.tenant_id=t AND sl.business_id=p_business AND sl.batch_id=r.batch_id
        AND c.place_id=r.excluded_place_id) THEN RAISE EXCEPTION 'REFERENCE_OWN_BUSINESS_NOT_EXCLUDED'; END IF;
    RETURN r.excluded_place_id;
  END $$"""


def downgrade():
    op.execute("LOCK TABLE reference_own_business_reviews,reference_radius_expansions IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security=off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_own_business_reviews)
      OR EXISTS(SELECT 1 FROM reference_radius_expansions)
      OR EXISTS(SELECT 1 FROM reference_provider_searches WHERE family_root_id IS NOT NULL)
      OR EXISTS(SELECT 1 FROM reference_publication_operations WHERE batch_id IS NULL) THEN
      RAISE EXCEPTION 'REFERENCE_OWN_REVIEW_PREVENTS_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security=on")
    op.execute(_ORIGINAL_SHORTLIST)
    op.execute("""DO $$ DECLARE d text; BEGIN
      SELECT\
 pg_get_functiondef('public.reference_publish_shortlist(uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,json\
b)'::regprocedure) INTO d;
      d:=replace(d,'PERFORM public.reference_assert_own_business_resolved(p_business,p_search);',
        'PERFORM public.reference_assert_business_identity(p_business,p_search);');
      EXECUTE replace(d,'PERFORM public.reference_complete_empty_ancestors(p_business,p_search,''completed''); ','');
      END $$""")
    op.execute(_PREVIOUS_USAGE)
    op.execute("""DO $$ DECLARE d text; BEGIN
      SELECT pg_get_functiondef('public.reference_load_search_context(uuid,uuid,uuid)'::regprocedure) INTO d;
      EXECUTE replace(d,
        'OR (doc#>''{preferences,reference_search,radius_km}'' IS DISTINCT FROM to_jsonb(s.radius_km) AND NOT\
 EXISTS(SELECT 1 FROM public.reference_provider_searches root JOIN public.reference_radius_expansions x ON\
 x.tenant_id=root.tenant_id AND x.business_id=root.business_id AND x.root_search_id=root.id WHERE\
 root.tenant_id=t AND root.business_id=p_business AND root.id=s.family_root_id AND root.cycle_id=s.cycle_id\
 AND root.context_version=s.context_version AND x.next_search_id=s.id AND x.kind=''scheduled'' AND\
 doc#>''{preferences,reference_search,radius_km}''=to_jsonb(root.radius_km)))',
        'OR doc#>''{preferences,reference_search,radius_km}'' IS DISTINCT FROM to_jsonb(s.radius_km)');
      END $$""")
    for signature in (
        "reference_filtered_commit_with_identity(uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,bigint,json\
b,jsonb,jsonb)",
        "reference_assert_own_business_resolved(uuid,uuid)",
        "reference_confirm_own_business_review(uuid,uuid,uuid,text)",
        f"reference_record_own_business_match({_RECORD})",
        "reference_read_own_business_review(uuid,uuid)",
        "reference_read_empty_advance(uuid,uuid,uuid)",
        "reference_empty_successor_context(uuid,uuid,uuid)",
        "reference_admit_empty_radius_successor(uuid,uuid,uuid,uuid,uuid,uuid,text,text,text)",
        "reference_publish_empty_search(uuid,uuid,uuid,uuid,uuid)",
        "reference_read_search_family(uuid,uuid)",
        "reference_complete_empty_ancestors(uuid,uuid,text)",
        "reference_search_is_google_empty(uuid,uuid)",
    ):
        op.execute(f"DROP FUNCTION public.{signature}")
    for policy in (
        "own_review_search_read",
        "own_review_search_lock",
        "expansion_search_read",
        "expansion_search_lock",
        "expansion_history_read",
    ):
        op.execute(f"DROP POLICY {policy} ON reference_provider_searches")
    op.execute("DROP POLICY own_review_events ON outbox_events")
    op.execute("DROP TABLE reference_own_business_reviews,reference_radius_expansions")
    op.execute("ALTER TABLE reference_provider_searches DROP COLUMN family_root_id")
    op.execute("ALTER TABLE reference_publication_operations ALTER COLUMN batch_id SET NOT NULL")
    op.execute("REVOKE SELECT(purpose) ON reference_provider_effects FROM meu_braco_direito_reference_lock")
    op.execute("""DO $$ DECLARE d text; events text; BEGIN
      SELECT pg_get_constraintdef(oid) INTO d FROM pg_constraint WHERE conrelid='outbox_events'::regclass
        AND conname='outbox_events_event_type_check';
      SELECT string_agg(DISTINCT quote_literal(m[1]),',') INTO events
        FROM regexp_matches(d,$pattern$'([^']+)'$pattern$,'g') m
        WHERE m[1] NOT IN\
 ('reference.own_business_match_recorded','reference.search_reviewed','reference.radius_expanded');
      IF events IS NULL THEN RAISE EXCEPTION 'REFERENCE_OUTBOX_CONSTRAINT_INVALID'; END IF;
      EXECUTE 'ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check';
      EXECUTE 'ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN\
 ('||events||'))';
      END $$""")


_ORIGINAL_SHORTLIST = """CREATE OR REPLACE FUNCTION public.reference_prepare_shortlist(
      p_business uuid,p_search uuid,p_batch uuid,p_operation uuid,p_candidates uuid[])
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        b public.reference_filtered_batches%ROWTYPE; s public.reference_provider_searches%ROWTYPE;
        prior public.reference_private_shortlist_headers%ROWTYPE; total int; distinct_count int; found_count int;
        event_id uuid; stored uuid[]; current_version bigint;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_search IS NULL OR p_batch IS NULL
          OR p_operation IS NULL OR p_candidates IS NULL OR cardinality(p_candidates)>10
          OR (cardinality(p_candidates)>0 AND array_ndims(p_candidates) IS DISTINCT FROM 1)
          OR array_position(p_candidates,NULL) IS NOT NULL THEN
          RAISE EXCEPTION 'REFERENCE_SHORTLIST_INVALID'; END IF;
        SELECT version INTO current_version FROM public.business_context_heads
          WHERE tenant_id=t AND business_id=p_business FOR SHARE;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO b FROM public.reference_filtered_batches WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_batch AND search_id=p_search;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_SHORTLIST_BATCH_INVALID'; END IF;
        SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_search AND context_version=b.context_version FOR SHARE;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_SHORTLIST_SEARCH_INVALID'; END IF;
        SELECT * INTO prior FROM public.reference_private_shortlist_headers WHERE tenant_id=t
          AND business_id=p_business AND batch_id=p_batch;
        IF FOUND THEN
          SELECT coalesce(array_agg(candidate_id ORDER BY position),ARRAY[]::uuid[]) INTO stored
            FROM public.reference_private_shortlist WHERE tenant_id=t AND business_id=p_business AND batch_id=p_batch;
          IF prior.actor_id IS DISTINCT FROM a OR prior.operation_id IS DISTINCT FROM p_operation
            OR stored IS DISTINCT FROM p_candidates THEN RAISE EXCEPTION 'REFERENCE_SHORTLIST_REPLAY_CONFLICT'; END IF;
          RETURN jsonb_build_object('batch_id',p_batch,'event_id',prior.event_id,'created',false);
        END IF;
        IF current_version IS DISTINCT FROM s.context_version OR s.state<>'pending' THEN
          RAISE EXCEPTION 'REFERENCE_SHORTLIST_CONTEXT_STALE'; END IF;
        SELECT count(*) INTO total FROM public.reference_filtered_batch_candidates
          WHERE tenant_id=t AND business_id=p_business AND batch_id=p_batch;
        IF cardinality(p_candidates)<>least(total,10) THEN RAISE EXCEPTION 'REFERENCE_SHORTLIST_INVALID'; END IF;
        SELECT count(DISTINCT value) INTO distinct_count FROM unnest(p_candidates) value;
        SELECT count(*) INTO found_count FROM public.reference_filtered_batch_candidates
          WHERE tenant_id=t AND business_id=p_business AND batch_id=p_batch AND candidate_id=ANY(p_candidates);
        IF distinct_count<>cardinality(p_candidates) OR found_count<>cardinality(p_candidates) THEN
          RAISE EXCEPTION 'REFERENCE_SHORTLIST_INVALID'; END IF;
        IF EXISTS(SELECT 1 FROM public.reference_filtered_batch_candidates excluded
          JOIN public.reference_filtered_batch_candidates included ON included.tenant_id=excluded.tenant_id
            AND included.business_id=excluded.business_id AND included.batch_id=excluded.batch_id
          WHERE excluded.tenant_id=t AND excluded.business_id=p_business AND excluded.batch_id=p_batch
            AND NOT excluded.candidate_id=ANY(p_candidates) AND included.candidate_id=ANY(p_candidates)
            AND excluded.reputation_score>included.reputation_score) OR EXISTS(
          SELECT 1 FROM unnest(p_candidates) WITH ORDINALITY x(id,pos)
          JOIN unnest(p_candidates) WITH ORDINALITY y(id,pos) ON x.pos<y.pos
          JOIN public.reference_filtered_batch_candidates a1 ON a1.tenant_id=t AND a1.business_id=p_business
            AND a1.batch_id=p_batch AND a1.candidate_id=x.id
          JOIN public.reference_filtered_batch_candidates a2 ON a2.tenant_id=t AND a2.business_id=p_business
            AND a2.batch_id=p_batch AND a2.candidate_id=y.id WHERE a1.reputation_score<a2.reputation_score) THEN
          RAISE EXCEPTION 'REFERENCE_SHORTLIST_RANK_INVALID'; END IF;
        event_id := gen_random_uuid();
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(event_id,t,'reference.private_shortlist_prepared',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_operation::text));
        INSERT INTO public.reference_private_shortlist_headers
          (tenant_id,business_id,batch_id,actor_id,operation_id,event_id)
          VALUES(t,p_business,p_batch,a,p_operation,event_id);
        INSERT INTO public.reference_private_shortlist(tenant_id,business_id,batch_id,candidate_id,position)
          SELECT t,p_business,p_batch,id,pos FROM unnest(p_candidates) WITH ORDINALITY x(id,pos);
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_operation,'reference.shortlist_prepared',p_batch);
        RETURN jsonb_build_object('batch_id',p_batch,'event_id',event_id,'created',true);
      END $$"""

_SHORTLIST = """CREATE OR REPLACE FUNCTION public.reference_prepare_shortlist(
      p_business uuid,p_search uuid,p_batch uuid,p_operation uuid,p_candidates uuid[])
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        b public.reference_filtered_batches%ROWTYPE; s public.reference_provider_searches%ROWTYPE;
        prior public.reference_private_shortlist_headers%ROWTYPE; total int; distinct_count int; found_count int;
        event_id uuid; stored uuid[]; current_version bigint;own_place text;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_search IS NULL OR p_batch IS NULL
          OR p_operation IS NULL OR p_candidates IS NULL OR cardinality(p_candidates)>10
          OR (cardinality(p_candidates)>0 AND array_ndims(p_candidates) IS DISTINCT FROM 1)
          OR array_position(p_candidates,NULL) IS NOT NULL THEN
          RAISE EXCEPTION 'REFERENCE_SHORTLIST_INVALID'; END IF;
        own_place:=public.reference_assert_own_business_resolved(p_business,p_search);
        SELECT version INTO current_version FROM public.business_context_heads
          WHERE tenant_id=t AND business_id=p_business FOR SHARE;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO b FROM public.reference_filtered_batches WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_batch AND search_id=p_search;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_SHORTLIST_BATCH_INVALID'; END IF;
        SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_search AND context_version=b.context_version FOR SHARE;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_SHORTLIST_SEARCH_INVALID'; END IF;
        SELECT * INTO prior FROM public.reference_private_shortlist_headers WHERE tenant_id=t
          AND business_id=p_business AND batch_id=p_batch;
        IF FOUND THEN
          SELECT coalesce(array_agg(candidate_id ORDER BY position),ARRAY[]::uuid[]) INTO stored
            FROM public.reference_private_shortlist WHERE tenant_id=t AND business_id=p_business AND batch_id=p_batch;
          IF prior.actor_id IS DISTINCT FROM a OR prior.operation_id IS DISTINCT FROM p_operation
            OR stored IS DISTINCT FROM p_candidates THEN RAISE EXCEPTION 'REFERENCE_SHORTLIST_REPLAY_CONFLICT'; END IF;
          RETURN jsonb_build_object('batch_id',p_batch,'event_id',prior.event_id,'created',false);
        END IF;
        IF current_version IS DISTINCT FROM s.context_version OR s.state<>'pending' THEN
          RAISE EXCEPTION 'REFERENCE_SHORTLIST_CONTEXT_STALE'; END IF;
        SELECT count(*) INTO total FROM public.reference_filtered_batch_candidates
          WHERE tenant_id=t AND business_id=p_business AND batch_id=p_batch AND place_id IS DISTINCT FROM own_place;
        IF cardinality(p_candidates)<>least(total,10) THEN RAISE EXCEPTION 'REFERENCE_SHORTLIST_INVALID'; END IF;
        SELECT count(DISTINCT value) INTO distinct_count FROM unnest(p_candidates) value;
        SELECT count(*) INTO found_count FROM public.reference_filtered_batch_candidates
          WHERE tenant_id=t AND business_id=p_business AND batch_id=p_batch AND candidate_id=ANY(p_candidates)\
 AND place_id IS DISTINCT FROM own_place;
        IF distinct_count<>cardinality(p_candidates) OR found_count<>cardinality(p_candidates) THEN
          RAISE EXCEPTION 'REFERENCE_SHORTLIST_INVALID'; END IF;
        IF EXISTS(SELECT 1 FROM public.reference_filtered_batch_candidates excluded
          JOIN public.reference_filtered_batch_candidates included ON included.tenant_id=excluded.tenant_id
            AND included.business_id=excluded.business_id AND included.batch_id=excluded.batch_id
          WHERE excluded.tenant_id=t AND excluded.business_id=p_business AND excluded.batch_id=p_batch
            AND excluded.place_id IS DISTINCT FROM own_place AND NOT excluded.candidate_id=ANY(p_candidates)\
 AND included.candidate_id=ANY(p_candidates)
            AND excluded.reputation_score>included.reputation_score) OR EXISTS(
          SELECT 1 FROM unnest(p_candidates) WITH ORDINALITY x(id,pos)
          JOIN unnest(p_candidates) WITH ORDINALITY y(id,pos) ON x.pos<y.pos
          JOIN public.reference_filtered_batch_candidates a1 ON a1.tenant_id=t AND a1.business_id=p_business
            AND a1.batch_id=p_batch AND a1.candidate_id=x.id
          JOIN public.reference_filtered_batch_candidates a2 ON a2.tenant_id=t AND a2.business_id=p_business
            AND a2.batch_id=p_batch AND a2.candidate_id=y.id WHERE a1.reputation_score<a2.reputation_score) THEN
          RAISE EXCEPTION 'REFERENCE_SHORTLIST_RANK_INVALID'; END IF;
        event_id := gen_random_uuid();
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(event_id,t,'reference.private_shortlist_prepared',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_operation::text));
        INSERT INTO public.reference_private_shortlist_headers
          (tenant_id,business_id,batch_id,actor_id,operation_id,event_id)
          VALUES(t,p_business,p_batch,a,p_operation,event_id);
        INSERT INTO public.reference_private_shortlist(tenant_id,business_id,batch_id,candidate_id,position)
          SELECT t,p_business,p_batch,id,pos FROM unnest(p_candidates) WITH ORDINALITY x(id,pos);
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_operation,'reference.shortlist_prepared',p_batch);
        RETURN jsonb_build_object('batch_id',p_batch,'event_id',event_id,'created',true);
      END $$"""


_ATOMIC_COMMIT = """CREATE FUNCTION public.reference_filtered_commit_with_identity(
  p_business uuid,p_search uuid,p_batch uuid,p_google uuid,p_google_event uuid,p_google_token uuid,
  p_jev uuid,p_jev_event uuid,p_jev_token uuid,p_source text,p_context bigint,p_candidates jsonb,p_judgments\
 jsonb,p_match jsonb)
  RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE result uuid;
  BEGIN
    -- Acquire identity locks before the existing provider/financial locks.
    PERFORM public.reference_assert_business_identity(p_business,p_search);
    result := public.reference_filtered_commit_with_similarity(p_business,p_search,p_batch,p_google,p_google_event,
      p_google_token,p_jev,p_jev_event,p_jev_token,p_source,p_context,p_candidates,p_judgments);
    PERFORM public.reference_record_own_business_match(p_business,p_search,p_batch,p_google,p_google_event,
      p_google_token,p_jev,p_jev_event,p_jev_token,p_source,p_match);
    RETURN result;
  END $$"""


_EMPTY_CONTEXT = """CREATE FUNCTION public.reference_empty_successor_context(p_business uuid,p_root uuid,p_parent uuid)
  RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;
    r public.reference_provider_searches%ROWTYPE;p public.reference_provider_searches%ROWTYPE;
    g public.reference_provider_effects%ROWTYPE;i jsonb;root_id uuid;current_cycle uuid;
  BEGIN
    i:=public.reference_prepare_business_identity(p_business);
    SELECT * INTO p FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business AND\
 id=p_parent;
    root_id:=coalesce(p_root,p.family_root_id,p.id);
    SELECT * INTO r FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business AND id=root_id;
    IF r.id IS NULL OR p.id IS NULL OR r.actor_id IS DISTINCT FROM a OR r.cycle_id IS DISTINCT FROM p.cycle_id
      OR (p.id<>r.id AND NOT EXISTS(SELECT 1 FROM public.reference_radius_expansions x WHERE x.tenant_id=t
        AND x.business_id=p_business AND x.root_search_id=r.id AND x.next_search_id=p.id)) THEN
      RAISE EXCEPTION 'REFERENCE_EMPTY_SUCCESSOR_INVALID'; END IF;
    PERFORM public.reference_assert_business_identity(p_business,r.id);
    SELECT cycle_id INTO current_cycle FROM public.reference_real_heads WHERE tenant_id=t AND business_id=p_business;
    IF NOT public.reference_search_is_google_empty(p_business,p.id) OR NOT p.radius_occupied OR current_cycle\
 IS DISTINCT FROM r.cycle_id THEN
      RAISE EXCEPTION 'REFERENCE_EMPTY_SUCCESSOR_INVALID'; END IF;
    RETURN jsonb_build_object('root_id',r.id,'root_operation',r.operation_id,'root_radius',r.radius_km,
      'parent_id',p.id,'next_radius',CASE p.radius_km WHEN 5 THEN 20 WHEN 20 THEN 50 ELSE NULL END,
      'context_version',r.context_version,'key_version',r.identity_key_version,'identity_mac',r.business_identity_mac,
      'name',r.business_name,'row_version',r.business_row_version,'address_version',r.business_address_version,
      'location_version',r.business_location_version,'origin_id',r.geocode_origin_id,'address',i->'address');
  END $$"""

_EMPTY_SUCCESSOR = """CREATE FUNCTION public.reference_admit_empty_radius_successor(
  p_business uuid,p_root uuid,p_parent uuid,p_operation uuid,p_search uuid,p_event uuid,p_mac text,p_identity\
 text,p_key text)
  RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;
    i jsonb;r public.reference_provider_searches%ROWTYPE;s public.reference_provider_searches%ROWTYPE;
    x public.reference_radius_expansions%ROWTYPE;next_radius smallint;link_event uuid;result_id uuid;
    next_empty boolean;kind text;
  BEGIN
    i:=public.reference_empty_successor_context(p_business,p_root,p_parent);
    IF p_operation IS NULL OR p_search IS NULL OR p_event IS NULL OR p_mac IS NULL OR p_identity IS NULL
      OR p_mac !~ '^[0-9a-f]{64}$' OR p_identity !~ '^[0-9a-f]{64}$'
      OR p_key IS DISTINCT FROM i->>'key_version' THEN RAISE EXCEPTION 'REFERENCE_EMPTY_SUCCESSOR_INVALID'; END IF;
    next_radius:=(i->>'next_radius')::smallint;
    IF next_radius IS NULL THEN RAISE EXCEPTION 'REFERENCE_EMPTY_SUCCESSOR_EXHAUSTED'; END IF;
    SELECT * INTO r FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business AND id=p_root;
    SELECT * INTO x FROM public.reference_radius_expansions WHERE tenant_id=t AND business_id=p_business
      AND root_search_id=p_root AND parent_search_id=p_parent;
    IF FOUND THEN
      IF x.operation_id IS DISTINCT FROM p_operation THEN RAISE EXCEPTION 'REFERENCE_EMPTY_SUCCESSOR_CONFLICT'; END IF;
      SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business AND\
 id=x.next_search_id;
      kind:=x.kind;
    ELSE
      SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
        AND cycle_id=r.cycle_id AND radius_km=next_radius AND radius_occupied;
      IF FOUND THEN
        kind:='cached';
      ELSE
        kind:='scheduled';
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(p_event,t,'reference.provider_search_requested',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_operation::text));
        INSERT INTO public.reference_provider_searches(id,tenant_id,business_id,actor_id,operation_id,context_version,
          request_mac,state,cycle_id,radius_km,request_event_id,identity_key_version,business_name,business_row_version,
          business_address_version,business_location_version,business_identity_mac,geocode_origin_id,family_root_id)
          VALUES(p_search,t,p_business,a,p_operation,r.context_version,p_mac,'pending',r.cycle_id,next_radius,\
p_event,p_key,
            r.business_name,r.business_row_version,r.business_address_version,r.business_location_version,p_identity,
            r.geocode_origin_id,p_root) RETURNING * INTO s;
      END IF;
      link_event:=gen_random_uuid();
      INSERT INTO public.outbox_events(id,tenant_id,event_type,payload) VALUES(link_event,t,'reference.radius_expanded',
        jsonb_build_object('business_id',p_business::text,'actor_id',a::text,'operation_id',r.operation_id::text));
      INSERT INTO\
 public.reference_radius_expansions(tenant_id,business_id,root_search_id,parent_search_id,next_search_id,
        operation_id,event_id,kind) VALUES(t,p_business,p_root,p_parent,s.id,p_operation,link_event,kind);
      UPDATE public.reference_provider_searches SET execution_status='radius_successor'
        WHERE tenant_id=t AND business_id=p_business AND id=p_parent AND actor_id=a;
      INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
        VALUES(t,a,p_operation,'reference.radius_expanded',p_root);
    END IF;
    SELECT res.id INTO result_id FROM public.reference_provider_results res
      JOIN public.reference_real_published_results pub ON (pub.tenant_id,pub.business_id,pub.result_id)=
        (res.tenant_id,res.business_id,res.id)
      WHERE res.tenant_id=t AND res.business_id=p_business AND res.search_id=s.id;
    next_empty:=public.reference_search_is_google_empty(p_business,s.id);
    IF kind='cached' AND result_id IS NOT NULL THEN
      PERFORM public.reference_complete_empty_ancestors(p_business,s.id,'completed');
    END IF;
    RETURN jsonb_build_object('state',kind,'next_search_id',s.id,'result_id',result_id,'next_empty',next_empty);
  END $$"""

_COMPLETE_ANCESTORS = """CREATE FUNCTION public.reference_complete_empty_ancestors(
  p_business uuid,p_search uuid,p_status text)
  RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
  BEGIN
    IF p_status NOT IN ('completed','empty_exhausted') THEN RAISE EXCEPTION 'REFERENCE_FAMILY_STATE_INVALID'; END IF;
    WITH RECURSIVE roots(id) AS (
      SELECT coalesce(family_root_id,id) FROM public.reference_provider_searches
        WHERE tenant_id=t AND business_id=p_business AND id=p_search
      UNION
      SELECT x.root_search_id FROM public.reference_radius_expansions x
        JOIN public.reference_provider_searches linked ON (linked.tenant_id,linked.business_id,linked.id)=
          (x.tenant_id,x.business_id,x.next_search_id)
        JOIN roots r ON coalesce(linked.family_root_id,linked.id)=r.id
        WHERE x.tenant_id=t AND x.business_id=p_business)
    UPDATE public.reference_provider_searches s SET state='completed',execution_status=p_status,
      completed_at=coalesce(s.completed_at,clock_timestamp())
      WHERE s.tenant_id=t AND s.business_id=p_business AND coalesce(s.family_root_id,s.id) IN (SELECT id FROM roots)
        AND public.reference_search_is_google_empty(p_business,s.id);
  END $$"""

_EMPTY_PUBLISH = """CREATE FUNCTION public.reference_publish_empty_search(
  p_business uuid,p_root uuid,p_parent uuid,p_operation uuid,p_result uuid)
  RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;
    r public.reference_provider_searches%ROWTYPE;p public.reference_provider_searches%ROWTYPE;
    prior public.reference_publication_operations%ROWTYPE;i jsonb;event_id uuid;fingerprint\
 text;cycle_confirmed timestamptz;
  BEGIN
    IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
    SELECT * INTO prior FROM public.reference_publication_operations WHERE tenant_id=t AND business_id=p_business
      AND search_id=p_parent;
    IF FOUND THEN
      IF prior.batch_id IS NOT NULL OR prior.operation_id IS DISTINCT FROM p_operation OR prior.result_id IS\
 DISTINCT FROM p_result THEN
        RAISE EXCEPTION 'REFERENCE_EMPTY_PUBLICATION_CONFLICT'; END IF;
      RETURN prior.result_id;
    END IF;
    i:=public.reference_empty_successor_context(p_business,p_root,p_parent);
    IF i->>'next_radius' IS NOT NULL OR p_operation IS NULL OR p_result IS NULL THEN
      RAISE EXCEPTION 'REFERENCE_EMPTY_SUCCESSOR_INVALID'; END IF;
    SELECT * INTO r FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business AND id=p_root;
    SELECT * INTO p FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business AND\
 id=p_parent;
    IF p.state NOT IN ('pending','completed') THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_SEARCH_INACTIVE'; END IF;
    fingerprint:=encode(sha256(convert_to(p_parent::text,'UTF8')),'hex');
    INSERT INTO public.reference_provider_results(tenant_id,business_id,id,search_id,recommendation_status)
      VALUES(t,p_business,p_result,p_parent,'unavailable');
    INSERT INTO public.reference_real_published_results VALUES(t,p_business,p_result);
    event_id:=gen_random_uuid();
    INSERT INTO public.outbox_events(id,tenant_id,event_type,payload) VALUES(event_id,t,'reference.results_published',
      jsonb_build_object('business_id',p_business::text,'actor_id',a::text,'operation_id',p_operation::text));
    INSERT INTO public.reference_publication_operations(tenant_id,business_id,search_id,batch_id,actor_id,operation_id,
      result_id,event_id,request_hash) VALUES(t,p_business,p_parent,NULL,a,p_operation,p_result,event_id,fingerprint);
    PERFORM public.reference_complete_empty_ancestors(p_business,p_parent,'empty_exhausted');
    SELECT confirmed_at INTO cycle_confirmed FROM public.reference_real_cycles
      WHERE tenant_id=t AND business_id=p_business AND id=r.cycle_id;
    -- Retain previous choices. A wholly empty, unconfirmed round has nothing to accept.
    IF cycle_confirmed IS NULL AND NOT EXISTS(SELECT 1 FROM public.reference_provider_searches s
      WHERE s.tenant_id=t AND s.business_id=p_business AND s.cycle_id=r.cycle_id AND s.radius_occupied
        AND NOT public.reference_search_is_google_empty(p_business,s.id)) THEN
      UPDATE public.reference_real_heads SET cycle_id=NULL WHERE tenant_id=t AND business_id=p_business AND\
 cycle_id=r.cycle_id;
    END IF;
    INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
      VALUES(t,a,p_operation,'reference.empty_family_published',p_parent);
    RETURN p_result;
  END $$"""

_FAMILY_READ = """CREATE FUNCTION public.reference_read_search_family(p_business uuid,p_search uuid)
  RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    r public.reference_provider_searches%ROWTYPE;head_cycle uuid;confirmed timestamptz;current_id\
 uuid;current_status text;
  BEGIN
    IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
    SELECT root.* INTO r FROM public.reference_provider_searches leaf JOIN public.reference_provider_searches root
      ON (root.tenant_id,root.business_id,root.id)=(leaf.tenant_id,leaf.business_id,coalesce(leaf.family_root_\
id,leaf.id))
      WHERE leaf.tenant_id=t AND leaf.business_id=p_business AND leaf.id=p_search;
    IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_SEARCH_NOT_FOUND'; END IF;
    SELECT cycle_id INTO head_cycle FROM public.reference_real_heads WHERE tenant_id=t AND business_id=p_business;
    SELECT confirmed_at INTO confirmed FROM public.reference_real_cycles
      WHERE tenant_id=t AND business_id=p_business AND id=r.cycle_id;
    WITH RECURSIVE reachable(id) AS (SELECT r.id UNION SELECT x.next_search_id
      FROM public.reference_radius_expansions x JOIN reachable previous ON previous.id=x.parent_search_id
      WHERE x.tenant_id=t AND x.business_id=p_business)
    SELECT s.id,s.execution_status INTO current_id,current_status FROM public.reference_provider_searches s
      WHERE s.tenant_id=t AND s.business_id=p_business AND s.id IN (SELECT id FROM reachable)
      ORDER BY s.radius_km DESC,s.created_at DESC,s.id DESC LIMIT 1;
    IF r.execution_status IN ('completed','empty_exhausted') THEN current_status:=r.execution_status; END IF;
    RETURN\
 jsonb_build_object('family_root_id',r.id,'family_current_search_id',current_id,'family_status',current_status,
      'can_retry_family',current_status='empty_exhausted' AND confirmed IS NULL AND head_cycle IS NULL);
  END $$"""


def _families_upgrade():
    t = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    op.execute("""ALTER TABLE reference_provider_searches ADD COLUMN family_root_id uuid,
      ADD FOREIGN KEY(tenant_id,business_id,family_root_id) REFERENCES\
 reference_provider_searches(tenant_id,business_id,id),
      ADD CHECK(family_root_id IS NULL OR family_root_id<>id)""")
    op.execute("""CREATE TABLE reference_radius_expansions (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,root_search_id uuid NOT NULL,parent_search_id uuid NOT NULL,
      next_search_id uuid NOT NULL,operation_id uuid NOT NULL,event_id uuid NOT NULL,
      kind text NOT NULL CHECK(kind IN ('scheduled','cached')),created_at timestamptz NOT NULL DEFAULT\
 clock_timestamp(),
      PRIMARY\
 KEY(tenant_id,business_id,root_search_id,parent_search_id),UNIQUE(tenant_id,business_id,root_search_id,next_search_id),
      FOREIGN KEY(tenant_id,business_id,root_search_id) REFERENCES\
 reference_provider_searches(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,parent_search_id) REFERENCES\
 reference_provider_searches(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,next_search_id) REFERENCES\
 reference_provider_searches(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id))""")
    op.execute("ALTER TABLE reference_radius_expansions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reference_radius_expansions FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY expansion_ledger ON reference_radius_expansions TO {_ROLE} "
        f"USING(tenant_id={t}) WITH CHECK(tenant_id={t})"
    )
    op.execute(f"GRANT SELECT,INSERT ON reference_radius_expansions TO {_ROLE}")
    op.execute("ALTER TABLE reference_publication_operations ALTER COLUMN batch_id DROP NOT NULL")
    owner = "public.lock_reference_cost_owner()"
    access = (
        f"tenant_id={t} AND {owner} AND EXISTS(SELECT 1 FROM reference_real_heads h WHERE "
        "(h.tenant_id,h.business_id,h.cycle_id)=(reference_provider_searches.tenant_id,"
        "reference_provider_searches.business_id,reference_provider_searches.cycle_id))"
    )
    op.execute(
        f"CREATE POLICY expansion_search_read ON reference_provider_searches FOR SELECT TO {_ROLE} USING({access})"
    )
    op.execute(
        f"CREATE POLICY expansion_search_lock ON reference_provider_searches FOR UPDATE TO {_ROLE}\
 USING({access}) WITH CHECK({access})"
    )
    historical = (
        f"tenant_id={t} AND {owner} AND EXISTS(SELECT 1 FROM reference_radius_expansions x WHERE "
        "x.tenant_id=reference_provider_searches.tenant_id AND x.business_id=reference_provider_searches.business_id "
        "AND reference_provider_searches.id IN (x.root_search_id,x.parent_search_id,x.next_search_id))"
    )
    op.execute(
        f"CREATE POLICY expansion_history_read ON reference_provider_searches FOR SELECT TO {_ROLE} USING({historical})"
    )
    op.execute("GRANT SELECT(purpose) ON reference_provider_effects TO meu_braco_direito_reference_lock")
    op.execute(_GOOGLE_EMPTY_PROOF)
    op.execute(
        "ALTER FUNCTION public.reference_search_is_google_empty(uuid,uuid) OWNER TO meu_braco_direito_reference_lock"
    )
    op.execute("REVOKE ALL ON FUNCTION public.reference_search_is_google_empty(uuid,uuid) FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION public.reference_search_is_google_empty(uuid,uuid) TO {_ROLE}")

    _function(_EMPTY_RECOVERY, "reference_read_empty_advance(uuid,uuid,uuid)", "meu_braco_direito_correlator")
    _function(_EMPTY_CONTEXT, "reference_empty_successor_context(uuid,uuid,uuid)", "meu_braco_direito_correlator")
    _function(_COMPLETE_ANCESTORS, "reference_complete_empty_ancestors(uuid,uuid,text)", _ROLE)
    _function(
        _EMPTY_SUCCESSOR,
        "reference_admit_empty_radius_successor(uuid,uuid,uuid,uuid,uuid,uuid,text,text,text)",
        "meu_braco_direito_correlator",
    )
    _function(
        _EMPTY_PUBLISH, "reference_publish_empty_search(uuid,uuid,uuid,uuid,uuid)", "meu_braco_direito_correlator"
    )
    _function(
        _FAMILY_READ, "reference_read_search_family(uuid,uuid)", "meu_braco_direito_app,meu_braco_direito_correlator"
    )
    op.execute("GRANT SELECT(family_root_id) ON reference_provider_searches TO meu_braco_direito_reference_lock")
    op.execute(_FAMILY_USAGE)
    op.execute("""DO $$ DECLARE d text; BEGIN
      SELECT pg_get_functiondef('public.reference_load_search_context(uuid,uuid,uuid)'::regprocedure) INTO d;
      IF position('OR doc#>''{preferences,reference_search,radius_km}'' IS DISTINCT FROM\
 to_jsonb(s.radius_km)' IN d)=0 THEN
        RAISE EXCEPTION 'REFERENCE_CONTEXT_RADIUS_SIGNATURE_CHANGED'; END IF;
      EXECUTE replace(d,
        'OR doc#>''{preferences,reference_search,radius_km}'' IS DISTINCT FROM to_jsonb(s.radius_km)',
        'OR (doc#>''{preferences,reference_search,radius_km}'' IS DISTINCT FROM to_jsonb(s.radius_km) AND NOT\
 EXISTS(SELECT 1 FROM public.reference_provider_searches root JOIN public.reference_radius_expansions x ON\
 x.tenant_id=root.tenant_id AND x.business_id=root.business_id AND x.root_search_id=root.id WHERE\
 root.tenant_id=t AND root.business_id=p_business AND root.id=s.family_root_id AND root.cycle_id=s.cycle_id\
 AND root.context_version=s.context_version AND x.next_search_id=s.id AND x.kind=''scheduled'' AND\
 doc#>''{preferences,reference_search,radius_km}''=to_jsonb(root.radius_km)))');
      END $$""")

    op.execute("""DO $$ DECLARE d text; BEGIN
      SELECT\
 pg_get_functiondef('public.reference_publish_shortlist(uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,json\
b)'::regprocedure) INTO d;
      EXECUTE replace(d,'RETURN published_id;',
        'PERFORM public.reference_complete_empty_ancestors(p_business,p_search,''completed''); RETURN published_id;');
      END $$""")


_FAMILY_USAGE = """CREATE OR REPLACE FUNCTION public.reference_search_cost_usage(p_business uuid,p_search\
 uuid,p_provider text)
  RETURNS TABLE(total_used numeric,provider_used numeric)
  LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;family uuid;
  BEGIN
    IF p_business IS NULL OR p_search IS NULL OR p_provider IS NULL OR p_provider NOT IN ('google','apify','jev')
      OR NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
    SELECT coalesce(family_root_id,id) INTO family FROM public.reference_provider_searches
      WHERE tenant_id=t AND business_id=p_business AND id=p_search;
    IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_SEARCH_INACTIVE'; END IF;
    RETURN QUERY SELECT
      coalesce(sum(CASE WHEN r.state='completed' THEN r.actual_usd_micros ELSE r.reserved_usd_micros END),0),
      coalesce(sum(CASE WHEN r.provider=p_provider THEN CASE WHEN r.state='completed' THEN r.actual_usd_micros
        ELSE r.reserved_usd_micros END ELSE 0 END),0)
      FROM public.reference_cost_reservations r WHERE r.tenant_id=t AND r.business_id=p_business AND (
        r.provider_search_id IN (SELECT s.id FROM public.reference_provider_searches s WHERE s.tenant_id=t
          AND s.business_id=p_business AND coalesce(s.family_root_id,s.id)=family)
        OR r.geocode_origin_id IN (SELECT s.geocode_origin_id FROM public.reference_provider_searches s WHERE\
 s.tenant_id=t
          AND s.business_id=p_business AND coalesce(s.family_root_id,s.id)=family));
  END $$"""


_GOOGLE_EMPTY_PROOF = """CREATE FUNCTION public.reference_search_is_google_empty(p_business uuid,p_search uuid)
  RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
  BEGIN
    IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
    RETURN EXISTS(SELECT 1 FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
      AND search_id=p_search AND provider='google' AND purpose='discovery' AND state='completed_empty')
      AND NOT EXISTS(SELECT 1 FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
        AND search_id=p_search AND provider='google' AND purpose='discovery' AND state<>'completed_empty');
  END $$"""


_EMPTY_RECOVERY = """CREATE FUNCTION public.reference_read_empty_advance(p_business uuid,p_root uuid,p_parent uuid)
  RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;
    s public.reference_provider_searches%ROWTYPE;x public.reference_radius_expansions%ROWTYPE;
    root_id uuid;result_id uuid;
  BEGIN
    IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
    SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business AND\
 id=p_parent;
    root_id:=coalesce(p_root,s.family_root_id,s.id);
    IF s.id IS NULL OR NOT EXISTS(SELECT 1 FROM public.reference_provider_searches root WHERE root.tenant_id=t
      AND root.business_id=p_business AND root.id=root_id AND root.actor_id=a AND root.cycle_id=s.cycle_id) THEN
      RAISE EXCEPTION 'REFERENCE_EMPTY_SUCCESSOR_INVALID'; END IF;
    SELECT pub.result_id INTO result_id FROM public.reference_publication_operations pub
      WHERE pub.tenant_id=t AND pub.business_id=p_business AND pub.search_id=p_parent AND pub.batch_id IS NULL;
    IF FOUND THEN RETURN jsonb_build_object('state','exhausted','root_id',root_id,'next_search_id',NULL,
      'result_id',result_id,'next_empty',true); END IF;
    SELECT * INTO x FROM public.reference_radius_expansions WHERE tenant_id=t AND business_id=p_business
      AND root_search_id=root_id AND parent_search_id=p_parent;
    IF NOT FOUND THEN RETURN NULL; END IF;
    SELECT pub.result_id INTO result_id FROM public.reference_publication_operations pub WHERE pub.tenant_id=t
      AND pub.business_id=p_business AND pub.search_id=x.next_search_id;
    RETURN jsonb_build_object('state',x.kind,'root_id',root_id,'next_search_id',x.next_search_id,'result_id',result_id,
      'next_empty',public.reference_search_is_google_empty(p_business,x.next_search_id));
  END $$"""


_PREVIOUS_USAGE = """CREATE OR REPLACE FUNCTION public.reference_search_cost_usage(p_business uuid,p_search\
 uuid,p_provider text)
  RETURNS TABLE(total_used numeric,provider_used numeric)
  LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
  BEGIN
    IF p_business IS NULL OR p_search IS NULL OR p_provider IS NULL OR p_provider NOT IN ('google','apify','jev')
      OR NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
    IF NOT EXISTS(SELECT 1 FROM public.reference_provider_searches s WHERE s.tenant_id=t AND s.business_id=p_business
      AND s.id=p_search) THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_SEARCH_INACTIVE'; END IF;
    RETURN QUERY SELECT
      coalesce(sum(CASE WHEN r.state='completed' THEN r.actual_usd_micros ELSE r.reserved_usd_micros END),0),
      coalesce(sum(CASE WHEN r.provider=p_provider THEN CASE WHEN r.state='completed' THEN r.actual_usd_micros
        ELSE r.reserved_usd_micros END ELSE 0 END),0)
      FROM public.reference_cost_reservations r WHERE r.tenant_id=t AND r.business_id=p_business
        AND (r.provider_search_id=p_search OR r.geocode_origin_id=(SELECT s.geocode_origin_id
          FROM public.reference_provider_searches s WHERE s.tenant_id=t AND s.business_id=p_business AND\
 s.id=p_search));
  END $$"""
