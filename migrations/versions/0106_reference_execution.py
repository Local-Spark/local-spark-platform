"""Wire the trusted discovery activity to the existing provider ledger.

No provider is enabled by this migration. Runtime credentials and the explicit
pilot budget remain mandatory. Persisted outputs contain only our classifications,
selected IDs and independent Instagram handles; raw Google responses are excluded.
"""

from alembic import op

revision = "0106_reference_execution"
down_revision = "0105_reference_contacts_runs"
branch_labels = None
depends_on = None

_ROLE = "meu_braco_direito_reference_ledger"
_RUNTIME = "meu_braco_direito_correlator"


def _function(signature):
    op.execute(f"ALTER FUNCTION public.{signature} OWNER TO {_ROLE}")
    op.execute(f"REVOKE ALL ON FUNCTION public.{signature} FROM PUBLIC,meu_braco_direito_app")
    op.execute(f"GRANT EXECUTE ON FUNCTION public.{signature} TO {_RUNTIME}")


def upgrade():
    op.execute("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))")
    op.execute("""ALTER TABLE reference_provider_searches ADD COLUMN execution_status text NOT NULL DEFAULT 'pending'
      CHECK(execution_status IN ('pending','running','awaiting_own_review','contacts_pending',
          'type_mapping_unavailable',
        'provider_uncertain','contacts_failed','completed','radius_successor','empty_exhausted','disabled','unavailable'))""")
    op.execute(f"GRANT UPDATE(execution_status) ON reference_provider_searches TO {_ROLE}")
    op.execute("GRANT SELECT(execution_status) ON reference_provider_searches TO meu_braco_direito_app")
    op.execute("""DO $$ DECLARE expression text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO expression FROM pg_constraint
        WHERE conrelid='public.outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE public.outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE public.outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' ||
        expression || ') OR event_type=''reference.execution_changed'')';
    END $$""")
    op.execute(f"""CREATE POLICY reference_execution_event ON outbox_events FOR INSERT TO {_ROLE}
      WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND event_type='reference.execution_changed'
        AND payload->>'actor_id'=nullif(current_setting('app.actor_id',true),'')::uuid::text)""")
    op.execute("""CREATE FUNCTION public.reference_execution_progress(
      p_business uuid,p_search uuid,p_event uuid,p_status text)
      RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;
        s public.reference_provider_searches%ROWTYPE; operation uuid;
      BEGIN
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_search FOR UPDATE;
        IF s.id IS NULL OR s.request_event_id IS DISTINCT FROM p_event OR p_status IS NULL
          OR p_status NOT IN ('running','awaiting_own_review','contacts_pending','type_mapping_unavailable',
            'provider_uncertain','contacts_failed','completed','radius_successor','disabled','unavailable') THEN
          RAISE EXCEPTION 'REFERENCE_EXECUTION_INVALID'; END IF;
        IF s.execution_status IN ('empty_exhausted','completed') OR s.execution_status=p_status THEN RETURN; END IF;
        operation:=gen_random_uuid();
        UPDATE public.reference_provider_searches SET execution_status=p_status
          WHERE tenant_id=t AND business_id=p_business AND id=p_search;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,operation,'reference.execution_changed',p_search);
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload) VALUES(gen_random_uuid(),t,
          'reference.execution_changed',
          jsonb_build_object('business_id',p_business::text,'actor_id',a::text,'operation_id',operation::text));
      END $$""")
    _function("reference_execution_progress(uuid,uuid,uuid,text)")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_effect_purpose")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_effect_purpose CHECK(
      (purpose IN ('discovery','mapping') AND recommendation_batch_id IS NULL AND shortlist_mac IS NULL
        AND (purpose<>'mapping' OR provider='jev')) OR
      (purpose='recommendation' AND provider='jev' AND recommendation_batch_id IS NOT NULL
        AND shortlist_mac IS NOT NULL AND shortlist_mac ~ '^[0-9a-f]{64}$'))""")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_jev_parent")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_jev_parent CHECK(
      (provider='google' AND parent_google_effect_id IS NULL AND
        (source_batch_mac IS NULL OR source_batch_mac ~ '^[0-9a-f]{64}$')) OR
      (provider='jev' AND purpose='mapping' AND parent_google_effect_id IS NULL
        AND source_batch_mac IS NOT NULL AND source_batch_mac ~ '^[0-9a-f]{64}$') OR
      (provider IN ('jev','apify') AND purpose<>'mapping' AND parent_google_effect_id IS NOT NULL
        AND source_batch_mac IS NOT NULL AND source_batch_mac ~ '^[0-9a-f]{64}$'))""")
    op.execute("""CREATE UNIQUE INDEX reference_mapping_per_search
      ON reference_provider_effects(tenant_id,business_id,search_id) WHERE purpose='mapping'""")
    # The original trigger continues to protect similarity/recommendation parents.
    op.execute("""DO $$ DECLARE body text; BEGIN
      SELECT pg_get_functiondef('public.reference_jev_require_parent_batch()'::regprocedure) INTO body;
      body := replace(body, 'IF NEW.provider=''jev'' AND OLD.state=''pending''',
        'IF NEW.provider=''jev'' AND NEW.purpose<>''mapping'' AND OLD.state=''pending''');
      EXECUTE body;
    END $$""")
    op.execute("""CREATE TABLE reference_provider_outputs (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,actor_id uuid NOT NULL,
      effect_id uuid NOT NULL,kind text NOT NULL CHECK(kind IN ('mapping','recommendation','contacts')),
      output jsonb NOT NULL CHECK(jsonb_typeof(output)='object'),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(tenant_id,business_id,effect_id),
      FOREIGN KEY(tenant_id,business_id,effect_id) REFERENCES reference_provider_effects(tenant_id,business_id,id))""")
    own = (
        "tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND "
        "actor_id=nullif(current_setting('app.actor_id',true),'')::uuid"
    )
    op.execute("ALTER TABLE reference_provider_outputs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reference_provider_outputs FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY reference_output_private ON reference_provider_outputs TO {_ROLE} "
        f"USING({own}) WITH CHECK({own})"
    )
    op.execute(f"GRANT SELECT,INSERT ON reference_provider_outputs TO {_ROLE}")
    op.execute(f"GRANT INSERT ON reference_contacts_lookups,reference_contacts_effect_links TO {_ROLE}")
    op.execute("""CREATE FUNCTION public.reference_stage_claim(
      p_business uuid,p_search uuid,p_stage text,p_intent jsonb)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        s public.reference_provider_searches%ROWTYPE; b public.reference_filtered_batches%ROWTYPE;
        e public.reference_provider_effects%ROWTYPE; l public.reference_contacts_lookups%ROWTYPE;
        c public.reference_filtered_batch_candidates%ROWTYPE;
        effect uuid := (p_intent->>'effect')::uuid; ev uuid := (p_intent->>'event')::uuid;
        pilot uuid := (p_intent->>'pilot')::uuid; mac text := p_intent->>'mac';
        amount bigint := (p_intent->>'amount')::bigint; charge text := p_intent->>'charge';
        key text := p_intent->>'key'; tariff text := p_intent->>'tariff'; credential text := p_intent->>'credential';
        provider text; parent uuid; source text; batch uuid; lookup uuid; result jsonb; previous uuid; attempt int;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_search IS NULL OR p_stage IS NULL
          OR p_stage NOT IN ('mapping','recommendation','contacts') OR effect IS NULL OR ev IS NULL
          OR pilot IS NULL OR mac IS NULL OR mac !~ '^[0-9a-f]{64}$'
          OR amount IS NULL OR amount NOT BETWEEN 1 AND 5000000
          OR key IS NULL OR key !~ '^[A-Za-z0-9_.-]{1,64}$'
          OR tariff IS NULL OR tariff !~ '^[A-Za-z0-9_.-]{1,64}$'
          OR credential IS NULL OR credential !~ '^[A-Za-z0-9_.-]{1,64}$'
          OR charge IS NULL THEN RAISE EXCEPTION 'REFERENCE_STAGE_INVALID'; END IF;
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        PERFORM public.reference_assert_business_identity(p_business,p_search);
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_search FOR SHARE;
        IF s.id IS NULL OR s.state<>'pending' THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_SEARCH_INACTIVE'; END IF;
        IF p_stage='mapping' THEN
          provider := 'jev'; source := s.request_mac;
          IF charge !~ '^jev-model:[A-Za-z0-9_.-]{1,120}$' THEN RAISE EXCEPTION 'REFERENCE_STAGE_INVALID'; END IF;
        ELSE
          SELECT * INTO b FROM public.reference_filtered_batches WHERE tenant_id=t AND business_id=p_business
            AND actor_id=a AND search_id=p_search AND id=(p_intent->>'batch')::uuid;
          IF b.id IS NULL OR b.context_version<>s.context_version OR NOT EXISTS(
            SELECT 1 FROM public.reference_private_shortlist_headers h WHERE h.tenant_id=t
              AND h.business_id=p_business AND h.batch_id=b.id AND h.actor_id=a) THEN
            RAISE EXCEPTION 'REFERENCE_STAGE_BATCH_INVALID'; END IF;
          batch := b.id; parent := b.google_effect_id; source := b.source_batch_mac;
          IF p_stage='recommendation' THEN
            provider := 'jev';
            IF charge !~ '^jev-model:[A-Za-z0-9_.-]{1,120}$' THEN RAISE EXCEPTION 'REFERENCE_STAGE_INVALID'; END IF;
          ELSE
            provider := 'apify';
            IF charge !~ '^apify-place-contacts:[0-9]+[.][0-9]+[.][0-9]+$' THEN
              RAISE EXCEPTION 'REFERENCE_STAGE_INVALID'; END IF;
            SELECT fc.* INTO c FROM public.reference_filtered_batch_candidates fc
              JOIN public.reference_private_shortlist q USING(tenant_id,business_id,batch_id,candidate_id)
              WHERE fc.tenant_id=t AND fc.business_id=p_business AND fc.batch_id=b.id
                AND fc.candidate_id=(p_intent->>'candidate')::uuid;
            IF c.candidate_id IS NULL THEN RAISE EXCEPTION 'REFERENCE_STAGE_CANDIDATE_INVALID'; END IF;
            SELECT * INTO l FROM public.reference_contacts_lookups WHERE tenant_id=t AND business_id=p_business
              AND cycle_id=s.cycle_id AND
          public.reference_place_id_sha256(place_id)=public.reference_place_id_sha256(c.place_id);
            IF l.id IS NOT NULL AND (l.search_id<>p_search OR l.candidate_id<>c.candidate_id) THEN
              RETURN jsonb_build_object('created',false,'state','cached','lookup',l.id);
            END IF;
            lookup := coalesce(l.id,(p_intent->>'lookup')::uuid);
            SELECT effect_id,attempt_no+1 INTO previous,attempt FROM public.reference_contacts_effect_links
              WHERE tenant_id=t AND business_id=p_business AND lookup_id=lookup ORDER BY attempt_no DESC LIMIT 1;
            attempt:=coalesce(attempt,1);
            IF lookup IS NULL THEN RAISE EXCEPTION 'REFERENCE_STAGE_INVALID'; END IF;
          END IF;
        END IF;
        SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business AND
          id=effect;
        IF e.id IS NULL THEN
          INSERT INTO public.outbox_events(id,tenant_id,event_type,payload) VALUES(ev,t,
          'reference.provider_effect_requested',
            jsonb_build_object('business_id',p_business::text,'actor_id',a::text,'operation_id',effect::text));
          INSERT INTO public.reference_provider_effects(id,tenant_id,business_id,actor_id,search_id,pilot_id,provider,
            request_mac,key_version,tariff_version,credential_version,field_mask,reserved_usd_micros,state,
            parent_google_effect_id,source_batch_mac,request_event_id,purpose,recommendation_batch_id,shortlist_mac)
            VALUES(effect,t,p_business,a,p_search,pilot,provider,mac,key,tariff,credential,charge,amount,'pending',
              parent,source,ev,CASE WHEN p_stage='contacts' THEN 'discovery' ELSE p_stage END,
              CASE WHEN p_stage='recommendation' THEN batch ELSE NULL END,
              CASE WHEN p_stage='recommendation' THEN mac ELSE NULL END);
          IF p_stage='contacts' THEN
            IF l.id IS NULL THEN
              INSERT INTO public.reference_contacts_lookups(tenant_id,business_id,id,actor_id,cycle_id,search_id,
          batch_id,candidate_id,place_id)
                VALUES(t,p_business,lookup,a,s.cycle_id,p_search,batch,c.candidate_id,c.place_id);
            END IF;
            INSERT INTO public.reference_contacts_effect_links(tenant_id,business_id,lookup_id,effect_id,
          attempt_no,previous_effect_id)
              VALUES(t,p_business,lookup,effect,attempt,previous);
          END IF;
          INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
            VALUES(t,a,effect,'reference.provider_stage_admitted',p_search);
        ELSE
          IF e.actor_id<>a OR e.search_id<>p_search OR e.provider<>provider OR e.pilot_id<>pilot
            OR e.request_event_id<>ev OR e.request_mac<>mac OR e.source_batch_mac<>source
            OR e.parent_google_effect_id IS DISTINCT FROM parent
            OR e.purpose<>(CASE WHEN p_stage='contacts' THEN 'discovery' ELSE p_stage END) THEN
            RAISE EXCEPTION 'REFERENCE_STAGE_CONFLICT'; END IF;
        END IF;
        IF p_stage='recommendation' THEN
          result := public.reference_reco_claim(effect,ev,mac,p_business,p_search,pilot,amount,key,tariff,
          credential,charge,
            b.google_effect_id,b.jev_effect_id,b.id,mac,s.context_version);
        ELSIF p_stage='contacts' THEN
          result := public.reference_contacts_claim(p_business,lookup,effect,ev,mac,pilot,amount,key,tariff,
          credential,charge);
        ELSE
          result := public.reference_provider_claim(effect,ev,mac,p_business,p_search,pilot,amount,key,tariff,
          credential,charge);
        END IF;
        RETURN result || jsonb_build_object('event',ev,'lookup',lookup);
      END $$""")
    _function("reference_stage_claim(uuid,uuid,text,jsonb)")
    op.execute("""CREATE FUNCTION public.reference_record_output(
      p_business uuid,p_effect uuid,p_token uuid,p_kind text,p_output jsonb)
      RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        e public.reference_provider_effects%ROWTYPE; previous public.reference_provider_outputs%ROWTYPE; item jsonb;
      BEGIN
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_effect FOR UPDATE;
        IF e.id IS NULL OR e.executor_token IS DISTINCT FROM p_token OR e.state NOT IN
          ('running','uncertain','completed_filtered','completed_published') OR jsonb_typeof(p_output) IS
          DISTINCT FROM 'object'
          OR p_kind IS NULL OR p_kind NOT IN ('mapping','recommendation','contacts') THEN
          RAISE EXCEPTION 'REFERENCE_OUTPUT_INVALID'; END IF;
        IF p_kind='mapping' THEN
          IF e.purpose<>'mapping' OR (SELECT count(*) FROM jsonb_object_keys(p_output))<>3
            OR NOT p_output ?& ARRAY['state','types','taxonomy_version']
            OR p_output->>'state' NOT IN ('mapped','uncertain','no_match')
            OR jsonb_typeof(p_output->'types') IS DISTINCT FROM 'array'
            OR jsonb_array_length(p_output->'types')>50
            OR jsonb_typeof(p_output->'taxonomy_version') IS DISTINCT FROM 'string'
            OR length(p_output->>'taxonomy_version') NOT BETWEEN 1 AND 64 THEN
            RAISE EXCEPTION 'REFERENCE_OUTPUT_INVALID'; END IF;
          FOR item IN SELECT value FROM jsonb_array_elements(p_output->'types') LOOP
            IF jsonb_typeof(item)<>'string' OR item#>>'{}' !~ '^[a-z][a-z0-9_]{0,79}$' THEN
              RAISE EXCEPTION 'REFERENCE_OUTPUT_INVALID'; END IF;
          END LOOP;
        ELSIF p_kind='recommendation' THEN
          IF e.purpose<>'recommendation' OR (SELECT count(*) FROM jsonb_object_keys(p_output))<>1
            OR jsonb_typeof(p_output->'candidate_ids') IS DISTINCT FROM 'array'
            OR jsonb_array_length(p_output->'candidate_ids')>3 THEN RAISE EXCEPTION 'REFERENCE_OUTPUT_INVALID'; END IF;
          IF (SELECT count(DISTINCT value) FROM jsonb_array_elements_text(p_output->'candidate_ids'))<>
            jsonb_array_length(p_output->'candidate_ids') THEN RAISE EXCEPTION 'REFERENCE_OUTPUT_INVALID'; END IF;
          FOR item IN SELECT value FROM jsonb_array_elements(p_output->'candidate_ids') LOOP
            IF NOT EXISTS(SELECT 1 FROM public.reference_private_shortlist WHERE tenant_id=t AND business_id=p_business
              AND batch_id=e.recommendation_batch_id AND candidate_id=(item#>>'{}')::uuid) THEN
              RAISE EXCEPTION 'REFERENCE_OUTPUT_INVALID'; END IF;
          END LOOP;
        ELSE
          IF e.provider<>'apify' OR (SELECT count(*) FROM jsonb_object_keys(p_output))<>2
            OR NOT p_output ?& ARRAY['handles','primary_handle']
            OR jsonb_typeof(p_output->'handles') IS DISTINCT FROM 'array'
            OR jsonb_array_length(p_output->'handles')>100
            OR jsonb_typeof(p_output->'primary_handle') NOT IN ('string','null') THEN
            RAISE EXCEPTION 'REFERENCE_OUTPUT_INVALID'; END IF;
          FOR item IN SELECT value FROM jsonb_array_elements(p_output->'handles') LOOP
            IF jsonb_typeof(item)<>'string' OR item#>>'{}' !~ '^[a-z0-9_][a-z0-9_.]{0,29}$' THEN
              RAISE EXCEPTION 'REFERENCE_OUTPUT_INVALID'; END IF;
          END LOOP;
          IF p_output->>'primary_handle' IS NOT NULL AND NOT (p_output->'handles') ? (p_output->>'primary_handle') THEN
            RAISE EXCEPTION 'REFERENCE_OUTPUT_INVALID'; END IF;
        END IF;
        SELECT * INTO previous FROM public.reference_provider_outputs WHERE tenant_id=t AND
          business_id=p_business AND effect_id=p_effect;
        IF previous.effect_id IS NOT NULL THEN
          IF previous.kind<>p_kind OR previous.output<>p_output THEN RAISE EXCEPTION
          'REFERENCE_OUTPUT_CONFLICT'; END IF;
          RETURN;
        END IF;
        INSERT INTO public.reference_provider_outputs(tenant_id,business_id,actor_id,effect_id,kind,output)
          VALUES(t,p_business,a,p_effect,p_kind,p_output);
        IF p_kind='mapping' THEN UPDATE public.reference_provider_effects SET state='completed_filtered',
          updated_at=clock_timestamp()
          WHERE tenant_id=t AND business_id=p_business AND id=p_effect; END IF;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_effect,'reference.provider_output_recorded',p_effect);
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload) VALUES(gen_random_uuid(),t,
          'reference.provider_effect_completed',
          jsonb_build_object('business_id',p_business::text,'actor_id',a::text,'operation_id',p_effect::text));
      END $$""")
    _function("reference_record_output(uuid,uuid,uuid,text,jsonb)")
    op.execute("""CREATE FUNCTION public.reference_execution_state(p_business uuid,p_search uuid,p_event uuid)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        s public.reference_provider_searches%ROWTYPE; b public.reference_filtered_batches%ROWTYPE;
      BEGIN
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business AND
          actor_id=a AND id=p_search;
        IF s.id IS NULL OR s.request_event_id IS DISTINCT FROM p_event THEN RAISE EXCEPTION
          'REFERENCE_EXECUTION_INVALID'; END IF;
        SELECT * INTO b FROM public.reference_filtered_batches WHERE tenant_id=t AND business_id=p_business AND
          actor_id=a AND search_id=p_search;
        RETURN jsonb_build_object('state',s.state,'execution_status',s.execution_status,
          'cycle_id',s.cycle_id,'context_version',s.context_version,
          'request_mac',s.request_mac,'batch_id',b.id,'source_batch_mac',b.source_batch_mac,
          'effects',coalesce((SELECT jsonb_agg(jsonb_build_object('id',e.id,'event',e.request_event_id,
          'provider',e.provider,
            'purpose',e.purpose,'state',e.state,'token',e.executor_token,'output',o.output,
            'candidate_id',l.candidate_id,'attempt_no',x.attempt_no))
            FROM public.reference_provider_effects e LEFT JOIN public.reference_provider_outputs o
              ON o.tenant_id=e.tenant_id AND o.business_id=e.business_id AND o.effect_id=e.id
            LEFT JOIN public.reference_contacts_effect_links x ON x.tenant_id=e.tenant_id AND
          x.business_id=e.business_id AND x.effect_id=e.id
            LEFT JOIN public.reference_contacts_lookups l ON l.tenant_id=x.tenant_id AND
          l.business_id=x.business_id AND l.id=x.lookup_id
            WHERE e.tenant_id=t AND e.business_id=p_business AND e.actor_id=a AND e.search_id=p_search),'[]'::jsonb),
          'candidates',coalesce((SELECT jsonb_agg(jsonb_build_object('candidate_id',c.candidate_id,'place_id',
          c.place_id,
            'reputation_score',c.reputation_score::text,'reputation_formula_version',c.reputation_formula_version,
            'similarity_level',j.similarity_level,'source_position',j.declared_google_position,
            'contacts_cache',coalesce((SELECT CASE WHEN EXISTS(SELECT 1 FROM public.reference_provider_results pr
                JOIN public.reference_real_published_results pp ON pp.tenant_id=pr.tenant_id AND
          pp.business_id=pr.business_id AND pp.result_id=pr.id
                WHERE pr.tenant_id=t AND pr.business_id=p_business AND pr.search_id=l.search_id) THEN
          'completed' ELSE 'pending' END
              FROM public.reference_contacts_lookups l WHERE l.tenant_id=t AND l.business_id=p_business
                AND l.cycle_id=s.cycle_id AND l.search_id<>s.id AND l.place_id=c.place_id),'none')) ORDER BY
          j.declared_google_position)
            FROM public.reference_filtered_batch_candidates c JOIN public.reference_similarity_snapshot_items j
              USING(tenant_id,business_id,batch_id,candidate_id)
            WHERE c.tenant_id=t AND c.business_id=p_business AND c.batch_id=b.id),'[]'::jsonb));
      END $$""")
    _function("reference_execution_state(uuid,uuid,uuid)")
    _terminal_retries()
    _release_unmapped_search()
    op.execute(
        f"GRANT EXECUTE ON FUNCTION public.reference_prepare_shortlist(uuid,uuid,uuid,uuid,uuid[]) TO {_RUNTIME}"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION public.reference_publish_shortlist("
        "uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,jsonb) "
        f"TO {_RUNTIME}"
    )


def downgrade():
    op.execute("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))")
    op.execute("LOCK TABLE reference_provider_outputs,reference_provider_effects IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security=off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_provider_outputs) OR
      EXISTS(SELECT 1 FROM reference_provider_effects WHERE purpose='mapping') OR
      EXISTS(SELECT 1 FROM reference_execution_retry_operations) OR
      EXISTS(SELECT 1 FROM reference_contacts_failure_proofs WHERE reason='terminal_failed') THEN
      RAISE EXCEPTION 'REFERENCE_EXECUTION_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security=on")
    for signature in (
        "reference_execution_state(uuid,uuid,uuid)",
        "reference_record_output(uuid,uuid,uuid,text,jsonb)",
        "reference_stage_claim(uuid,uuid,text,jsonb)",
    ):
        op.execute(f"DROP FUNCTION public.{signature}")
    op.execute(
        f"REVOKE EXECUTE ON FUNCTION public.reference_prepare_shortlist(uuid,uuid,uuid,uuid,uuid[]) FROM {_RUNTIME}"
    )
    op.execute(
        "REVOKE EXECUTE ON FUNCTION public.reference_publish_shortlist("
        "uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,jsonb) "
        f"FROM {_RUNTIME}"
    )
    op.execute("DROP FUNCTION public.reference_release_unmapped_search(uuid,uuid,uuid,uuid)")
    _undo_terminal_retries()
    op.execute("DROP FUNCTION public.reference_execution_progress(uuid,uuid,uuid,text)")
    op.execute("DROP POLICY reference_execution_event ON outbox_events")
    op.execute("ALTER TABLE reference_provider_searches DROP COLUMN execution_status")
    op.execute("DROP TABLE reference_provider_outputs")
    op.execute("DROP INDEX reference_mapping_per_search")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_effect_purpose")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_effect_purpose CHECK(
      (purpose='discovery' AND recommendation_batch_id IS NULL AND shortlist_mac IS NULL) OR
      (purpose='recommendation' AND provider='jev' AND recommendation_batch_id IS NOT NULL
        AND shortlist_mac IS NOT NULL AND shortlist_mac ~ '^[0-9a-f]{64}$'))""")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_jev_parent")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_jev_parent CHECK(
      (provider='google' AND parent_google_effect_id IS NULL AND
        (source_batch_mac IS NULL OR source_batch_mac ~ '^[0-9a-f]{64}$')) OR
      (provider IN ('jev','apify') AND parent_google_effect_id IS NOT NULL
        AND source_batch_mac IS NOT NULL AND source_batch_mac ~ '^[0-9a-f]{64}$'))""")
    op.execute("""DO $$ DECLARE body text; BEGIN
      SELECT pg_get_functiondef('public.reference_jev_require_parent_batch()'::regprocedure) INTO body;
      EXECUTE replace(body,' AND NEW.purpose<>''mapping''','');
    END $$""")
    op.execute(f"REVOKE INSERT ON reference_contacts_lookups,reference_contacts_effect_links FROM {_ROLE}")


