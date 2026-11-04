"""Publish a sanitized shortlist and make cycle retention part of selection.

The private writer is callable only by its NOLOGIN owner until the provider
activity is integrated. It consumes existing executor fences, not client scores
or Place IDs. Successful provider output does not settle an unknown invoice.
"""

from importlib import import_module

from alembic import op

revision = "0101_reference_publication"
down_revision = "0100_business_address"
branch_labels = None
depends_on = None

_ROLE = "meu_braco_direito_reference_ledger"
_PUBLISH = "uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,jsonb"
_SELECT = "uuid,uuid,uuid,uuid[],uuid[],uuid,jsonb"


def upgrade():
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m JOIN user_accounts u ON u.id=m.actor_id AND u.active "
        f"WHERE m.tenant_id={tenant} AND m.actor_id={actor} AND m.active AND m.role='owner')"
    )
    op.execute("""ALTER TABLE reference_provider_results ADD COLUMN recommendation_status text NOT NULL
      DEFAULT 'unavailable' CHECK(recommendation_status IN ('completed','unavailable'))""")
    op.execute("""CREATE TABLE reference_publication_operations (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,search_id uuid NOT NULL,batch_id uuid NOT NULL,
      actor_id uuid NOT NULL,operation_id uuid NOT NULL,result_id uuid NOT NULL,event_id uuid NOT NULL,
      request_hash char(64) NOT NULL,
      PRIMARY KEY(tenant_id,business_id,search_id),UNIQUE(tenant_id,business_id,operation_id),
      FOREIGN KEY(tenant_id,business_id,batch_id) REFERENCES reference_filtered_batches(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,result_id) REFERENCES reference_provider_results(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id))""")
    op.execute("""CREATE TABLE reference_cycle_reviews (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,cycle_id uuid NOT NULL,first_result_id uuid NOT NULL,
      required_place_ids uuid[] NOT NULL CHECK(cardinality(required_place_ids)<=3),resolved_operation_id uuid,
      PRIMARY KEY(tenant_id,business_id,cycle_id),
      FOREIGN KEY(tenant_id,business_id,cycle_id) REFERENCES reference_real_cycles(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,first_result_id)
        REFERENCES reference_provider_results(tenant_id,business_id,id))""")
    op.execute("""ALTER TABLE reference_real_selection_operations
      ADD COLUMN decision_confirmation jsonb NOT NULL DEFAULT '{}'::jsonb""")
    for table in ("reference_publication_operations", "reference_cycle_reviews"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY publication_ledger ON {table} TO {_ROLE} "
            f"USING(tenant_id={tenant}) WITH CHECK(tenant_id={tenant})"
        )
        op.execute(f"GRANT SELECT,INSERT,UPDATE ON {table} TO {_ROLE}")
    op.execute(
        "CREATE POLICY cycle_review_owner ON reference_cycle_reviews FOR SELECT TO meu_braco_direito_app "
        f"USING(tenant_id={tenant} AND {owner})"
    )
    op.execute("GRANT SELECT ON reference_cycle_reviews TO meu_braco_direito_app")
    op.execute(f"GRANT UPDATE(response,decision_confirmation) ON reference_real_selection_operations TO {_ROLE}")
    op.execute(f"GRANT UPDATE(completed_at) ON reference_provider_searches TO {_ROLE}")
    for table in (
        "reference_provider_places",
        "reference_provider_results",
        "reference_provider_result_candidates",
        "reference_provider_profile_options",
        "reference_real_published_results",
    ):
        op.execute(
            f"CREATE POLICY publication_write ON {table} TO {_ROLE} "
            f"USING(tenant_id={tenant}) WITH CHECK(tenant_id={tenant})"
        )
        op.execute(f"GRANT SELECT,INSERT ON {table} TO {_ROLE}")
    # Keep at most the presented ten observations after publication; their rows
    # remain because existing contact/recommendation foreign keys refer to them.
    op.execute(f"GRANT DELETE ON reference_filtered_batch_candidates TO {_ROLE}")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_state_check")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_check")
    op.execute("""ALTER TABLE reference_provider_effects
      ADD CONSTRAINT reference_provider_effects_state_check CHECK(state IN
('pending','running','uncertain','completed_empty','completed_filtered','failed_definitive','completed_published')),
      ADD CONSTRAINT reference_provider_effects_check CHECK(
        (state='pending' AND executor_token IS NULL) OR (state<>'pending' AND executor_token IS NOT NULL))""")
    op.execute("""DO $$ DECLARE expression text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO expression FROM pg_constraint
        WHERE conrelid='public.outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE public.outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE public.outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' ||
        expression || ') OR event_type=''reference.results_published'')';
    END $$""")
    op.execute(f"""CREATE POLICY publication_event ON outbox_events FOR INSERT TO {_ROLE}
      WITH CHECK(tenant_id={tenant} AND event_type='reference.results_published'
        AND payload->>'actor_id'={actor}::text)""")
    _publisher()
    _selection()


