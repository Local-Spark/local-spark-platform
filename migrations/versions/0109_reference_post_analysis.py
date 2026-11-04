"""Fenced Jev post analysis, retaining only own pattern codes and accounting."""

from alembic import op

revision = "0109_reference_post_analysis"
down_revision = "0108_reference_learning"
branch_labels = None
depends_on = None

_ROLE = "meu_braco_direito_reference_ledger"
_SIGNATURES = (
    "reference_post_caption_read(uuid,uuid,text)",
    "reference_post_sample_read(uuid,uuid,text)",
    "reference_post_caption_claimed(uuid,uuid,text)",
    "reference_feed_record_terminal_cost(uuid,uuid,uuid,bigint)",
    "reference_post_claim(uuid,uuid,uuid,bigint,uuid,uuid,uuid,text,text,uuid,text,text,text,text,text,bigint)",
    "reference_post_uncertain(uuid,uuid,uuid)",
    "reference_post_record(uuid,uuid,uuid,jsonb,text,text,bigint,bigint)",
    "reference_post_read(uuid,uuid,text)",
)


def upgrade():
    op.execute("""CREATE FUNCTION public.reference_post_choices_valid(p jsonb) RETURNS boolean
      LANGUAGE sql IMMUTABLE SET search_path=pg_catalog,public AS $$ SELECT CASE
      WHEN jsonb_typeof(p) IS DISTINCT FROM 'object' OR p='{}'::jsonb THEN false
      ELSE NOT EXISTS(SELECT 1 FROM jsonb_each(p) item WHERE jsonb_typeof(item.value)<>'string'
        OR NOT CASE item.key
          WHEN 'tone' THEN item.value #>> '{}' =
          ANY(ARRAY['friendly','professional','direct','playful','inspirational','uncertain'])
          WHEN 'theme' THEN item.value #>> '{}' =
          ANY(ARRAY['product','offer','education','process','customer','team','community','seasonal','uncertain'])
          WHEN 'format' THEN item.value #>> '{}' =
          ANY(ARRAY['photo','text_card','infographic','collage','illustration','uncertain'])
          WHEN 'palette' THEN item.value #>> '{}' =
          ANY(ARRAY['warm','cool','neutral','vibrant','monochrome','uncertain'])
          WHEN 'lighting' THEN item.value #>> '{}' = ANY(ARRAY['natural','soft','studio','contrast','uncertain'])
          WHEN 'composition' THEN item.value #>> '{}' =
          ANY(ARRAY['closeup','wide','centered','minimal','grid','uncertain'])
          WHEN 'text_density' THEN item.value #>> '{}' = ANY(ARRAY['none','sparse','dominant','uncertain'])
          WHEN 'subject' THEN item.value #>> '{}' =
          ANY(ARRAY['product','people','space','process','abstract','uncertain'])
          ELSE false END) END $$""")
    op.execute("""CREATE TABLE reference_post_effects(
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,id uuid NOT NULL,actor_id uuid NOT NULL,
      window_id uuid NOT NULL,parent_feed_effect_id uuid NOT NULL,pilot_id uuid NOT NULL,
      sample_mac char(64) NOT NULL CHECK(sample_mac ~ '^[0-9a-f]{64}$'),
      caption_mac char(64) CHECK(caption_mac ~ '^[0-9a-f]{64}$'),
      request_mac char(64) NOT NULL CHECK(request_mac ~ '^[0-9a-f]{64}$'),
      key_version text NOT NULL CHECK(key_version ~ '^[A-Za-z0-9_.-]{1,64}$'),
      tariff_version text NOT NULL,credential_version text NOT NULL CHECK(credential_version ~
          '^[A-Za-z0-9_.-]{1,64}$'),
      model text NOT NULL CHECK(model ~ '^[A-Za-z0-9_.-]{1,120}$'),
      reserved_usd_micros bigint NOT NULL CHECK(reserved_usd_micros BETWEEN 1 AND 5000000),
      state text NOT NULL CHECK(state IN ('running','uncertain','completed')),
      executor_token uuid NOT NULL,event_id uuid NOT NULL,
      choices jsonb CHECK(choices IS NULL OR public.reference_post_choices_valid(choices)),
      vocabulary_version text CHECK(vocabulary_version='reference-patterns-v1'),
      provider_model text CHECK(provider_model ~ '^[A-Za-z0-9_.-]{1,120}$'),
      input_tokens bigint CHECK(input_tokens>=0),output_tokens bigint CHECK(output_tokens>=0),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(tenant_id,business_id,id),UNIQUE(tenant_id,id),UNIQUE(tenant_id,business_id,window_id,sample_mac),
      UNIQUE(tenant_id,business_id,window_id,caption_mac),
      FOREIGN KEY(tenant_id,business_id,window_id) REFERENCES reference_feed_windows(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,parent_feed_effect_id) REFERENCES
          reference_feed_effects(tenant_id,business_id,id),
      FOREIGN KEY(pilot_id) REFERENCES reference_provider_pilots(id),
      FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id),
      CHECK((state='completed' AND choices IS NOT NULL AND vocabulary_version IS NOT NULL AND provider_model IS NOT NULL
        AND input_tokens IS NOT NULL AND output_tokens IS NOT NULL) OR
        (state<>'completed' AND choices IS NULL AND vocabulary_version IS NULL AND provider_model IS NULL
         AND input_tokens IS NULL AND output_tokens IS NULL)))""")
    op.execute("ALTER TABLE reference_post_effects ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reference_post_effects FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY reference_post_executor ON reference_post_effects TO {_ROLE}
      USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)
      WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)""")
    op.execute(f"""GRANT SELECT,INSERT,UPDATE(state,choices,vocabulary_version,provider_model,input_tokens,
          output_tokens)
      ON reference_post_effects TO {_ROLE}""")
    op.execute("""CREATE FUNCTION public.reference_post_claim(
      p_business uuid,p_window uuid,p_reference uuid,p_version bigint,p_parent uuid,p_parent_token uuid,
      p_effect uuid,p_sample text,p_caption text,p_pilot uuid,p_mac text,p_key text,p_tariff text,
      p_credential text,p_model text,p_amount bigint)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;
        old public.reference_post_effects%ROWTYPE;w public.reference_feed_windows%ROWTYPE;
        parent public.reference_feed_effects%ROWTYPE;pilot public.reference_provider_pilots%ROWTYPE;
        pol public.reference_cost_policies%ROWTYPE;pp public.reference_cost_policy_providers%ROWTYPE;
        tariff public.reference_provider_tariffs%ROWTYPE;used numeric;provider_used numeric;
        cm date;token uuid;ev uuid;
      BEGIN
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        IF (p_caption IS NOT NULL AND p_caption !~ '^[0-9a-f]{64}$')
          OR p_effect IS NULL OR p_sample IS NULL OR p_sample !~ '^[0-9a-f]{64}$'
          OR p_mac IS NULL OR p_mac !~ '^[0-9a-f]{64}$' OR p_key IS NULL OR p_key !~ '^[A-Za-z0-9_.-]{1,64}$'
          OR p_credential IS NULL OR p_credential !~ '^[A-Za-z0-9_.-]{1,64}$'
          OR p_model IS NULL OR p_model !~ '^[A-Za-z0-9_.-]{1,120}$'
          OR p_amount IS NULL OR p_amount NOT BETWEEN 1 AND 5000000 THEN
          RAISE EXCEPTION 'REFERENCE_POST_INTENT_INVALID'; END IF;
        IF NOT public.reference_feed_window_active(p_business,p_window) THEN
          RAISE EXCEPTION 'REFERENCE_FEED_REFERENCE_INVALID'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO w FROM public.reference_feed_windows WHERE tenant_id=t AND business_id=p_business
          AND id=p_window AND actor_id=a FOR SHARE;
        IF w.id IS NULL OR w.reference_id IS DISTINCT FROM p_reference OR w.association_version IS DISTINCT FROM
          p_version
          THEN RAISE EXCEPTION 'REFERENCE_FEED_REFERENCE_INVALID'; END IF;
        SELECT * INTO parent FROM public.reference_feed_effects WHERE tenant_id=t AND business_id=p_business
          AND id=p_parent AND actor_id=a FOR SHARE;
        IF parent.id IS NULL OR parent.window_id IS DISTINCT FROM p_window OR parent.pilot_id IS DISTINCT FROM p_pilot
          OR p_parent_token IS NULL OR parent.executor_token IS DISTINCT FROM p_parent_token
          OR parent.state NOT IN ('running','uncertain') OR NOT EXISTS(SELECT 1 FROM public.reference_feed_resources
            WHERE tenant_id=t AND business_id=p_business AND effect_id=p_parent AND actor_id=a) THEN
          RAISE EXCEPTION 'REFERENCE_POST_PARENT_INVALID'; END IF;
        SELECT * INTO old FROM public.reference_post_effects WHERE tenant_id=t AND business_id=p_business
          AND (id=p_effect OR (window_id=p_window AND sample_mac=p_sample)
            OR (window_id=p_window AND caption_mac=p_caption)) FOR UPDATE;
        IF FOUND THEN
          IF old.id IS DISTINCT FROM p_effect OR old.actor_id IS DISTINCT FROM a OR old.window_id IS DISTINCT FROM
          p_window
            OR old.parent_feed_effect_id IS DISTINCT FROM p_parent OR old.sample_mac IS DISTINCT FROM p_sample
            OR old.caption_mac IS DISTINCT FROM p_caption
            OR old.pilot_id IS DISTINCT FROM p_pilot OR old.request_mac IS DISTINCT FROM p_mac
            OR old.key_version IS DISTINCT FROM p_key OR old.tariff_version IS DISTINCT FROM p_tariff
            OR old.credential_version IS DISTINCT FROM p_credential OR old.model IS DISTINCT FROM p_model
            OR old.reserved_usd_micros IS DISTINCT FROM p_amount THEN RAISE EXCEPTION
          'REFERENCE_POST_INTENT_CONFLICT'; END IF;
          RETURN jsonb_build_object('created',false,'state',old.state);
        END IF;
        SELECT * INTO tariff FROM public.reference_provider_tariffs WHERE version=p_tariff FOR SHARE;
        IF tariff.version IS NULL OR NOT tariff.active OR tariff.provider<>'jev'
          OR tariff.field_mask IS DISTINCT FROM 'jev-model:'||p_model OR p_amount<tariff.minimum_reserved_usd_micros
          THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_TARIFF_INVALID'; END IF;
        SELECT * INTO pilot FROM public.reference_provider_pilots WHERE id=p_pilot FOR UPDATE;
        IF pilot.id IS NULL OR NOT pilot.active THEN RAISE EXCEPTION 'REFERENCE_PILOT_DISABLED'; END IF;
        IF pilot.reserved_usd_micros+p_amount>pilot.cap_usd_micros THEN RAISE EXCEPTION
          'REFERENCE_PILOT_BUDGET_EXCEEDED'; END IF;
        SELECT q.* INTO pol FROM public.reference_cost_policy_head h JOIN public.reference_cost_policies q
          ON q.id=h.policy_id WHERE h.singleton;
        IF pol.id IS NULL THEN RAISE EXCEPTION 'REFERENCE_BUDGET_DISABLED'; END IF;
        SELECT * INTO pp FROM public.reference_cost_policy_providers WHERE policy_id=pol.id AND provider='jev';
        IF pp.policy_id IS NULL THEN RAISE EXCEPTION 'REFERENCE_BUDGET_DISABLED'; END IF;
        SELECT coalesce(sum(CASE WHEN state='completed' THEN actual_usd_micros ELSE reserved_usd_micros END),0),
          coalesce(sum(CASE WHEN state='completed' THEN actual_usd_micros ELSE reserved_usd_micros END)
          FILTER(WHERE provider='jev'),0) INTO used,provider_used
          FROM public.reference_cost_reservations WHERE tenant_id=t AND business_id=p_business AND
          feed_window_id=p_window;
        IF used+p_amount>pol.per_search OR provider_used+p_amount>pp.per_search
          THEN RAISE EXCEPTION 'REFERENCE_SEARCH_BUDGET_EXCEEDED'; END IF;
        cm:=date_trunc('month',clock_timestamp() AT TIME ZONE pol.timezone)::date;
        SELECT coalesce(sum(CASE WHEN month=cm THEN committed_usd_micros ELSE outstanding_usd_micros END),0)
          INTO used FROM public.reference_cost_monthly WHERE provider='all';
        IF used+p_amount>pol.monthly_total THEN RAISE EXCEPTION 'REFERENCE_MONTHLY_BUDGET_EXCEEDED'; END IF;
        SELECT coalesce(sum(CASE WHEN month=cm THEN committed_usd_micros ELSE outstanding_usd_micros END),0)
          INTO used FROM public.reference_cost_monthly WHERE provider='jev';
        IF used+p_amount>pp.monthly_total THEN RAISE EXCEPTION 'REFERENCE_MONTHLY_PROVIDER_BUDGET_EXCEEDED'; END IF;
        UPDATE public.reference_provider_pilots SET reserved_usd_micros=reserved_usd_micros+p_amount WHERE id=p_pilot;
        INSERT INTO public.reference_cost_monthly(month,provider,committed_usd_micros,outstanding_usd_micros)
          VALUES(cm,'all',p_amount,p_amount),(cm,'jev',p_amount,p_amount) ON CONFLICT(month,provider) DO UPDATE SET
          committed_usd_micros=reference_cost_monthly.committed_usd_micros+excluded.committed_usd_micros,
          outstanding_usd_micros=reference_cost_monthly.outstanding_usd_micros+excluded.outstanding_usd_micros;
        token:=gen_random_uuid();ev:=gen_random_uuid();
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload) VALUES(ev,t,'reference.provider_cost_changed',
          jsonb_build_object('business_id',p_business::text,'actor_id',a::text,'operation_id',p_effect::text));
        INSERT INTO public.reference_post_effects(tenant_id,business_id,id,actor_id,window_id,parent_feed_effect_id,
          pilot_id,sample_mac,caption_mac,request_mac,key_version,tariff_version,credential_version,model,reserved_usd_micros,
          state,executor_token,event_id) VALUES(t,p_business,p_effect,a,p_window,p_parent,p_pilot,p_sample,
          p_caption,p_mac,p_key,
          p_tariff,p_credential,p_model,p_amount,'running',token,ev);
        INSERT INTO public.reference_cost_reservations(id,tenant_id,business_id,actor_id,discovery_id,
          provider_search_id,
          feed_window_id,pilot_id,effect_id,request_hash,provider,month,reserved_usd_micros,state,policy_id)
          VALUES(gen_random_uuid(),t,p_business,a,NULL,NULL,p_window,p_pilot,p_effect,p_mac,'jev',cm,p_amount,
          'claimed',pol.id);
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_effect,'reference.post_cost_claimed',p_window);
        RETURN jsonb_build_object('created',true,'state','running','executor_token',token);
      END $$""")
    op.execute("""CREATE FUNCTION public.reference_post_uncertain(p_business uuid,p_effect uuid,p_token uuid)
      RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;e public.reference_post_effects%ROWTYPE;
      BEGIN
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO e FROM public.reference_post_effects WHERE tenant_id=t AND business_id=p_business AND actor_id=a
          AND id=p_effect FOR UPDATE;
        IF e.id IS NULL OR p_token IS NULL OR e.executor_token IS DISTINCT FROM p_token
          THEN RAISE EXCEPTION 'REFERENCE_POST_FENCE_INVALID'; END IF;
        IF e.state<>'running' THEN RETURN; END IF;
        UPDATE public.reference_post_effects SET state='uncertain' WHERE tenant_id=t AND business_id=p_business
          AND id=p_effect;
        UPDATE public.reference_cost_reservations SET state='uncertain',updated_at=clock_timestamp()
          WHERE tenant_id=t AND business_id=p_business AND actor_id=a AND feed_window_id=e.window_id
          AND effect_id=p_effect AND state='claimed';
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_RESERVATION_NOT_FOUND'; END IF;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_effect,'reference.post_cost_uncertain',e.window_id);
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload) VALUES(gen_random_uuid(),t,
          'reference.provider_cost_changed',jsonb_build_object('business_id',p_business::text,'actor_id',a::text,
          'operation_id',p_effect::text));
      END $$""")
    op.execute("""CREATE FUNCTION public.reference_post_record(p_business uuid,p_effect uuid,p_token
          uuid,p_choices jsonb,
      p_vocabulary text,p_model text,p_incoming bigint,p_outgoing bigint) RETURNS void
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;e public.reference_post_effects%ROWTYPE;
      BEGIN
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        SELECT * INTO e FROM public.reference_post_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_effect;
        IF e.id IS NULL OR p_token IS NULL OR e.executor_token IS DISTINCT FROM p_token
          THEN RAISE EXCEPTION 'REFERENCE_POST_FENCE_INVALID'; END IF;
        IF NOT public.reference_feed_window_active(p_business,e.window_id)
          THEN RAISE EXCEPTION 'REFERENCE_FEED_REFERENCE_INVALID'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO e FROM public.reference_post_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_effect FOR UPDATE;
        IF e.state='completed' THEN
          IF (e.choices,e.vocabulary_version,e.provider_model,e.input_tokens,e.output_tokens)
            IS DISTINCT FROM (p_choices,p_vocabulary,p_model,p_incoming,p_outgoing)
            THEN RAISE EXCEPTION 'REFERENCE_POST_RESULT_CONFLICT'; END IF;
          RETURN;
        END IF;
        IF NOT public.reference_post_choices_valid(p_choices) OR p_vocabulary IS DISTINCT FROM 'reference-patterns-v1'
          OR p_model IS NULL OR p_model !~ '^[A-Za-z0-9_.-]{1,120}$'
          OR p_incoming IS NULL OR p_incoming<0 OR p_outgoing IS NULL OR p_outgoing<0
          THEN RAISE EXCEPTION 'REFERENCE_POST_RESULT_INVALID'; END IF;
        PERFORM 1 FROM public.reference_cost_reservations WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND effect_id=p_effect AND feed_window_id=e.window_id AND provider='jev'
          AND request_hash=e.request_mac AND reserved_usd_micros=e.reserved_usd_micros AND state IN
          ('claimed','uncertain');
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_RESERVATION_NOT_FOUND'; END IF;
        UPDATE public.reference_post_effects SET state='completed',choices=p_choices,vocabulary_version=p_vocabulary,
          provider_model=p_model,input_tokens=p_incoming,output_tokens=p_outgoing
          WHERE tenant_id=t AND business_id=p_business AND id=p_effect;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_effect,'reference.post_patterns_recorded',e.window_id);
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload) VALUES(gen_random_uuid(),t,
          'reference.provider_cost_changed',jsonb_build_object('business_id',p_business::text,'actor_id',a::text,
          'operation_id',p_effect::text));
      END $$""")
    op.execute("""CREATE FUNCTION public.reference_post_read(p_business uuid,p_window uuid,p_sample text) RETURNS jsonb
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;result jsonb;
      BEGIN
        IF NOT public.reference_feed_window_active(p_business,p_window)
          THEN RAISE EXCEPTION 'REFERENCE_FEED_REFERENCE_INVALID'; END IF;
        SELECT jsonb_build_object('choices',choices,'vocabulary_version',vocabulary_version,'provider_model',
          provider_model,
          'input_tokens',input_tokens,'output_tokens',output_tokens) INTO result FROM public.reference_post_effects
          WHERE tenant_id=t AND business_id=p_business AND actor_id=a AND window_id=p_window AND sample_mac=p_sample
          AND state='completed';
        RETURN result;
      END $$""")
    _sample_metadata()
    _feed_cost()
    for signature in _SIGNATURES:
        op.execute(f"ALTER FUNCTION public.{signature} OWNER TO {_ROLE}")
        op.execute(f"REVOKE ALL ON FUNCTION public.{signature} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION public.{signature} TO meu_braco_direito_correlator")
    op.execute("REVOKE ALL ON FUNCTION public.reference_post_choices_valid(jsonb) FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION public.reference_post_choices_valid(jsonb) TO {_ROLE}")


def _feed_cost():
    op.execute("""ALTER TABLE reference_feed_resources ADD COLUMN reported_cost_usd_micros bigint
      CHECK(reported_cost_usd_micros>=0)""")
    op.execute(f"GRANT UPDATE(reported_cost_usd_micros) ON reference_feed_resources TO {_ROLE}")
    op.execute("""CREATE FUNCTION public.reference_feed_record_terminal_cost(
      p_business uuid,p_effect uuid,p_token uuid,p_actual bigint) RETURNS void
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;
        e public.reference_feed_effects%ROWTYPE;r public.reference_cost_reservations%ROWTYPE;
        old_cost bigint;changed integer;
      BEGIN
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO e FROM public.reference_feed_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_effect FOR UPDATE;
        IF e.id IS NULL OR p_token IS NULL OR e.executor_token IS DISTINCT FROM p_token
          OR e.state NOT IN ('running','uncertain','completed') THEN
          RAISE EXCEPTION 'REFERENCE_FEED_FENCE_INVALID'; END IF;
        SELECT reported_cost_usd_micros INTO old_cost FROM public.reference_feed_resources
          WHERE tenant_id=t AND business_id=p_business AND effect_id=p_effect AND actor_id=a FOR UPDATE;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_FEED_RESOURCE_INVALID'; END IF;
        SELECT * INTO r FROM public.reference_cost_reservations WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND effect_id=p_effect AND feed_window_id=e.window_id AND provider='apify' FOR UPDATE;
        IF r.id IS NULL THEN RAISE EXCEPTION 'REFERENCE_RESERVATION_NOT_FOUND'; END IF;
        IF p_actual IS NULL THEN
          IF r.state IN ('completed','uncertain') THEN RETURN; END IF;
          UPDATE public.reference_cost_reservations SET state='uncertain',updated_at=clock_timestamp()
            WHERE tenant_id=t AND business_id=p_business AND id=r.id;
        ELSE
          IF p_actual<0 OR p_actual>r.reserved_usd_micros THEN
            RAISE EXCEPTION 'REFERENCE_FEED_RECEIPT_INVALID'; END IF;
          IF old_cost IS NOT NULL THEN
            IF old_cost IS DISTINCT FROM p_actual OR r.state<>'completed' OR r.actual_usd_micros<>p_actual THEN
              RAISE EXCEPTION 'REFERENCE_FEED_RECEIPT_CONFLICT'; END IF;
            RETURN;
          END IF;
          IF r.state NOT IN ('claimed','uncertain') THEN RAISE EXCEPTION 'REFERENCE_FEED_RECEIPT_CONFLICT'; END IF;
          UPDATE public.reference_provider_pilots
            SET reserved_usd_micros=reserved_usd_micros-r.reserved_usd_micros+p_actual
            WHERE id=r.pilot_id AND reserved_usd_micros>=r.reserved_usd_micros;
          IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_MONTHLY_INCONSISTENT'; END IF;
          UPDATE public.reference_cost_monthly
            SET committed_usd_micros=committed_usd_micros-r.reserved_usd_micros+p_actual,
                outstanding_usd_micros=outstanding_usd_micros-r.reserved_usd_micros
            WHERE month=r.month AND provider IN ('all','apify')
              AND committed_usd_micros>=r.reserved_usd_micros AND outstanding_usd_micros>=r.reserved_usd_micros;
          GET DIAGNOSTICS changed=ROW_COUNT;
          IF changed<>2 THEN RAISE EXCEPTION 'REFERENCE_MONTHLY_INCONSISTENT'; END IF;
          UPDATE public.reference_cost_reservations SET state='completed',actual_usd_micros=p_actual,
            updated_at=clock_timestamp() WHERE tenant_id=t AND business_id=p_business AND id=r.id;
          UPDATE public.reference_feed_resources SET reported_cost_usd_micros=p_actual
            WHERE tenant_id=t AND business_id=p_business AND effect_id=p_effect;
        END IF;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_effect,CASE WHEN p_actual IS NULL THEN 'reference.feed_cost_uncertain'
            ELSE 'reference.feed_cost_reported' END,r.id);
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(gen_random_uuid(),t,'reference.provider_cost_changed',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_effect::text));
      END $$""")


def downgrade():
    op.execute("LOCK TABLE reference_post_effects,reference_feed_resources IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security=off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_post_effects) OR
      EXISTS(SELECT 1 FROM reference_feed_resources WHERE reported_cost_usd_micros IS NOT NULL) THEN
      RAISE EXCEPTION 'REFERENCE_POST_ANALYSIS_REQUIRES_FORWARD_RECOVERY'; END IF; END $$""")
    op.execute("SET LOCAL row_security=on")
    for signature in reversed(_SIGNATURES):
        op.execute(f"DROP FUNCTION public.{signature}")
    op.execute("ALTER TABLE reference_feed_resources DROP COLUMN reported_cost_usd_micros")
    op.execute("DROP TABLE reference_post_effects")
    op.execute("DROP FUNCTION public.reference_post_choices_valid(jsonb)")


