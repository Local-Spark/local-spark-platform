"""DRAFT: atomic private similarity projection; no runtime grant.

The selected order is declared by the trusted in-memory caller, not yet proved
by the database against the original Google response. No fallback or publication
is enabled; a separate provenance-enforcing activity is still mandatory.
"""

from alembic import op

revision = "0099_similarity_snapshot"
down_revision = "0098_shared_retry_authorization"
branch_labels = None
depends_on = None

_SIGNATURE = "uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,bigint,jsonb,jsonb"
_LEGACY = "uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,bigint,jsonb"
_ROLE = "meu_braco_direito_reference_ledger"


def upgrade():
    op.execute("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))")
    op.execute("LOCK TABLE reference_provider_effects IN ACCESS EXCLUSIVE MODE")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed',
       'reference.provider_effect_requested','reference.provider_cost_changed','reference.provider_effect_completed',
       'reference.provider_search_requested','reference.provider_search_cancelled','reference.real_selection_confirmed',
       'reference.private_shortlist_prepared','reference.feed_resources_recorded','reference.contacts_not_dispatched',
       'reference.contacts_retry_authorized','reference.similarity_snapshot_recorded'))""")
    op.execute(f"""CREATE POLICY reference_similarity_event ON outbox_events TO {_ROLE}
      USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND event_type='reference.similarity_snapshot_recorded'
        AND payload->>'actor_id'=nullif(current_setting('app.actor_id',true),'')::uuid::text)
      WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND event_type='reference.similarity_snapshot_recorded'
        AND payload->>'actor_id'=nullif(current_setting('app.actor_id',true),'')::uuid::text)""")
    op.execute(f"GRANT SELECT(id,tenant_id,actor_id,operation_id,action,resource_id) ON audit_events TO {_ROLE}")
    op.execute(f"""CREATE POLICY reference_similarity_audit_read ON audit_events FOR SELECT TO {_ROLE}
      USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid
        AND action IN ('reference.filtered_committed','reference.similarity_snapshot_recorded'))""")
    op.execute(
        f"ALTER FUNCTION public.reference_filtered_commit({_LEGACY}) RENAME TO reference_filtered_commit_evidence_inner"
    )
    op.execute(
        f"REVOKE ALL ON FUNCTION public.reference_filtered_commit_evidence_inner({_LEGACY}) "
        "FROM PUBLIC,meu_braco_direito_correlator,meu_braco_direito_app"
    )
    op.execute("""CREATE FUNCTION public.reference_filtered_commit(
      p_business uuid,p_search uuid,p_batch uuid,p_google uuid,p_google_event uuid,p_google_token uuid,
      p_jev uuid,p_jev_event uuid,p_jev_token uuid,p_source_mac text,p_context bigint,p_candidates jsonb)
      RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
      BEGIN
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        IF NOT EXISTS(SELECT 1 FROM public.reference_filtered_batches b WHERE b.tenant_id=t
          AND b.business_id=p_business AND b.actor_id=a AND b.search_id=p_search AND b.id=p_batch) THEN
          RAISE EXCEPTION 'REFERENCE_SIMILARITY_REQUIRED'; END IF;
        RETURN public.reference_filtered_commit_evidence_inner(p_business,p_search,p_batch,p_google,p_google_event,
          p_google_token,p_jev,p_jev_event,p_jev_token,p_source_mac,p_context,p_candidates);
      END $$""")
    op.execute(f"ALTER FUNCTION public.reference_filtered_commit({_LEGACY}) OWNER TO {_ROLE}")
    op.execute(f"REVOKE ALL ON FUNCTION public.reference_filtered_commit({_LEGACY}) FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION public.reference_filtered_commit({_LEGACY}) TO meu_braco_direito_correlator")
    op.execute("""CREATE TABLE reference_similarity_snapshots (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, actor_id uuid NOT NULL,
      batch_id uuid NOT NULL, judgment_count smallint NOT NULL CHECK(judgment_count BETWEEN 0 AND 20),
      judgment_schema text NOT NULL CHECK(judgment_schema='jev-similarity-level-v1'),
      event_id uuid NOT NULL, PRIMARY KEY(tenant_id,business_id,batch_id),
      FOREIGN KEY(tenant_id,business_id,batch_id)
        REFERENCES reference_filtered_batches(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id))""")
    op.execute("""CREATE TABLE reference_similarity_snapshot_items (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,actor_id uuid NOT NULL,batch_id uuid NOT NULL,
      candidate_id uuid NOT NULL,declared_google_position smallint NOT NULL
        CHECK(declared_google_position BETWEEN 1 AND 20),
      judgment text NOT NULL CHECK(judgment IN ('match','no_match','uncertain')),
      similarity_level text NOT NULL CHECK(similarity_level IN ('high','medium','low','unknown')),
      PRIMARY KEY(tenant_id,business_id,batch_id,candidate_id),
      UNIQUE(tenant_id,business_id,batch_id,declared_google_position),
      FOREIGN KEY(tenant_id,business_id,batch_id)
        REFERENCES reference_similarity_snapshots(tenant_id,business_id,batch_id))""")
    own = (
        "tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND "
        "actor_id=nullif(current_setting('app.actor_id',true),'')::uuid"
    )
    for table in ("reference_similarity_snapshots", "reference_similarity_snapshot_items"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY reference_similarity_private ON {table} TO {_ROLE} USING({own}) WITH CHECK({own})")
        op.execute(f"GRANT SELECT,INSERT ON {table} TO {_ROLE}")
    op.execute("""CREATE FUNCTION public.reference_filtered_commit_with_similarity(
      p_business uuid,p_search uuid,p_batch uuid,p_google uuid,p_google_event uuid,p_google_token uuid,
      p_jev uuid,p_jev_event uuid,p_jev_token uuid,p_source_mac text,p_context bigint,p_candidates jsonb,
      p_judgments jsonb) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        item jsonb; item_count integer; stored_count integer; old_batch uuid;
        snapshot_count integer; snapshot_event uuid;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_search IS NULL OR p_batch IS NULL
          OR jsonb_typeof(p_judgments) IS DISTINCT FROM 'array' THEN
          RAISE EXCEPTION 'REFERENCE_SIMILARITY_INVALID'; END IF;
        item_count := jsonb_array_length(p_judgments);
        IF item_count>20 THEN RAISE EXCEPTION 'REFERENCE_SIMILARITY_INVALID'; END IF;
        FOR item IN SELECT value FROM jsonb_array_elements(p_judgments) LOOP
          IF jsonb_typeof(item) IS DISTINCT FROM 'object' OR
            (SELECT count(*) FROM jsonb_object_keys(item))<>3 OR
            NOT (item ?& ARRAY['candidate_id','judgment','similarity_level']) OR
            jsonb_typeof(item->'candidate_id')<>'string' OR
            (item->>'candidate_id') !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' OR
            jsonb_typeof(item->'judgment')<>'string' OR
            item->>'judgment' NOT IN ('match','no_match','uncertain') OR
            jsonb_typeof(item->'similarity_level')<>'string' OR
            item->>'similarity_level' NOT IN ('high','medium','low','unknown') THEN
            RAISE EXCEPTION 'REFERENCE_SIMILARITY_INVALID'; END IF;
        END LOOP;
        IF (SELECT count(DISTINCT value->>'candidate_id') FROM jsonb_array_elements(p_judgments))<>item_count THEN
          RAISE EXCEPTION 'REFERENCE_SIMILARITY_INVALID'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT b.id INTO old_batch FROM public.reference_filtered_batches b WHERE b.tenant_id=t
          AND b.business_id=p_business AND b.search_id=p_search;
        IF FOUND AND NOT EXISTS(SELECT 1 FROM public.reference_similarity_snapshots h WHERE h.tenant_id=t
          AND h.business_id=p_business AND h.batch_id=old_batch AND h.actor_id=a) THEN
          RAISE EXCEPTION 'REFERENCE_SIMILARITY_LEGACY_UNVERIFIED'; END IF;
        PERFORM public.reference_filtered_commit_evidence_inner(p_business,p_search,p_batch,p_google,
          p_google_event,p_google_token,p_jev,p_jev_event,p_jev_token,p_source_mac,p_context,p_candidates);
        SELECT h.judgment_count,h.event_id INTO snapshot_count,snapshot_event
          FROM public.reference_similarity_snapshots h
          WHERE h.tenant_id=t AND h.business_id=p_business AND h.batch_id=p_batch AND h.actor_id=a;
        IF FOUND THEN
          SELECT count(*) INTO stored_count FROM public.reference_similarity_snapshot_items i
            WHERE i.tenant_id=t AND i.business_id=p_business AND i.batch_id=p_batch AND i.actor_id=a;
          IF snapshot_count<>item_count OR stored_count<>item_count OR NOT EXISTS(
            SELECT 1 FROM public.outbox_events e WHERE e.tenant_id=t AND e.id=snapshot_event
              AND e.event_type='reference.similarity_snapshot_recorded' AND e.payload=jsonb_build_object(
                'business_id',p_business::text,'actor_id',a::text,'operation_id',p_batch::text)) OR EXISTS(
            SELECT 1 FROM jsonb_array_elements(p_judgments) WITH ORDINALITY x(value,pos)
            LEFT JOIN public.reference_similarity_snapshot_items i ON i.tenant_id=t AND i.business_id=p_business
              AND i.batch_id=p_batch AND i.actor_id=a AND i.declared_google_position=x.pos
            WHERE i.candidate_id IS DISTINCT FROM (x.value->>'candidate_id')::uuid
              OR i.judgment IS DISTINCT FROM x.value->>'judgment'
              OR i.similarity_level IS DISTINCT FROM x.value->>'similarity_level') THEN
            RAISE EXCEPTION 'REFERENCE_SIMILARITY_REPLAY_CONFLICT'; END IF;
          RETURN p_batch;
        END IF;
        IF EXISTS(SELECT 1 FROM public.reference_filtered_batch_candidates c
          LEFT JOIN jsonb_array_elements(p_judgments) x(value)
            ON (x.value->>'candidate_id')::uuid=c.candidate_id AND x.value->>'judgment'='match'
              AND x.value->>'similarity_level' IN ('high','medium','low')
          WHERE c.tenant_id=t AND c.business_id=p_business AND c.batch_id=p_batch AND c.actor_id=a
            AND x.value IS NULL) THEN RAISE EXCEPTION 'REFERENCE_SIMILARITY_MAPPING_INVALID'; END IF;
        snapshot_event := gen_random_uuid();
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(snapshot_event,t,'reference.similarity_snapshot_recorded',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_batch::text));
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_batch,'reference.similarity_snapshot_recorded',p_search);
        INSERT INTO public.reference_similarity_snapshots
          (tenant_id,business_id,actor_id,batch_id,judgment_count,judgment_schema,event_id)
          VALUES(t,p_business,a,p_batch,item_count,'jev-similarity-level-v1',snapshot_event);
        INSERT INTO public.reference_similarity_snapshot_items
          (tenant_id,business_id,actor_id,batch_id,candidate_id,declared_google_position,judgment,similarity_level)
          SELECT t,p_business,a,p_batch,(x.value->>'candidate_id')::uuid,x.pos,
            x.value->>'judgment',x.value->>'similarity_level'
            FROM jsonb_array_elements(p_judgments) WITH ORDINALITY x(value,pos);
        RETURN p_batch;
      END $$""")
    op.execute(f"ALTER FUNCTION public.reference_filtered_commit_with_similarity({_SIGNATURE}) OWNER TO {_ROLE}")
    op.execute(
        f"REVOKE ALL ON FUNCTION public.reference_filtered_commit_with_similarity({_SIGNATURE}) "
        "FROM PUBLIC,meu_braco_direito_correlator,meu_braco_direito_app"
    )

    op.execute("""CREATE FUNCTION public.reference_similarity_snapshot_recovery(
      p_business uuid,p_search uuid,p_google uuid,p_google_event uuid)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        prior jsonb; b uuid; expected integer; actual integer; items jsonb; snapshot_event uuid;
        filtered_count integer; matched_count integer; filtered jsonb;
      BEGIN
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        prior := public.reference_filtered_recovery(p_business,p_search,p_google,p_google_event);
        IF prior IS NULL OR prior->>'state' IS DISTINCT FROM 'filtered' THEN RETURN NULL; END IF;
        b := (prior->>'batch_id')::uuid;
        IF NOT EXISTS(
          SELECT 1 FROM public.reference_filtered_batches batch
          JOIN public.reference_provider_searches s ON s.tenant_id=batch.tenant_id
            AND s.business_id=batch.business_id AND s.actor_id=batch.actor_id AND s.id=batch.search_id
            AND s.context_version=batch.context_version
          JOIN public.reference_provider_effects g ON g.tenant_id=batch.tenant_id
            AND g.business_id=batch.business_id AND g.actor_id=batch.actor_id AND g.id=batch.google_effect_id
            AND g.search_id=batch.search_id AND g.provider='google' AND g.state='completed_filtered'
            AND g.request_event_id=p_google_event AND g.source_batch_mac=batch.source_batch_mac
          JOIN public.reference_provider_effects j ON j.tenant_id=batch.tenant_id
            AND j.business_id=batch.business_id AND j.actor_id=batch.actor_id AND j.id=batch.jev_effect_id
            AND j.search_id=batch.search_id AND j.provider='jev' AND j.purpose='discovery'
            AND j.state='completed_filtered' AND j.parent_google_effect_id=g.id
            AND j.pilot_id=g.pilot_id AND j.source_batch_mac=batch.source_batch_mac
          JOIN public.reference_cost_reservations rg ON rg.tenant_id=g.tenant_id
            AND rg.business_id=g.business_id AND rg.actor_id=g.actor_id AND rg.effect_id=g.id
            AND rg.provider_search_id=g.search_id AND rg.provider='google' AND rg.pilot_id=g.pilot_id
            AND rg.request_hash=g.request_mac AND rg.reserved_usd_micros=g.reserved_usd_micros
            AND rg.state IN ('uncertain','completed')
          JOIN public.reference_cost_reservations rj ON rj.tenant_id=j.tenant_id
            AND rj.business_id=j.business_id AND rj.actor_id=j.actor_id AND rj.effect_id=j.id
            AND rj.provider_search_id=j.search_id AND rj.provider='jev' AND rj.pilot_id=j.pilot_id
            AND rj.request_hash=j.request_mac AND rj.reserved_usd_micros=j.reserved_usd_micros
            AND rj.state IN ('uncertain','completed')
          JOIN public.outbox_events ge ON ge.tenant_id=g.tenant_id AND ge.id=g.request_event_id
            AND ge.event_type='reference.provider_effect_requested' AND ge.payload=jsonb_build_object(
              'business_id',p_business::text,'actor_id',a::text,'operation_id',g.id::text)
          JOIN public.outbox_events je ON je.tenant_id=j.tenant_id AND je.id=j.request_event_id
            AND je.event_type='reference.provider_effect_requested' AND je.payload=jsonb_build_object(
              'business_id',p_business::text,'actor_id',a::text,'operation_id',j.id::text)
          WHERE batch.tenant_id=t AND batch.business_id=p_business AND batch.actor_id=a
            AND batch.id=b AND batch.search_id=p_search AND batch.google_effect_id=p_google
        ) THEN RAISE EXCEPTION 'REFERENCE_SIMILARITY_RECOVERY_INVALID'; END IF;
        SELECT h.judgment_count,h.event_id INTO expected,snapshot_event FROM public.reference_similarity_snapshots h
          WHERE h.tenant_id=t AND h.business_id=p_business AND h.batch_id=b AND h.actor_id=a;
        IF NOT FOUND THEN RETURN NULL; END IF;
        IF NOT EXISTS(SELECT 1 FROM public.audit_events au WHERE au.tenant_id=t AND au.actor_id=a
          AND au.operation_id=b AND au.resource_id=p_search AND au.action='reference.filtered_committed')
          OR NOT EXISTS(SELECT 1 FROM public.audit_events au WHERE au.tenant_id=t AND au.actor_id=a
          AND au.operation_id=b AND au.resource_id=p_search AND au.action='reference.similarity_snapshot_recorded') THEN
          RAISE EXCEPTION 'REFERENCE_SIMILARITY_RECOVERY_INVALID'; END IF;
        IF NOT EXISTS(SELECT 1 FROM public.outbox_events e WHERE e.tenant_id=t AND e.id=snapshot_event
          AND e.event_type='reference.similarity_snapshot_recorded' AND e.payload=jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',b::text)) THEN
          RAISE EXCEPTION 'REFERENCE_SIMILARITY_RECOVERY_INVALID'; END IF;
        SELECT count(*),coalesce(jsonb_agg(jsonb_build_object('candidate_id',i.candidate_id::text,
          'declared_google_position',i.declared_google_position,'judgment',i.judgment,
          'similarity_level',i.similarity_level) ORDER BY i.declared_google_position),'[]'::jsonb)
          INTO actual,items FROM public.reference_similarity_snapshot_items i
          WHERE i.tenant_id=t AND i.business_id=p_business AND i.batch_id=b AND i.actor_id=a;
        IF actual<>expected THEN RAISE EXCEPTION 'REFERENCE_SIMILARITY_RECOVERY_INVALID'; END IF;
        SELECT count(*),count(i.candidate_id),coalesce(jsonb_agg(jsonb_build_object(
          'candidate_id',c.candidate_id::text,'filtered_position',c.position,'place_id',c.place_id,
          'reputation_score',c.reputation_score,'reputation_formula_version',c.reputation_formula_version)
          ORDER BY c.position),'[]'::jsonb) INTO filtered_count,matched_count,filtered
          FROM public.reference_filtered_batch_candidates c
          LEFT JOIN public.reference_similarity_snapshot_items i ON i.tenant_id=c.tenant_id
            AND i.business_id=c.business_id AND i.batch_id=c.batch_id AND i.actor_id=c.actor_id
            AND i.candidate_id=c.candidate_id AND i.judgment='match'
            AND i.similarity_level IN ('high','medium','low')
          WHERE c.tenant_id=t AND c.business_id=p_business AND c.batch_id=b AND c.actor_id=a;
        IF filtered_count<>matched_count THEN RAISE EXCEPTION 'REFERENCE_SIMILARITY_RECOVERY_INVALID'; END IF;
        RETURN jsonb_build_object('batch_id',b::text,'judgments',items,'filtered_candidates',filtered,
          'source_order_verified',false,'provider_response_verified',false);
      END $$""")
    op.execute(f"ALTER FUNCTION public.reference_similarity_snapshot_recovery(uuid,uuid,uuid,uuid) OWNER TO {_ROLE}")
    op.execute(
        "REVOKE ALL ON FUNCTION public.reference_similarity_snapshot_recovery(uuid,uuid,uuid,uuid) "
        "FROM PUBLIC,meu_braco_direito_correlator,meu_braco_direito_app"
    )


def downgrade():
    op.execute("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))")
    op.execute(
        "LOCK TABLE reference_similarity_snapshots,reference_similarity_snapshot_items,outbox_events "
        "IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_similarity_snapshots) OR
      EXISTS(SELECT 1 FROM outbox_events WHERE event_type='reference.similarity_snapshot_recorded') THEN
      RAISE EXCEPTION 'REFERENCE_SIMILARITY_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("DROP FUNCTION public.reference_similarity_snapshot_recovery(uuid,uuid,uuid,uuid)")
    op.execute(f"DROP FUNCTION public.reference_filtered_commit_with_similarity({_SIGNATURE})")
    op.execute("DROP TABLE reference_similarity_snapshot_items,reference_similarity_snapshots")
    op.execute(f"DROP FUNCTION public.reference_filtered_commit({_LEGACY})")
    op.execute(
        f"ALTER FUNCTION public.reference_filtered_commit_evidence_inner({_LEGACY}) RENAME TO reference_filtered_commit"
    )
    op.execute(f"REVOKE ALL ON FUNCTION public.reference_filtered_commit({_LEGACY}) FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION public.reference_filtered_commit({_LEGACY}) TO meu_braco_direito_correlator")
    op.execute("DROP POLICY reference_similarity_event ON outbox_events")
    op.execute("DROP POLICY reference_similarity_audit_read ON audit_events")
    op.execute(f"REVOKE SELECT(id,tenant_id,actor_id,operation_id,action,resource_id) ON audit_events FROM {_ROLE}")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed',
       'reference.provider_effect_requested','reference.provider_cost_changed','reference.provider_effect_completed',
       'reference.provider_search_requested','reference.provider_search_cancelled','reference.real_selection_confirmed',
       'reference.private_shortlist_prepared','reference.feed_resources_recorded','reference.contacts_not_dispatched',
       'reference.contacts_retry_authorized'))""")