def _terminal_retries():
    op.execute(
        "ALTER TABLE reference_contacts_failure_proofs DROP CONSTRAINT reference_contacts_failure_proofs_reason_check"
    )
    op.execute("""ALTER TABLE reference_contacts_failure_proofs ADD CONSTRAINT
      reference_contacts_failure_proofs_reason_check
      CHECK(reason IN ('not_dispatched','terminal_failed'))""")
    op.execute("""DO $$ DECLARE expression text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO expression FROM pg_constraint
        WHERE conrelid='public.outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE public.outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE public.outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' ||
        expression ||
          ') OR event_type IN (''reference.contacts_terminal_failed'',''reference.provider_retry_requested''))';
    END $$""")
    op.execute(f"""CREATE POLICY reference_terminal_failure_event ON outbox_events TO {_ROLE}
      USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND event_type='reference.contacts_terminal_failed')
      WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND event_type='reference.contacts_terminal_failed'
        AND payload->>'actor_id'=nullif(current_setting('app.actor_id',true),'')::uuid::text)""")
    op.execute("""CREATE POLICY reference_terminal_failure_proof_read ON outbox_events FOR SELECT
      TO meu_braco_direito_reference_lock USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND event_type='reference.contacts_terminal_failed')""")
    op.execute("""CREATE FUNCTION public.reference_contacts_terminal_failure(
      p_business uuid,p_lookup uuid,p_effect uuid,p_token uuid,p_status text) RETURNS void
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;
        e public.reference_provider_effects%ROWTYPE; event uuid;
      BEGIN
        IF p_status IS NULL OR p_status NOT IN ('FAILED','TIMED-OUT','ABORTED') THEN
          RAISE EXCEPTION 'REFERENCE_CONTACTS_FAILURE_INVALID'; END IF;
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND id=p_effect AND actor_id=a AND provider='apify' FOR UPDATE;
        IF e.id IS NULL OR e.executor_token IS DISTINCT FROM p_token
          OR e.state NOT IN ('running','uncertain','failed_definitive') OR NOT EXISTS(
            SELECT 1 FROM public.reference_contacts_runs r WHERE r.tenant_id=t AND r.business_id=p_business
              AND r.effect_id=e.id AND r.actor_id=a) OR NOT EXISTS(
            SELECT 1 FROM public.reference_contacts_effect_links x WHERE x.tenant_id=t AND x.business_id=p_business
              AND x.lookup_id=p_lookup AND x.effect_id=e.id) OR NOT EXISTS(
            SELECT 1 FROM public.reference_cost_reservations r WHERE r.tenant_id=t AND r.business_id=p_business
              AND r.actor_id=a AND r.effect_id=e.id AND r.provider='apify' AND r.provider_search_id=e.search_id
              AND r.request_hash=e.request_mac AND r.reserved_usd_micros=e.reserved_usd_micros
              AND r.state IN ('claimed','uncertain','completed')) THEN
          RAISE EXCEPTION 'REFERENCE_CONTACTS_FAILURE_INVALID'; END IF;
        IF EXISTS(SELECT 1 FROM public.reference_contacts_failure_proofs WHERE tenant_id=t AND business_id=p_business
          AND effect_id=e.id AND reason='terminal_failed') THEN RETURN; END IF;
        UPDATE public.reference_cost_reservations SET state='uncertain',updated_at=clock_timestamp()
          WHERE tenant_id=t AND business_id=p_business AND actor_id=a AND effect_id=e.id AND state='claimed';
        UPDATE public.reference_provider_effects SET state='failed_definitive',updated_at=clock_timestamp()
          WHERE tenant_id=t AND business_id=p_business AND id=e.id;
        event:=gen_random_uuid();
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload) VALUES(event,t,
          'reference.contacts_terminal_failed',
          jsonb_build_object('business_id',p_business::text,'actor_id',a::text,'operation_id',e.id::text));
        INSERT INTO public.reference_contacts_failure_proofs(tenant_id,business_id,lookup_id,effect_id,actor_id,
          event_id,reason)
          VALUES(t,p_business,p_lookup,e.id,a,event,'terminal_failed');
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,e.id,'reference.contacts_terminal_failed',p_lookup);
      END $$""")
    _function("reference_contacts_terminal_failure(uuid,uuid,uuid,uuid,text)")
    for signature in (
        "reference_contacts_claim(uuid,uuid,uuid,uuid,text,uuid,bigint,text,text,text,text)",
        "reference_authorize_shared_contacts_retry(uuid,uuid,uuid,uuid,uuid)",
    ):
        op.execute(f"""DO $$ DECLARE body text; BEGIN
          SELECT pg_get_functiondef('public.{signature}'::regprocedure) INTO body;
          body:=replace(body,'proof.reason=''not_dispatched''',
          'proof.reason IN (''not_dispatched'',''terminal_failed'')');
          body:=replace(body,'r.state=''uncertain''','r.state IN (''uncertain'',''completed'')');
          body:=replace(body,'o.event_type=''reference.contacts_not_dispatched''',
            'o.event_type=CASE proof.reason WHEN ''terminal_failed'' THEN ' ||
            '''reference.contacts_terminal_failed'' ELSE ''reference.contacts_not_dispatched'' END');
          EXECUTE body;
        END $$""")
    op.execute("""CREATE TABLE reference_execution_retry_operations(
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,operation_id uuid NOT NULL,actor_id uuid NOT NULL,
      search_id uuid NOT NULL,event_id uuid NOT NULL,
      PRIMARY KEY(tenant_id,business_id,operation_id),
      FOREIGN KEY(tenant_id,business_id,search_id) REFERENCES reference_provider_searches(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id))""")
    op.execute("ALTER TABLE reference_execution_retry_operations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reference_execution_retry_operations FORCE ROW LEVEL SECURITY")
    op.execute("""CREATE POLICY reference_retry_request_private ON reference_execution_retry_operations
      TO meu_braco_direito_reference_lock USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid)
      WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid)""")
    op.execute("GRANT SELECT,INSERT ON reference_execution_retry_operations TO meu_braco_direito_reference_lock")
    op.execute(
        "GRANT SELECT(actor_id,operation_id,execution_status,state) ON reference_provider_searches "
        "TO meu_braco_direito_reference_lock"
    )
    op.execute("""CREATE POLICY reference_retry_request_event ON outbox_events FOR INSERT
      TO meu_braco_direito_reference_lock
      WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND event_type='reference.provider_retry_requested')""")
    op.execute("""CREATE POLICY reference_retry_request_audit ON audit_events FOR INSERT
      TO meu_braco_direito_reference_lock
      WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid
        AND action='reference.provider_retry_requested')""")
    op.execute("""CREATE FUNCTION public.reference_request_execution_retry(
      p_business uuid,p_search uuid,p_operation uuid)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;
        source_actor uuid; source_operation uuid; status text; event uuid;
        prior public.reference_execution_retry_operations%ROWTYPE;
      BEGIN
        IF p_operation IS NULL THEN RAISE EXCEPTION 'REFERENCE_RETRY_REQUEST_INVALID'; END IF;
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        SELECT actor_id,operation_id,execution_status INTO source_actor,source_operation,status
          FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business AND id=p_search;
        IF source_actor IS NULL THEN RAISE EXCEPTION 'REFERENCE_RETRY_REQUEST_INVALID'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-retry:'||t::text||':'||p_search::text,106));
        SELECT * INTO prior FROM public.reference_execution_retry_operations WHERE tenant_id=t
          AND business_id=p_business AND operation_id=p_operation;
        IF prior.operation_id IS NOT NULL THEN
          IF prior.actor_id<>a OR prior.search_id<>p_search THEN RAISE EXCEPTION
          'REFERENCE_RETRY_REQUEST_CONFLICT'; END IF;
          RETURN jsonb_build_object('search_id',p_search,'state','pending');
        END IF;
        IF status NOT IN ('contacts_failed','contacts_pending') THEN RAISE EXCEPTION
          'REFERENCE_RETRY_NOT_AVAILABLE'; END IF;
        event:=gen_random_uuid();
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(event,t,'reference.provider_retry_requested',jsonb_build_object('business_id',p_business::text,
            'actor_id',source_actor::text,'operation_id',source_operation::text));
        INSERT INTO public.reference_execution_retry_operations VALUES(t,p_business,p_operation,a,p_search,event);
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_operation,'reference.provider_retry_requested',p_search);
        RETURN jsonb_build_object('search_id',p_search,'state','pending');
      END $$""")
    op.execute(
        "ALTER FUNCTION public.reference_request_execution_retry(uuid,uuid,uuid) "
        "OWNER TO meu_braco_direito_reference_lock"
    )
    op.execute("REVOKE ALL ON FUNCTION public.reference_request_execution_retry(uuid,uuid,uuid) FROM PUBLIC")
    op.execute(
        "GRANT EXECUTE ON FUNCTION public.reference_request_execution_retry(uuid,uuid,uuid) TO meu_braco_direito_app"
    )