def _sample_metadata():
    op.execute("""CREATE FUNCTION public.reference_post_sample_read(p_business uuid,p_window uuid,p_sample text)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;result jsonb;
      BEGIN
        IF NOT public.reference_feed_window_active(p_business,p_window)
          THEN RAISE EXCEPTION 'REFERENCE_FEED_REFERENCE_INVALID'; END IF;
        SELECT jsonb_build_object('state',state,'includes_caption',caption_mac IS NOT NULL,'result',
          CASE WHEN state='completed' THEN jsonb_build_object('choices',choices,'vocabulary_version',vocabulary_version,
            'provider_model',provider_model,'input_tokens',input_tokens,'output_tokens',output_tokens) ELSE NULL END)
          INTO result FROM public.reference_post_effects WHERE tenant_id=t AND business_id=p_business AND actor_id=a
          AND window_id=p_window AND sample_mac=p_sample;
        RETURN result;
      END $$""")
    op.execute("""CREATE FUNCTION public.reference_post_caption_claimed(p_business uuid,p_window uuid,p_caption text)
      RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      BEGIN
        IF NOT public.reference_feed_window_active(p_business,p_window)
          THEN RAISE EXCEPTION 'REFERENCE_FEED_REFERENCE_INVALID'; END IF;
        RETURN EXISTS(SELECT 1 FROM public.reference_post_effects
          WHERE tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
            AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid
            AND business_id=p_business AND window_id=p_window AND caption_mac=p_caption);
      END $$""")
    op.execute("""CREATE FUNCTION public.reference_post_caption_read(p_business uuid,p_window uuid,p_caption text)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE sample text;
      BEGIN
        IF NOT public.reference_feed_window_active(p_business,p_window)
          THEN RAISE EXCEPTION 'REFERENCE_FEED_REFERENCE_INVALID'; END IF;
        SELECT sample_mac INTO sample FROM public.reference_post_effects
          WHERE tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
            AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid
            AND business_id=p_business AND window_id=p_window AND caption_mac=p_caption;
        IF sample IS NULL THEN RETURN NULL; END IF;
        RETURN public.reference_post_sample_read(p_business,p_window,sample);
      END $$""")
