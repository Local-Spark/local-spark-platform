"""Private, fenced storage of filtered and scored reference observations.

No client access or intent creation is enabled here. Cleanup of this temporary
batch must be added atomically with a future final-result writer.
"""

from alembic import op

revision = "0079_reference_filtered_batch"
down_revision = "0078_reference_jev_guard"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_state_check")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_check")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_effects_state_check
      CHECK(state IN ('pending','running','uncertain','completed_empty','completed_filtered'))""")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_effects_check CHECK(
      (state='pending' AND executor_token IS NULL) OR
      (state IN ('running','uncertain','completed_empty','completed_filtered') AND executor_token IS NOT NULL))""")
    op.execute("""CREATE TABLE reference_filtered_batches (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, actor_id uuid NOT NULL, id uuid NOT NULL,
      search_id uuid NOT NULL, google_effect_id uuid NOT NULL, jev_effect_id uuid NOT NULL,
      source_batch_mac char(64) NOT NULL CHECK(source_batch_mac ~ '^[0-9a-f]{64}$'),
      context_version bigint NOT NULL CHECK(context_version > 0),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(tenant_id,business_id,id), UNIQUE(tenant_id,business_id,search_id),
      UNIQUE(tenant_id,business_id,google_effect_id), UNIQUE(tenant_id,business_id,jev_effect_id),
      FOREIGN KEY(tenant_id,business_id,search_id) REFERENCES reference_provider_searches(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,google_effect_id)
        REFERENCES reference_provider_effects(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,jev_effect_id)
        REFERENCES reference_provider_effects(tenant_id,business_id,id))""")
    op.execute("""CREATE TABLE reference_filtered_batch_candidates (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, actor_id uuid NOT NULL, batch_id uuid NOT NULL,
      candidate_id uuid NOT NULL, position smallint NOT NULL CHECK(position BETWEEN 1 AND 20),
      place_id text NOT NULL CHECK(length(place_id) BETWEEN 1 AND 2048 AND place_id=btrim(place_id)),
      reputation_score numeric NOT NULL CHECK(reputation_score BETWEEN 0 AND 10),
      reputation_formula_version text NOT NULL CHECK(reputation_formula_version='penalized-3.4-v1'),
      PRIMARY KEY(tenant_id,business_id,batch_id,candidate_id),
      UNIQUE(tenant_id,business_id,batch_id,position), UNIQUE(tenant_id,business_id,batch_id,place_id),
      FOREIGN KEY(tenant_id,business_id,batch_id) REFERENCES reference_filtered_batches(tenant_id,business_id,id))""")
    own = (
        "tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND "
        "actor_id=nullif(current_setting('app.actor_id',true),'')::uuid"
    )
    for table in ("reference_filtered_batches", "reference_filtered_batch_candidates"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY reference_filtered_ledger ON {table} TO meu_braco_direito_reference_ledger "
            f"USING({own}) WITH CHECK({own})"
        )
        op.execute(f"GRANT SELECT,INSERT ON {table} TO meu_braco_direito_reference_ledger")
    op.execute("""CREATE FUNCTION public.reference_filtered_commit(
      p_business uuid,p_search uuid,p_batch uuid,p_google uuid,p_google_event uuid,p_google_token uuid,
      p_jev uuid,p_jev_event uuid,p_jev_token uuid,p_source_mac text,p_context bigint,p_candidates jsonb)
      RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        g public.reference_provider_effects%ROWTYPE; j public.reference_provider_effects%ROWTYPE;
        b public.reference_filtered_batches%ROWTYPE; item jsonb; candidate_count integer; actual_count integer;
        search_state text;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_search IS NULL OR p_batch IS NULL
          OR p_google IS NULL OR p_google_event IS NULL OR p_google_token IS NULL OR p_jev IS NULL
          OR p_jev_event IS NULL OR p_jev_token IS NULL OR p_google=p_jev OR p_source_mac IS NULL
          OR p_source_mac !~ '^[0-9a-f]{64}$' OR p_context IS NULL OR p_context < 1
          OR jsonb_typeof(p_candidates) IS DISTINCT FROM 'array' THEN
          RAISE EXCEPTION 'REFERENCE_FILTERED_INVALID'; END IF;
        candidate_count := jsonb_array_length(p_candidates);
        IF candidate_count > 20 THEN RAISE EXCEPTION 'REFERENCE_FILTERED_INVALID'; END IF;
        FOR item IN SELECT value FROM jsonb_array_elements(p_candidates) LOOP
          IF jsonb_typeof(item) IS DISTINCT FROM 'object' OR
             (SELECT count(*) FROM jsonb_object_keys(item))<>4 OR
             NOT (item ?& ARRAY['candidate_id','place_id','reputation_score','reputation_formula_version']) OR
             jsonb_typeof(item->'candidate_id')<>'string' OR
             (item->>'candidate_id') !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' OR
             jsonb_typeof(item->'place_id')<>'string' OR length(item->>'place_id') NOT BETWEEN 1 AND 2048 OR
             (item->>'place_id')<>btrim(item->>'place_id') OR
             jsonb_typeof(item->'reputation_score')<>'string' OR
             (item->>'reputation_score') !~ '^(0|[1-9][0-9]*)(\\.[0-9]+)?$' OR
             (item->>'reputation_score')::numeric NOT BETWEEN 0 AND 10 OR
             item->>'reputation_formula_version'<>'penalized-3.4-v1' THEN
            RAISE EXCEPTION 'REFERENCE_FILTERED_INVALID'; END IF;
        END LOOP;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        PERFORM 1 FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND id IN (p_google,p_jev) ORDER BY id FOR UPDATE;
        SELECT * INTO g FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_google AND provider='google';
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_FILTERED_FENCE_INVALID'; END IF;
        SELECT * INTO j FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_jev AND provider='jev';
        IF NOT FOUND OR g.executor_token IS DISTINCT FROM p_google_token
          OR j.executor_token IS DISTINCT FROM p_jev_token
          OR g.search_id IS DISTINCT FROM p_search OR j.search_id IS DISTINCT FROM p_search
          OR j.parent_google_effect_id IS DISTINCT FROM g.id OR j.source_batch_mac IS DISTINCT FROM p_source_mac
          OR j.pilot_id IS DISTINCT FROM g.pilot_id THEN RAISE EXCEPTION 'REFERENCE_FILTERED_FENCE_INVALID'; END IF;
        SELECT s.state INTO search_state FROM public.reference_provider_searches s WHERE s.tenant_id=t
          AND s.business_id=p_business AND s.actor_id=a AND s.id=p_search AND s.context_version=p_context FOR SHARE;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_FILTERED_SEARCH_INVALID'; END IF;
        IF NOT EXISTS(SELECT 1 FROM public.outbox_events o WHERE o.id=p_google_event AND o.tenant_id=t
          AND o.event_type='reference.provider_effect_requested' AND o.payload=jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',g.id::text)) OR
          NOT EXISTS(SELECT 1 FROM public.outbox_events o WHERE o.id=p_jev_event AND o.tenant_id=t
          AND o.event_type='reference.provider_effect_requested' AND o.payload=jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',j.id::text)) THEN
          RAISE EXCEPTION 'REFERENCE_FILTERED_EVENT_INVALID'; END IF;
        SELECT * INTO b FROM public.reference_filtered_batches WHERE tenant_id=t AND business_id=p_business
          AND search_id=p_search;
        IF FOUND THEN
          IF b.id IS DISTINCT FROM p_batch OR b.actor_id IS DISTINCT FROM a OR b.google_effect_id IS DISTINCT FROM g.id
            OR b.jev_effect_id IS DISTINCT FROM j.id OR b.source_batch_mac IS DISTINCT FROM p_source_mac
            OR b.context_version IS DISTINCT FROM p_context OR g.state<>'completed_filtered'
            OR j.state<>'completed_filtered' THEN RAISE EXCEPTION 'REFERENCE_FILTERED_REPLAY_CONFLICT'; END IF;
          SELECT count(*) INTO actual_count FROM public.reference_filtered_batch_candidates c
            WHERE c.tenant_id=t AND c.business_id=p_business AND c.batch_id=b.id;
          IF actual_count<>candidate_count OR EXISTS(
            SELECT 1 FROM jsonb_array_elements(p_candidates) WITH ORDINALITY x(value,pos)
            LEFT JOIN public.reference_filtered_batch_candidates c ON c.tenant_id=t AND c.business_id=p_business
              AND c.batch_id=b.id AND c.position=x.pos
            WHERE c.candidate_id IS DISTINCT FROM (x.value->>'candidate_id')::uuid
              OR c.place_id IS DISTINCT FROM x.value->>'place_id'
              OR c.reputation_score IS DISTINCT FROM (x.value->>'reputation_score')::numeric
              OR c.reputation_formula_version IS DISTINCT FROM x.value->>'reputation_formula_version') THEN
            RAISE EXCEPTION 'REFERENCE_FILTERED_REPLAY_CONFLICT'; END IF;
          RETURN b.id;
        END IF;
        IF search_state<>'pending' THEN RAISE EXCEPTION 'REFERENCE_FILTERED_SEARCH_INVALID'; END IF;
        IF g.state<>'running' OR j.state<>'running' THEN RAISE EXCEPTION 'REFERENCE_FILTERED_FENCE_INVALID'; END IF;
        PERFORM 1 FROM public.reference_cost_reservations WHERE tenant_id=t AND actor_id=a
          AND business_id=p_business AND effect_id IN (g.id,j.id) AND provider_search_id=p_search
          AND pilot_id=g.pilot_id AND state='claimed' FOR UPDATE;
        GET DIAGNOSTICS actual_count = ROW_COUNT;
        IF actual_count<>2 THEN RAISE EXCEPTION 'REFERENCE_RESERVATION_NOT_FOUND'; END IF;
        INSERT INTO public.reference_filtered_batches
          (tenant_id,business_id,actor_id,id,search_id,google_effect_id,jev_effect_id,source_batch_mac,context_version)
          VALUES(t,p_business,a,p_batch,p_search,g.id,j.id,p_source_mac,p_context);
        INSERT INTO public.reference_filtered_batch_candidates
          (tenant_id,business_id,actor_id,batch_id,candidate_id,position,place_id,reputation_score,reputation_formula_version)
          SELECT t,p_business,a,p_batch,(x.value->>'candidate_id')::uuid,x.pos,
            x.value->>'place_id',(x.value->>'reputation_score')::numeric,x.value->>'reputation_formula_version'
          FROM jsonb_array_elements(p_candidates) WITH ORDINALITY x(value,pos);
        UPDATE public.reference_cost_reservations SET state='uncertain',updated_at=clock_timestamp()
          WHERE tenant_id=t AND actor_id=a AND effect_id IN (g.id,j.id);
        UPDATE public.reference_provider_effects SET state='completed_filtered',updated_at=clock_timestamp()
          WHERE tenant_id=t AND business_id=p_business AND id IN (g.id,j.id);
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_batch,'reference.filtered_committed',p_search);
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          SELECT gen_random_uuid(),t,'reference.provider_effect_completed',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',effect::text)
          FROM (VALUES(g.id),(j.id)) v(effect);
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          SELECT gen_random_uuid(),t,'reference.provider_cost_changed',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',effect::text)
          FROM (VALUES(g.id),(j.id)) v(effect);
        RETURN p_batch;
      END $$""")
    op.execute("""ALTER FUNCTION public.reference_filtered_commit(
      uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,bigint,jsonb) OWNER TO meu_braco_direito_reference_ledger""")
    op.execute("""REVOKE ALL ON FUNCTION public.reference_filtered_commit(
      uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,bigint,jsonb) FROM PUBLIC""")
    # No runtime grant until a later migration also verifies the source MAC
    # durably fixed on the Google effect by the fenced Jev-intent creator.


def downgrade():
    op.execute(
        "LOCK TABLE reference_filtered_batch_candidates,reference_filtered_batches,reference_provider_effects "
        "IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_filtered_batches) OR
      EXISTS(SELECT 1 FROM reference_provider_effects WHERE state='completed_filtered') THEN
      RAISE EXCEPTION 'REFERENCE_FILTERED_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("""DROP FUNCTION public.reference_filtered_commit(
      uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,bigint,jsonb)""")
    op.execute("DROP TABLE reference_filtered_batch_candidates,reference_filtered_batches")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_state_check")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_check")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_effects_state_check
      CHECK(state IN ('pending','running','uncertain','completed_empty'))""")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_effects_check CHECK(
      (state='pending' AND executor_token IS NULL) OR
      (state IN ('running','uncertain','completed_empty') AND executor_token IS NOT NULL))""")