def _publisher():
    op.execute("""CREATE FUNCTION public.reference_publish_shortlist(
      p_business uuid,p_search uuid,p_batch uuid,p_google uuid,p_google_event uuid,p_google_token uuid,
      p_jev uuid,p_jev_event uuid,p_jev_token uuid,p_source text,p_projection jsonb)
      RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        s public.reference_provider_searches%ROWTYPE;b public.reference_filtered_batches%ROWTYPE;
        g public.reference_provider_effects%ROWTYPE;j public.reference_provider_effects%ROWTYPE;
        e public.reference_provider_effects%ROWTYPE;prior public.reference_publication_operations%ROWTYPE;
        current_cycle uuid;current_version bigint;operation uuid;published_id uuid;event_id uuid;
        request_hash text;item jsonb;reco jsonb;rec_ids uuid[];contact_candidate uuid;contact_place text;
        contact_handles text[];primary_handle text;place_identity uuid;candidate record;required uuid[];
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_search IS NULL OR p_batch IS NULL
          OR jsonb_typeof(p_projection) IS DISTINCT FROM 'object'
          OR NOT p_projection ?& ARRAY['operation_id','recommendation','contacts']
          OR jsonb_typeof(p_projection->'contacts') IS DISTINCT FROM 'array'
          OR jsonb_array_length(p_projection->'contacts')>10 THEN
          RAISE EXCEPTION 'REFERENCE_PUBLICATION_INVALID'; END IF;
        operation := (p_projection->>'operation_id')::uuid;
        IF operation IS NULL THEN RAISE EXCEPTION 'REFERENCE_PUBLICATION_INVALID'; END IF;
        request_hash := encode(sha256(convert_to(p_projection::text,'UTF8')),'hex');
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        SELECT cycle_id INTO current_cycle FROM public.reference_real_heads
          WHERE tenant_id=t AND business_id=p_business FOR UPDATE;
        SELECT version INTO current_version FROM public.business_context_heads
          WHERE tenant_id=t AND business_id=p_business FOR SHARE;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO b FROM public.reference_filtered_batches WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_batch AND search_id=p_search;
        SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_search FOR UPDATE;
        SELECT * INTO g FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_google AND provider='google' FOR UPDATE;
        SELECT * INTO j FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_jev AND provider='jev' AND purpose='discovery' FOR UPDATE;
        IF b.id IS NULL OR s.id IS NULL OR g.id IS NULL OR j.id IS NULL
          OR b.google_effect_id IS DISTINCT FROM p_google OR b.jev_effect_id IS DISTINCT FROM p_jev
          OR b.source_batch_mac IS DISTINCT FROM p_source
          OR g.search_id IS DISTINCT FROM p_search OR j.search_id IS DISTINCT FROM p_search
          OR g.request_event_id IS DISTINCT FROM p_google_event OR j.request_event_id IS DISTINCT FROM p_jev_event
          OR g.executor_token IS DISTINCT FROM p_google_token OR j.executor_token IS DISTINCT FROM p_jev_token
          OR g.state<>'completed_filtered' OR j.state<>'completed_filtered'
          OR g.source_batch_mac IS DISTINCT FROM p_source OR j.source_batch_mac IS DISTINCT FROM p_source
          OR j.parent_google_effect_id IS DISTINCT FROM g.id THEN
          RAISE EXCEPTION 'REFERENCE_PUBLICATION_FENCE_INVALID'; END IF;
        SELECT * INTO prior FROM public.reference_publication_operations WHERE tenant_id=t
          AND business_id=p_business AND search_id=p_search;
        IF FOUND THEN
          IF prior.actor_id IS DISTINCT FROM a OR prior.operation_id IS DISTINCT FROM operation
            OR prior.batch_id IS DISTINCT FROM p_batch OR prior.request_hash IS DISTINCT FROM request_hash THEN
            RAISE EXCEPTION 'REFERENCE_PUBLICATION_CONFLICT'; END IF;
          RETURN prior.result_id;
        END IF;
        IF s.state<>'pending' OR s.cycle_id IS DISTINCT FROM current_cycle
          OR s.context_version IS DISTINCT FROM current_version OR b.context_version IS DISTINCT FROM current_version
          OR NOT EXISTS(SELECT 1 FROM public.reference_private_shortlist_headers h WHERE h.tenant_id=t
            AND h.business_id=p_business AND h.batch_id=p_batch AND h.actor_id=a) THEN
          RAISE EXCEPTION 'REFERENCE_PUBLICATION_CONTEXT_STALE'; END IF;
        reco := p_projection->'recommendation';
        IF reco<>'null'::jsonb THEN
          IF jsonb_typeof(reco->'candidate_ids') IS DISTINCT FROM 'array'
            OR jsonb_array_length(reco->'candidate_ids')>3 THEN
            RAISE EXCEPTION 'REFERENCE_PUBLICATION_RECOMMENDATION_INVALID'; END IF;
          SELECT coalesce(array_agg(value::uuid),ARRAY[]::uuid[]) INTO rec_ids
            FROM jsonb_array_elements_text(reco->'candidate_ids');
          IF cardinality(rec_ids)<>(SELECT count(DISTINCT value) FROM unnest(rec_ids) value)
            OR cardinality(rec_ids)<>(SELECT count(*) FROM public.reference_private_shortlist
              WHERE tenant_id=t AND business_id=p_business AND batch_id=p_batch AND candidate_id=ANY(rec_ids)) THEN
            RAISE EXCEPTION 'REFERENCE_PUBLICATION_RECOMMENDATION_INVALID'; END IF;
          SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
            AND actor_id=a AND id=(reco#>>'{effect,effect_id}')::uuid AND provider='jev'
            AND purpose='recommendation' FOR UPDATE;
          IF e.id IS NULL OR e.search_id IS DISTINCT FROM p_search
            OR e.recommendation_batch_id IS DISTINCT FROM p_batch OR e.parent_google_effect_id IS DISTINCT FROM p_google
            OR e.request_event_id IS DISTINCT FROM (reco#>>'{effect,event_id}')::uuid
            OR e.executor_token IS DISTINCT FROM (reco#>>'{effect,executor_token}')::uuid
            OR e.state NOT IN ('running','uncertain') THEN
            RAISE EXCEPTION 'REFERENCE_PUBLICATION_RECOMMENDATION_INVALID'; END IF;
          UPDATE public.reference_provider_effects SET state='completed_published',updated_at=clock_timestamp()
            WHERE tenant_id=t AND business_id=p_business AND id=e.id;
        ELSE rec_ids := ARRAY[]::uuid[]; END IF;
        IF (SELECT count(DISTINCT value->>'candidate_id') FROM jsonb_array_elements(p_projection->'contacts'))
          <>jsonb_array_length(p_projection->'contacts') THEN RAISE EXCEPTION
            'REFERENCE_PUBLICATION_CONTACTS_INVALID'; END IF;
        published_id := gen_random_uuid();
        INSERT INTO public.reference_provider_results(tenant_id,business_id,id,search_id,recommendation_status)
          VALUES(t,p_business,published_id,p_search,CASE WHEN reco='null'::jsonb THEN 'unavailable' ELSE 'completed'
            END);
        FOR candidate IN SELECT c.*,sl.position AS final_position FROM public.reference_private_shortlist sl
          JOIN public.reference_filtered_batch_candidates c USING(tenant_id,business_id,batch_id,candidate_id)
          WHERE sl.tenant_id=t AND sl.business_id=p_business AND sl.batch_id=p_batch ORDER BY sl.position LOOP
          SELECT p.id INTO place_identity FROM public.reference_provider_places p
            WHERE p.tenant_id=t AND p.business_id=p_business AND p.place_id=candidate.place_id;
          IF NOT FOUND THEN
            place_identity := gen_random_uuid();
            INSERT INTO public.reference_provider_places(tenant_id,business_id,id,place_id)
              VALUES(t,p_business,place_identity,candidate.place_id);
          END IF;
          INSERT INTO public.reference_provider_result_candidates
            (tenant_id,business_id,result_id,id,place_id,position,reputation_score,reputation_formula_version,
             jev_recommendation_rank)
            VALUES(t,p_business,published_id,candidate.candidate_id,place_identity,candidate.final_position,
candidate.reputation_score,candidate.reputation_formula_version,array_position(rec_ids,candidate.candidate_id));
          -- Reuse a previously published association in the same six-month cycle.
          INSERT INTO public.reference_provider_profile_options
(tenant_id,business_id,result_id,candidate_id,instagram_handle,source_position,is_primary,source,association_status)
            SELECT
              t,p_business,published_id,candidate.candidate_id,po.instagram_handle,po.source_position,po.is_primary,
              po.source,po.association_status FROM public.reference_provider_profile_options po
            WHERE (po.tenant_id,po.business_id,po.result_id,po.candidate_id)=(
              SELECT c.tenant_id,c.business_id,c.result_id,c.id FROM public.reference_provider_result_candidates c
              JOIN public.reference_provider_results r ON
                (r.tenant_id,r.business_id,r.id)=(c.tenant_id,c.business_id,c.result_id)
              JOIN public.reference_real_published_results pub ON (pub.tenant_id,pub.business_id,pub.result_id)
                =(r.tenant_id,r.business_id,r.id)
              JOIN public.reference_provider_searches old_search ON
                (old_search.tenant_id,old_search.business_id,old_search.id)
                =(r.tenant_id,r.business_id,r.search_id)
              WHERE c.tenant_id=t AND c.business_id=p_business AND c.place_id=place_identity
                AND old_search.cycle_id=s.cycle_id ORDER BY r.created_at DESC,r.id DESC LIMIT 1);
        END LOOP;
        FOR item IN SELECT value FROM jsonb_array_elements(p_projection->'contacts') LOOP
          contact_candidate := (item->>'candidate_id')::uuid;
          SELECT c.place_id INTO contact_place FROM public.reference_filtered_batch_candidates c
            JOIN public.reference_private_shortlist sl USING(tenant_id,business_id,batch_id,candidate_id)
            WHERE c.tenant_id=t AND c.business_id=p_business AND c.batch_id=p_batch AND
              c.candidate_id=contact_candidate;
          SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
            AND actor_id=a AND id=(item#>>'{effect,effect_id}')::uuid AND provider='apify' FOR UPDATE;
          IF contact_place IS NULL OR e.id IS NULL OR e.state NOT IN ('running','uncertain')
            OR e.request_event_id IS DISTINCT FROM (item#>>'{effect,event_id}')::uuid
            OR e.executor_token IS DISTINCT FROM (item#>>'{effect,executor_token}')::uuid
            OR NOT EXISTS(SELECT 1 FROM public.reference_contacts_lookups l
              JOIN public.reference_contacts_effect_links x USING(tenant_id,business_id)
              WHERE l.tenant_id=t AND l.business_id=p_business AND l.id=x.lookup_id AND x.effect_id=e.id
                AND l.cycle_id=s.cycle_id AND l.place_id=contact_place)
            OR jsonb_typeof(item->'handles') IS DISTINCT FROM 'array' OR jsonb_array_length(item->'handles')>100 THEN
            RAISE EXCEPTION 'REFERENCE_PUBLICATION_CONTACTS_INVALID'; END IF;
          SELECT coalesce(array_agg(value),ARRAY[]::text[]) INTO contact_handles FROM
            jsonb_array_elements_text(item->'handles');
          primary_handle := item->>'primary_handle';
          IF cardinality(contact_handles)<>(SELECT count(DISTINCT value) FROM unnest(contact_handles) value)
            OR (primary_handle IS NOT NULL AND NOT primary_handle=ANY(contact_handles)) THEN
            RAISE EXCEPTION 'REFERENCE_PUBLICATION_CONTACTS_INVALID'; END IF;
          -- A new paid lookup must not replace an existing cached association.
          IF EXISTS(SELECT 1 FROM public.reference_provider_profile_options p WHERE p.tenant_id=t
            AND p.business_id=p_business AND p.result_id=published_id AND p.candidate_id=contact_candidate) THEN
            RAISE EXCEPTION 'REFERENCE_PUBLICATION_CONTACTS_ALREADY_CACHED'; END IF;
          INSERT INTO public.reference_provider_profile_options
(tenant_id,business_id,result_id,candidate_id,instagram_handle,source_position,is_primary,source,association_status)
            SELECT
              t,p_business,published_id,contact_candidate,value,pos,coalesce(value=primary_handle,false),'apify','unverified'
            FROM unnest(contact_handles) WITH ORDINALITY options(value,pos);
          UPDATE public.reference_provider_effects SET state='completed_published',updated_at=clock_timestamp()
            WHERE tenant_id=t AND business_id=p_business AND id=e.id;
        END LOOP;
        INSERT INTO public.reference_real_published_results VALUES(t,p_business,published_id);
        UPDATE public.reference_provider_searches SET state='completed',completed_at=clock_timestamp()
          WHERE tenant_id=t AND business_id=p_business
          AND id=p_search;
        SELECT coalesce(array_agg(old.place_id ORDER BY old.place_id),ARRAY[]::uuid[]) INTO required
          FROM public.reference_real_selected old
          JOIN public.reference_provider_results r ON
            (r.tenant_id,r.business_id,r.id)=(old.tenant_id,old.business_id,old.result_id)
          JOIN public.reference_provider_searches old_search ON
            (old_search.tenant_id,old_search.business_id,old_search.id)
            =(r.tenant_id,r.business_id,r.search_id)
          WHERE old.tenant_id=t AND old.business_id=p_business AND old_search.cycle_id<>s.cycle_id
            AND NOT EXISTS(SELECT 1 FROM public.reference_provider_result_candidates c WHERE c.tenant_id=t
              AND c.business_id=p_business AND c.result_id=published_id AND c.place_id=old.place_id);
        INSERT INTO public.reference_cycle_reviews(tenant_id,business_id,cycle_id,first_result_id,required_place_ids)
          VALUES(t,p_business,s.cycle_id,published_id,required) ON CONFLICT DO NOTHING;
        event_id := gen_random_uuid();
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(event_id,t,'reference.results_published',
          jsonb_build_object('business_id',p_business::text,'actor_id',a::text,'operation_id',operation::text));
        INSERT INTO public.reference_publication_operations
          VALUES(t,p_business,p_search,p_batch,a,operation,published_id,event_id,request_hash);
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,operation,'reference.results_published',published_id);
        DELETE FROM public.reference_filtered_batch_candidates c WHERE c.tenant_id=t AND c.business_id=p_business
          AND c.batch_id=p_batch AND NOT EXISTS(SELECT 1 FROM public.reference_private_shortlist sl
            WHERE
              (sl.tenant_id,sl.business_id,sl.batch_id,sl.candidate_id)=(c.tenant_id,c.business_id,c.batch_id,c.candidate_id));
        RETURN published_id;
      END $$""")
    op.execute(f"ALTER FUNCTION public.reference_publish_shortlist({_PUBLISH}) OWNER TO {_ROLE}")
    op.execute(
        f"REVOKE ALL ON FUNCTION public.reference_publish_shortlist({_PUBLISH}) "
        "FROM PUBLIC,meu_braco_direito_app,meu_braco_direito_correlator"
    )