def _undo_terminal_retries():
    for signature in (
        "reference_contacts_claim(uuid,uuid,uuid,uuid,text,uuid,bigint,text,text,text,text)",
        "reference_authorize_shared_contacts_retry(uuid,uuid,uuid,uuid,uuid)",
    ):
        op.execute(f"""DO $$ DECLARE body text; BEGIN
          SELECT pg_get_functiondef('public.{signature}'::regprocedure) INTO body;
          body:=replace(body,'proof.reason IN (''not_dispatched'',''terminal_failed'')',
          'proof.reason=''not_dispatched''');
          body:=replace(body,'r.state IN (''uncertain'',''completed'')','r.state=''uncertain''');
          body:=replace(body,
          'o.event_type=CASE proof.reason WHEN ''terminal_failed'' THEN ' ||
            '''reference.contacts_terminal_failed'' ELSE ''reference.contacts_not_dispatched'' END',
            'o.event_type=''reference.contacts_not_dispatched''');
          EXECUTE body;
        END $$""")
    op.execute("DROP FUNCTION public.reference_request_execution_retry(uuid,uuid,uuid)")
    op.execute("DROP FUNCTION public.reference_contacts_terminal_failure(uuid,uuid,uuid,uuid,text)")
    op.execute("DROP TABLE reference_execution_retry_operations")
    for policy in (
        "reference_terminal_failure_event",
        "reference_terminal_failure_proof_read",
        "reference_retry_request_event",
    ):
        op.execute(f"DROP POLICY {policy} ON outbox_events")
    op.execute("DROP POLICY reference_retry_request_audit ON audit_events")
    op.execute(
        "REVOKE SELECT(actor_id,operation_id,execution_status,state) ON reference_provider_searches "
        "FROM meu_braco_direito_reference_lock"
    )
    op.execute(
        "ALTER TABLE reference_contacts_failure_proofs DROP CONSTRAINT reference_contacts_failure_proofs_reason_check"
    )
    op.execute(
        "ALTER TABLE reference_contacts_failure_proofs ADD CONSTRAINT "
        "reference_contacts_failure_proofs_reason_check CHECK(reason='not_dispatched')"
    )


