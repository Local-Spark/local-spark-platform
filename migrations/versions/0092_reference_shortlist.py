"""Prepare a private top-ten shortlist; no provider or publication is enabled.

Equal scores are deliberately not resolved here. Runtime execution remains
revoked until the owner chooses a tie rule and the recommendation intent can
bind the resulting immutable shortlist. Temporary observations stay intact.
"""

from alembic import op

revision = "0092_reference_shortlist"
down_revision = "0091_reference_context_fence"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE reference_private_shortlist_headers (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,batch_id uuid NOT NULL,actor_id uuid NOT NULL,
      operation_id uuid NOT NULL,event_id uuid NOT NULL,created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(tenant_id,business_id,batch_id), UNIQUE(tenant_id,business_id,operation_id),
      FOREIGN KEY(tenant_id,business_id,batch_id) REFERENCES reference_filtered_batches(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id))""")
    op.execute("""ALTER TABLE reference_private_shortlist ADD CONSTRAINT reference_shortlist_header_fk
      FOREIGN KEY(tenant_id,business_id,batch_id)
      REFERENCES reference_private_shortlist_headers(tenant_id,business_id,batch_id)""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    op.execute("ALTER TABLE reference_private_shortlist_headers ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reference_private_shortlist_headers FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY reference_shortlist_ledger ON reference_private_shortlist_headers
      TO meu_braco_direito_reference_ledger USING(tenant_id={tenant} AND actor_id={actor})
      WITH CHECK(tenant_id={tenant} AND actor_id={actor})""")
    op.execute("GRANT SELECT,INSERT ON reference_private_shortlist_headers TO meu_braco_direito_reference_ledger")
    op.execute("GRANT INSERT ON reference_private_shortlist TO meu_braco_direito_reference_ledger")
    op.execute(f"""CREATE POLICY reference_reco_insert ON reference_private_shortlist FOR INSERT
      TO meu_braco_direito_reference_ledger WITH CHECK(tenant_id={tenant})""")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed',
       'reference.provider_effect_requested','reference.provider_cost_changed','reference.provider_effect_completed',
       'reference.provider_search_requested','reference.provider_search_cancelled','reference.real_selection_confirmed',
       'reference.private_shortlist_prepared'))""")
    op.execute(f"""CREATE POLICY reference_shortlist_event_emit ON outbox_events FOR INSERT
      TO meu_braco_direito_reference_ledger WITH CHECK(tenant_id={tenant}
        AND event_type='reference.private_shortlist_prepared' AND payload->>'actor_id'={actor}::text)""")
    op.execute("""CREATE FUNCTION public.reference_prepare_shortlist(
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
      END $$""")
    op.execute("""ALTER FUNCTION public.reference_prepare_shortlist(uuid,uuid,uuid,uuid,uuid[])
      OWNER TO meu_braco_direito_reference_ledger""")
    op.execute("""REVOKE ALL ON FUNCTION public.reference_prepare_shortlist(uuid,uuid,uuid,uuid,uuid[])
      FROM PUBLIC,meu_braco_direito_correlator,meu_braco_direito_app""")


def downgrade():
    op.execute("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))")
    op.execute(
        "LOCK TABLE reference_private_shortlist_headers,reference_private_shortlist,outbox_events "
        "IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_private_shortlist_headers) OR
      EXISTS(SELECT 1 FROM outbox_events WHERE event_type='reference.private_shortlist_prepared') THEN
      RAISE EXCEPTION 'REFERENCE_SHORTLIST_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("DROP FUNCTION public.reference_prepare_shortlist(uuid,uuid,uuid,uuid,uuid[])")
    op.execute("DROP POLICY reference_shortlist_event_emit ON outbox_events")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed',
       'reference.provider_effect_requested','reference.provider_cost_changed','reference.provider_effect_completed',
       'reference.provider_search_requested','reference.provider_search_cancelled','reference.real_selection_confirmed'))""")
    op.execute("DROP POLICY reference_reco_insert ON reference_private_shortlist")
    op.execute("REVOKE INSERT ON reference_private_shortlist FROM meu_braco_direito_reference_ledger")
    op.execute("ALTER TABLE reference_private_shortlist DROP CONSTRAINT reference_shortlist_header_fk")
    op.execute("DROP TABLE reference_private_shortlist_headers")