def _selection():
    op.execute("""CREATE FUNCTION public.reference_confirm_published_selection(
      p_business uuid,p_operation uuid,p_cycle uuid,p_results uuid[],p_candidates uuid[],p_first_result
        uuid,p_decisions jsonb)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        current_cycle uuid;review public.reference_cycle_reviews%ROWTYPE;
        prior public.reference_real_selection_operations%ROWTYPE;confirmation jsonb;response jsonb;
        chosen uuid[];decision_keys uuid[];entry record;
      BEGIN
        IF p_cycle IS NULL OR p_decisions IS NULL OR jsonb_typeof(p_decisions)<>'object' THEN
          RAISE EXCEPTION 'REFERENCE_CYCLE_DECISION_INVALID'; END IF;
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        SELECT cycle_id INTO current_cycle FROM public.reference_real_heads WHERE tenant_id=t AND
          business_id=p_business FOR UPDATE;
        confirmation := jsonb_build_object('cycle_id',p_cycle,'first_result_id',p_first_result,'decisions',p_decisions);
        SELECT * INTO prior FROM public.reference_real_selection_operations WHERE tenant_id=t
          AND business_id=p_business AND operation_id=p_operation;
        IF FOUND THEN
          IF prior.decision_confirmation IS DISTINCT FROM confirmation THEN
            RAISE EXCEPTION 'REFERENCE_SELECTION_OPERATION_CONFLICT'; END IF;
          RETURN public.reference_confirm_real_selection(p_business,p_operation,p_results,p_candidates);
        END IF;
        IF current_cycle IS DISTINCT FROM p_cycle THEN RAISE EXCEPTION 'REFERENCE_SELECTION_CYCLE_STALE'; END IF;
        SELECT * INTO review FROM public.reference_cycle_reviews WHERE tenant_id=t AND business_id=p_business AND
          cycle_id=p_cycle;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_SELECTION_RESULT_PENDING'; END IF;
        IF review.resolved_operation_id IS NULL AND cardinality(review.required_place_ids)>0 THEN
          SELECT coalesce(array_agg(key::uuid ORDER BY key::uuid),ARRAY[]::uuid[]) INTO decision_keys FROM
            jsonb_each_text(p_decisions);
          IF p_first_result IS DISTINCT FROM review.first_result_id OR decision_keys IS DISTINCT FROM
            review.required_place_ids THEN
            RAISE EXCEPTION 'REFERENCE_CYCLE_DECISION_INCOMPLETE'; END IF;
          SELECT coalesce(array_agg(c.place_id),ARRAY[]::uuid[]) INTO chosen
            FROM unnest(p_results,p_candidates) x(result_id,candidate_id)
            JOIN public.reference_provider_result_candidates c ON c.tenant_id=t AND c.business_id=p_business
              AND c.result_id=x.result_id AND c.id=x.candidate_id;
          FOR entry IN SELECT key,value FROM jsonb_each_text(p_decisions) LOOP
            IF entry.value NOT IN ('keep','remove') OR (entry.value='keep') IS DISTINCT FROM
              (entry.key::uuid=ANY(chosen)) THEN
              RAISE EXCEPTION 'REFERENCE_CYCLE_DECISION_SELECTION_MISMATCH'; END IF;
          END LOOP;
        ELSIF p_decisions<>'{}'::jsonb OR p_first_result IS NOT NULL THEN
          RAISE EXCEPTION 'REFERENCE_CYCLE_DECISION_NOT_REQUIRED';
        END IF;
        response := public.reference_confirm_real_selection(p_business,p_operation,p_results,p_candidates);
        UPDATE public.reference_real_selection_operations SET decision_confirmation=confirmation
          WHERE tenant_id=t AND business_id=p_business AND operation_id=p_operation;
        UPDATE public.reference_cycle_reviews SET resolved_operation_id=coalesce(resolved_operation_id,p_operation)
          WHERE tenant_id=t AND business_id=p_business AND cycle_id=p_cycle;
        RETURN response;
      END $$""")
    op.execute(f"ALTER FUNCTION public.reference_confirm_published_selection({_SELECT}) OWNER TO {_ROLE}")
    op.execute(f"REVOKE ALL ON FUNCTION public.reference_confirm_published_selection({_SELECT}) FROM PUBLIC")
    op.execute(
        f"GRANT EXECUTE ON FUNCTION public.reference_confirm_published_selection({_SELECT}) TO meu_braco_direito_app"
    )


