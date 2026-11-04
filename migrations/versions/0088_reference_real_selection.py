"""Private, fenced real-reference selection awaiting evidenced publication.

No runtime role can execute the selection function or write publication
markers. A later publication slice must establish provenance before either
operation can become reachable from a product route.
"""

from alembic import op

revision = "0088_reference_real_selection"
down_revision = "0087_reference_feed_ledger"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE UNIQUE INDEX reference_provider_candidate_place_identity
      ON reference_provider_result_candidates(tenant_id,business_id,result_id,id,place_id)""")
    op.execute("""CREATE TABLE reference_real_published_results (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,result_id uuid NOT NULL,
      PRIMARY KEY(tenant_id,business_id,result_id),
      FOREIGN KEY(tenant_id,business_id,result_id)
        REFERENCES reference_provider_results(tenant_id,business_id,id))""")
    op.execute("""CREATE TABLE reference_real_selected (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,place_id uuid NOT NULL,
      result_id uuid NOT NULL,candidate_id uuid NOT NULL,
      PRIMARY KEY(tenant_id,business_id,place_id),
      FOREIGN KEY(tenant_id,business_id,result_id)
        REFERENCES reference_real_published_results(tenant_id,business_id,result_id),
      FOREIGN KEY(tenant_id,business_id,result_id,candidate_id,place_id)
        REFERENCES reference_provider_result_candidates(tenant_id,business_id,result_id,id,place_id),
      FOREIGN KEY(tenant_id,business_id,place_id) REFERENCES reference_provider_places(tenant_id,business_id,id))""")
    op.execute("""CREATE TABLE reference_real_selection_operations (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,operation_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),cycle_id uuid NOT NULL,
      selection jsonb NOT NULL CHECK(jsonb_typeof(selection)='array'),
      response jsonb NOT NULL CHECK(jsonb_typeof(response)='object'),event_id uuid NOT NULL,
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(tenant_id,business_id,operation_id),
      FOREIGN KEY(tenant_id,business_id,cycle_id) REFERENCES reference_real_cycles(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    for table in ("reference_real_published_results", "reference_real_selected", "reference_real_selection_operations"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY reference_selection_ledger ON {table} TO meu_braco_direito_reference_ledger "
            f"USING(tenant_id={tenant}) WITH CHECK(tenant_id={tenant})"
        )
    # Publication is not yet implemented; the ledger can only read markers.
    op.execute("GRANT SELECT ON reference_real_published_results TO meu_braco_direito_reference_ledger")
    op.execute("GRANT SELECT,INSERT,DELETE ON reference_real_selected TO meu_braco_direito_reference_ledger")
    op.execute("GRANT SELECT,INSERT ON reference_real_selection_operations TO meu_braco_direito_reference_ledger")
    op.execute(
        "GRANT SELECT,UPDATE(confirmed_at,locked_until) ON reference_real_cycles TO meu_braco_direito_reference_ledger"
    )
    for table in ("reference_provider_results", "reference_provider_result_candidates"):
        op.execute(
            f"CREATE POLICY reference_selection_read ON {table} FOR SELECT TO meu_braco_direito_reference_ledger "
            f"USING(tenant_id={tenant})"
        )
        op.execute(f"GRANT SELECT ON {table} TO meu_braco_direito_reference_ledger")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed',
       'reference.provider_effect_requested','reference.provider_cost_changed','reference.provider_effect_completed',
       'reference.provider_search_requested','reference.provider_search_cancelled','reference.real_selection_confirmed'))""")
    op.execute(f"""CREATE POLICY reference_real_selection_event_emit ON outbox_events FOR INSERT
      TO meu_braco_direito_reference_ledger WITH CHECK(tenant_id={tenant}
        AND event_type='reference.real_selection_confirmed' AND payload->>'actor_id'={actor}::text)""")
    op.execute("""CREATE FUNCTION public.reference_confirm_real_selection(
      p_business uuid,p_operation uuid,p_results uuid[],p_candidates uuid[])
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        head public.reference_real_heads%ROWTYPE; cycle public.reference_real_cycles%ROWTYPE;
        prior public.reference_real_selection_operations%ROWTYPE; canonical jsonb;
        supplied int; unique_pairs int; found_count int; eligible_count int; unique_places int;
        event_id uuid; instant timestamptz; result jsonb;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_operation IS NULL
          OR p_results IS NULL OR p_candidates IS NULL
          OR cardinality(p_results) NOT BETWEEN 1 AND 3
          OR cardinality(p_results) IS DISTINCT FROM cardinality(p_candidates)
          OR array_ndims(p_results) IS DISTINCT FROM 1 OR array_ndims(p_candidates) IS DISTINCT FROM 1
          OR array_position(p_results,NULL) IS NOT NULL OR array_position(p_candidates,NULL) IS NOT NULL THEN
          RAISE EXCEPTION 'REFERENCE_REAL_SELECTION_INVALID'; END IF;
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        SELECT * INTO head FROM public.reference_real_heads
          WHERE tenant_id=t AND business_id=p_business FOR UPDATE;
        IF NOT FOUND OR head.cycle_id IS NULL THEN RAISE EXCEPTION 'REFERENCE_SELECTION_NO_CYCLE'; END IF;
        SELECT count(*),count(DISTINCT (x.result_id,x.candidate_id)),
          jsonb_agg(jsonb_build_object('result_id',x.result_id,'candidate_id',x.candidate_id)
            ORDER BY x.result_id,x.candidate_id)
          INTO supplied,unique_pairs,canonical
          FROM unnest(p_results,p_candidates) AS x(result_id,candidate_id);
        IF supplied<>unique_pairs THEN RAISE EXCEPTION 'REFERENCE_SELECTION_DUPLICATE_ENTITY'; END IF;
        SELECT * INTO prior FROM public.reference_real_selection_operations
          WHERE tenant_id=t AND business_id=p_business AND operation_id=p_operation;
        IF FOUND THEN
          IF prior.actor_id IS DISTINCT FROM a OR prior.selection IS DISTINCT FROM canonical THEN
            RAISE EXCEPTION 'REFERENCE_SELECTION_OPERATION_CONFLICT'; END IF;
          RETURN prior.response;
        END IF;
        SELECT * INTO cycle FROM public.reference_real_cycles
          WHERE tenant_id=t AND business_id=p_business AND id=head.cycle_id FOR UPDATE;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_SELECTION_NO_CYCLE'; END IF;
        SELECT count(c.id),count(DISTINCT c.place_id),
          count(*) FILTER (WHERE c.id IS NOT NULL AND pub.result_id IS NOT NULL AND s.state='completed'
            AND (s.cycle_id=cycle.id OR EXISTS(SELECT 1 FROM public.reference_real_selected old
              WHERE old.tenant_id=t AND old.business_id=p_business AND old.place_id=c.place_id)))
          INTO found_count,unique_places,eligible_count
          FROM unnest(p_results,p_candidates) AS x(result_id,candidate_id)
          LEFT JOIN public.reference_provider_result_candidates c ON c.tenant_id=t AND c.business_id=p_business
            AND c.result_id=x.result_id AND c.id=x.candidate_id
          LEFT JOIN public.reference_provider_results r ON r.tenant_id=c.tenant_id AND r.business_id=c.business_id
            AND r.id=c.result_id
          LEFT JOIN public.reference_real_published_results pub ON pub.tenant_id=r.tenant_id
            AND pub.business_id=r.business_id AND pub.result_id=r.id
          LEFT JOIN public.reference_provider_searches s ON s.tenant_id=r.tenant_id AND s.business_id=r.business_id
            AND s.id=r.search_id;
        IF found_count<>supplied OR eligible_count<>supplied THEN
          RAISE EXCEPTION 'REFERENCE_SELECTION_INVALID_CANDIDATE'; END IF;
        IF unique_places<>supplied THEN RAISE EXCEPTION 'REFERENCE_SELECTION_DUPLICATE_ENTITY'; END IF;
        DELETE FROM public.reference_real_selected WHERE tenant_id=t AND business_id=p_business;
        INSERT INTO public.reference_real_selected(tenant_id,business_id,place_id,result_id,candidate_id)
          SELECT t,p_business,c.place_id,c.result_id,c.id
          FROM unnest(p_results,p_candidates) AS x(result_id,candidate_id)
          JOIN public.reference_provider_result_candidates c ON c.tenant_id=t AND c.business_id=p_business
            AND c.result_id=x.result_id AND c.id=x.candidate_id;
        instant := clock_timestamp();
        UPDATE public.reference_real_cycles SET confirmed_at=coalesce(confirmed_at,instant),
          locked_until=coalesce(locked_until,((instant AT TIME ZONE 'UTC')+interval '6 months') AT TIME ZONE 'UTC')
          WHERE tenant_id=t AND business_id=p_business AND id=cycle.id RETURNING * INTO cycle;
        event_id := gen_random_uuid();
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(event_id,t,'reference.real_selection_confirmed',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_operation::text));
        result := jsonb_build_object('operation_id',p_operation,'cycle_id',cycle.id,
          'locked_until',cycle.locked_until,'selection',canonical);
        INSERT INTO public.reference_real_selection_operations
          (tenant_id,business_id,operation_id,actor_id,cycle_id,selection,response,event_id)
          VALUES(t,p_business,p_operation,a,cycle.id,canonical,result,event_id);
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_operation,'reference.real_selection_confirmed',p_business);
        RETURN result;
      END $$""")
    op.execute("""ALTER FUNCTION public.reference_confirm_real_selection(uuid,uuid,uuid[],uuid[])
      OWNER TO meu_braco_direito_reference_ledger""")
    op.execute("REVOKE ALL ON FUNCTION public.reference_confirm_real_selection(uuid,uuid,uuid[],uuid[]) FROM PUBLIC")


def downgrade():
    op.execute(
        "LOCK TABLE reference_real_published_results,reference_real_selected,"
        "reference_real_selection_operations IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_real_published_results) OR
      EXISTS(SELECT 1 FROM reference_real_selected) OR EXISTS(SELECT 1 FROM reference_real_selection_operations) OR
      EXISTS(SELECT 1 FROM outbox_events WHERE event_type='reference.real_selection_confirmed') THEN
      RAISE EXCEPTION 'REFERENCE_REAL_SELECTION_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("DROP FUNCTION public.reference_confirm_real_selection(uuid,uuid,uuid[],uuid[])")
    op.execute("DROP POLICY reference_real_selection_event_emit ON outbox_events")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed',
       'reference.provider_effect_requested','reference.provider_cost_changed','reference.provider_effect_completed',
       'reference.provider_search_requested','reference.provider_search_cancelled'))""")
    for table in ("reference_provider_results", "reference_provider_result_candidates"):
        op.execute(f"REVOKE SELECT ON {table} FROM meu_braco_direito_reference_ledger")
        op.execute(f"DROP POLICY reference_selection_read ON {table}")
    op.execute(
        "REVOKE UPDATE(confirmed_at,locked_until) ON reference_real_cycles FROM meu_braco_direito_reference_ledger"
    )
    op.execute(
        "DROP TABLE reference_real_selection_operations,reference_real_selected,reference_real_published_results"
    )
    op.execute("DROP INDEX reference_provider_candidate_place_identity")