def _release_unmapped_search():
    op.execute("""CREATE FUNCTION public.reference_release_unmapped_search(
      p_business uuid,p_search uuid,p_event uuid,p_operation uuid) RETURNS void
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;
        s public.reference_provider_searches%ROWTYPE; ev uuid;
      BEGIN
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_search FOR UPDATE;
        IF s.id IS NULL OR s.request_event_id IS DISTINCT FROM p_event OR p_operation IS NULL THEN
          RAISE EXCEPTION 'REFERENCE_EXECUTION_INVALID'; END IF;
        IF s.state='cancelled' AND s.cancel_operation_id=p_operation THEN RETURN; END IF;
        IF s.state<>'pending' OR EXISTS(SELECT 1 FROM public.reference_provider_effects e WHERE e.tenant_id=t
          AND e.business_id=p_business AND e.search_id=p_search AND e.provider='google' AND e.state<>'pending')
          OR NOT EXISTS(SELECT 1 FROM public.reference_provider_effects e
            JOIN public.reference_provider_outputs o ON o.tenant_id=e.tenant_id AND o.business_id=e.business_id
              AND o.effect_id=e.id AND o.kind='mapping' AND o.output->>'state' IN ('uncertain','no_match')
            WHERE e.tenant_id=t AND e.business_id=p_business AND e.search_id=p_search
              AND e.actor_id=a AND e.purpose='mapping' AND e.state='completed_filtered') THEN
          RAISE EXCEPTION 'REFERENCE_MAPPING_RELEASE_INVALID'; END IF;
        ev:=gen_random_uuid();
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(ev,t,'reference.provider_search_cancelled',
          jsonb_build_object('business_id',p_business::text,'actor_id',a::text,'operation_id',p_operation::text));
        UPDATE public.reference_provider_searches SET state='cancelled',radius_occupied=false,
          cancel_operation_id=p_operation,cancel_event_id=ev,execution_status='type_mapping_unavailable'
          WHERE tenant_id=t AND business_id=p_business AND id=p_search;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_operation,'reference.mapping_unavailable',p_search);
      END $$""")
    _function("reference_release_unmapped_search(uuid,uuid,uuid,uuid)")