def downgrade():
    op.execute("""LOCK TABLE reference_publication_operations,reference_cycle_reviews,
      reference_provider_effects,reference_real_selection_operations IN ACCESS EXCLUSIVE MODE""")
    op.execute("SET LOCAL row_security=off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_publication_operations)
      OR EXISTS(SELECT 1 FROM reference_cycle_reviews)
      OR EXISTS(SELECT 1 FROM reference_provider_effects WHERE state='completed_published')
      OR EXISTS(SELECT 1 FROM reference_real_selection_operations WHERE decision_confirmation<>'{}'::jsonb)
      OR EXISTS(SELECT 1 FROM outbox_events WHERE event_type='reference.results_published') THEN
      RAISE EXCEPTION 'REFERENCE_PUBLICATION_REQUIRES_FORWARD_RECOVERY'; END IF; END $$""")
    op.execute("SET LOCAL row_security=on")
    op.execute(f"DROP FUNCTION public.reference_confirm_published_selection({_SELECT})")
    op.execute(f"DROP FUNCTION public.reference_publish_shortlist({_PUBLISH})")
    op.execute("DROP POLICY publication_event ON outbox_events")
    prior = import_module("migrations.versions.0100_business_address")
    prior._event_constraint((*prior._EVENTS, "business.address_saved"))
    op.execute("DROP TABLE reference_cycle_reviews,reference_publication_operations")
    op.execute(f"REVOKE UPDATE(response,decision_confirmation) ON reference_real_selection_operations FROM {_ROLE}")
    op.execute(f"REVOKE UPDATE(completed_at) ON reference_provider_searches FROM {_ROLE}")
    op.execute("ALTER TABLE reference_real_selection_operations DROP COLUMN decision_confirmation")
    for table in (
        "reference_provider_places",
        "reference_provider_results",
        "reference_provider_result_candidates",
        "reference_provider_profile_options",
        "reference_real_published_results",
    ):
        op.execute(f"DROP POLICY publication_write ON {table}")
        op.execute(f"REVOKE INSERT ON {table} FROM {_ROLE}")
    op.execute(f"REVOKE SELECT ON reference_provider_places,reference_provider_profile_options FROM {_ROLE}")
    op.execute(f"REVOKE DELETE ON reference_filtered_batch_candidates FROM {_ROLE}")
    op.execute("ALTER TABLE reference_provider_results DROP COLUMN recommendation_status")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_state_check")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_check")
    op.execute("""ALTER TABLE reference_provider_effects
      ADD CONSTRAINT reference_provider_effects_state_check CHECK(state IN
        ('pending','running','uncertain','completed_empty','completed_filtered','failed_definitive')),
      ADD CONSTRAINT reference_provider_effects_check CHECK(
        (state='pending' AND executor_token IS NULL) OR (state<>'pending' AND executor_token IS NOT NULL))""")
