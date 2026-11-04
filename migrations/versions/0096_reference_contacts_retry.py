"""Inactive contacts retries after fenced, durably recorded non-dispatch.

No runtime function grant or intent creator is introduced. A trusted future
activity must prove non-dispatch; remote failures and ambiguous sends remain
blocked. Every attempt holds its own reservation and prior holds remain intact.
"""

from alembic import op

revision = "0096_reference_contacts_retry"
down_revision = "0095_reference_contacts_guard"
branch_labels = None
depends_on = None

_CLAIM = "uuid,uuid,uuid,uuid,text,uuid,bigint,text,text,text,text"


def upgrade():
    op.execute("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))")
    op.execute("LOCK TABLE reference_provider_effects,reference_contacts_effect_links IN ACCESS EXCLUSIVE MODE")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_state_check")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_check")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_effects_state_check
      CHECK(state IN ('pending','running','uncertain','completed_empty','completed_filtered','failed_definitive')),
      ADD CONSTRAINT reference_provider_effects_check CHECK(
        (state='pending' AND executor_token IS NULL) OR
        (state IN ('running','uncertain','completed_empty','completed_filtered','failed_definitive')
          AND executor_token IS NOT NULL)),
      ADD CONSTRAINT reference_definitive_failure_contacts_only
        CHECK(state<>'failed_definitive' OR provider='apify')""")
    op.execute("""DO $$ DECLARE constraint_name text; BEGIN
      SELECT conname INTO constraint_name FROM pg_constraint
        WHERE conrelid='public.reference_contacts_effect_links'::regclass AND contype='u'
          AND pg_get_constraintdef(oid)='UNIQUE (tenant_id, business_id, lookup_id)';
      IF constraint_name IS NULL THEN RAISE EXCEPTION 'REFERENCE_CONTACTS_CONSTRAINT_MISSING'; END IF;
      EXECUTE format('ALTER TABLE public.reference_contacts_effect_links DROP CONSTRAINT %I',constraint_name);
    END $$""")
    op.execute("""ALTER TABLE reference_contacts_effect_links ADD COLUMN attempt_no integer NOT NULL DEFAULT 1,
      ADD COLUMN previous_effect_id uuid,
      ADD CONSTRAINT reference_contacts_attempt_positive CHECK(attempt_no>0),
      ADD CONSTRAINT reference_contacts_attempt_chain CHECK(
        (attempt_no=1 AND previous_effect_id IS NULL) OR (attempt_no>1 AND previous_effect_id IS NOT NULL)),
      ADD UNIQUE(tenant_id,business_id,lookup_id,attempt_no),
      ADD UNIQUE(tenant_id,business_id,lookup_id,effect_id),
      ADD FOREIGN KEY(tenant_id,business_id,lookup_id,previous_effect_id)
        REFERENCES reference_contacts_effect_links(tenant_id,business_id,lookup_id,effect_id)""")
    op.execute("""CREATE TABLE reference_contacts_failure_proofs (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,lookup_id uuid NOT NULL,effect_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),event_id uuid NOT NULL,
      reason text NOT NULL CHECK(reason='not_dispatched'),created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(tenant_id,business_id,effect_id),
      FOREIGN KEY(tenant_id,business_id,lookup_id,effect_id)
        REFERENCES reference_contacts_effect_links(tenant_id,business_id,lookup_id,effect_id),
      FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    op.execute("ALTER TABLE reference_contacts_failure_proofs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reference_contacts_failure_proofs FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY reference_contacts_proof_ledger ON reference_contacts_failure_proofs
      TO meu_braco_direito_reference_ledger USING(tenant_id={tenant} AND actor_id={actor})
      WITH CHECK(tenant_id={tenant} AND actor_id={actor})""")
    op.execute("GRANT SELECT,INSERT ON reference_contacts_failure_proofs TO meu_braco_direito_reference_ledger")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed',
       'reference.provider_effect_requested','reference.provider_cost_changed','reference.provider_effect_completed',
       'reference.provider_search_requested','reference.provider_search_cancelled','reference.real_selection_confirmed',
       'reference.private_shortlist_prepared','reference.feed_resources_recorded','reference.contacts_not_dispatched'))""")
    op.execute(f"""CREATE POLICY reference_contacts_failure_event_emit ON outbox_events FOR INSERT
      TO meu_braco_direito_reference_ledger WITH CHECK(tenant_id={tenant}
        AND event_type='reference.contacts_not_dispatched' AND payload->>'actor_id'={actor}::text)""")
    op.execute(f"""CREATE POLICY reference_contacts_failure_event_read ON outbox_events FOR SELECT
      TO meu_braco_direito_reference_ledger USING(tenant_id={tenant}
        AND event_type='reference.contacts_not_dispatched' AND payload->>'actor_id'={actor}::text)""")
    op.execute("""CREATE FUNCTION public.reference_contacts_not_dispatched(
      p_business uuid,p_lookup uuid,p_effect uuid,p_executor uuid) RETURNS uuid
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        e public.reference_provider_effects%ROWTYPE; proof public.reference_contacts_failure_proofs%ROWTYPE;
        event_id uuid;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_lookup IS NULL OR p_effect IS NULL OR p_executor IS NULL
          THEN RAISE EXCEPTION 'REFERENCE_CONTACTS_FAILURE_INVALID'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        PERFORM 1 FROM public.reference_contacts_lookups WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_lookup FOR UPDATE;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_CONTACTS_FAILURE_INVALID'; END IF;
        SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_effect AND provider='apify' FOR UPDATE;
        IF NOT FOUND OR e.executor_token IS DISTINCT FROM p_executor OR NOT EXISTS(
          SELECT 1 FROM public.reference_contacts_effect_links x WHERE x.tenant_id=t AND x.business_id=p_business
            AND x.lookup_id=p_lookup AND x.effect_id=p_effect) THEN
          RAISE EXCEPTION 'REFERENCE_CONTACTS_FAILURE_INVALID'; END IF;
        SELECT * INTO proof FROM public.reference_contacts_failure_proofs WHERE tenant_id=t AND business_id=p_business
          AND lookup_id=p_lookup AND effect_id=p_effect AND actor_id=a;
        IF FOUND THEN
          IF e.state<>'failed_definitive' OR proof.reason<>'not_dispatched' OR NOT EXISTS(
            SELECT 1 FROM public.outbox_events o WHERE o.tenant_id=t AND o.id=proof.event_id
              AND o.event_type='reference.contacts_not_dispatched' AND o.payload=jsonb_build_object(
                'business_id',p_business::text,'actor_id',a::text,'operation_id',p_effect::text)) OR NOT EXISTS(
            SELECT 1 FROM public.reference_cost_reservations r WHERE r.tenant_id=t AND r.business_id=p_business
              AND r.actor_id=a AND r.effect_id=e.id AND r.provider_search_id=e.search_id AND r.provider='apify'
              AND r.pilot_id=e.pilot_id AND r.request_hash=e.request_mac
              AND r.reserved_usd_micros=e.reserved_usd_micros AND r.state='uncertain') THEN
            RAISE EXCEPTION 'REFERENCE_CONTACTS_FAILURE_INVALID'; END IF;
          RETURN proof.event_id;
        END IF;
        IF e.state<>'running' OR e.request_event_id IS NULL OR NOT EXISTS(
          SELECT 1 FROM public.outbox_events o WHERE o.tenant_id=t AND o.id=e.request_event_id
            AND o.event_type='reference.provider_effect_requested' AND o.payload=jsonb_build_object(
              'business_id',p_business::text,'actor_id',a::text,'operation_id',e.id::text)) THEN
          RAISE EXCEPTION 'REFERENCE_CONTACTS_FAILURE_INVALID'; END IF;
        UPDATE public.reference_cost_reservations SET state='uncertain',updated_at=clock_timestamp()
          WHERE tenant_id=t AND business_id=p_business AND actor_id=a AND provider='apify'
            AND provider_search_id=e.search_id AND effect_id=e.id AND pilot_id=e.pilot_id
            AND request_hash=e.request_mac AND state='claimed';
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_RESERVATION_NOT_FOUND'; END IF;
        UPDATE public.reference_provider_effects SET state='failed_definitive',updated_at=clock_timestamp()
          WHERE tenant_id=t AND business_id=p_business AND id=e.id;
        event_id := gen_random_uuid();
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(event_id,t,'reference.contacts_not_dispatched',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_effect::text));
        INSERT INTO public.reference_contacts_failure_proofs
          (tenant_id,business_id,lookup_id,effect_id,actor_id,event_id,reason)
          VALUES(t,p_business,p_lookup,p_effect,a,event_id,'not_dispatched');
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_effect,'reference.contacts_not_dispatched',p_lookup);
        RETURN event_id;
      END $$""")
    op.execute("""ALTER FUNCTION public.reference_contacts_not_dispatched(uuid,uuid,uuid,uuid)
      OWNER TO meu_braco_direito_reference_ledger""")
    op.execute("""REVOKE ALL ON FUNCTION public.reference_contacts_not_dispatched(uuid,uuid,uuid,uuid)
      FROM PUBLIC,meu_braco_direito_correlator""")
    op.execute(
        f"ALTER FUNCTION public.reference_contacts_claim({_CLAIM}) RENAME TO reference_contacts_claim_retry_inner"
    )
    op.execute(
        f"REVOKE ALL ON FUNCTION public.reference_contacts_claim_retry_inner({_CLAIM}) "
        "FROM PUBLIC,meu_braco_direito_correlator"
    )
    op.execute("""CREATE FUNCTION public.reference_contacts_claim(
      p_business uuid,p_lookup uuid,p_effect uuid,p_event uuid,p_mac text,p_pilot uuid,p_amount bigint,
      p_key text,p_tariff text,p_credential text,p_class text)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        e public.reference_provider_effects%ROWTYPE; attempt public.reference_contacts_effect_links%ROWTYPE;
        expected_context bigint; current_context bigint; prior_count integer;
      BEGIN
        SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_effect AND provider='apify';
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_CONTACTS_INTENT_INVALID'; END IF;
        IF e.state='pending' THEN
          IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
          SELECT context_version INTO expected_context FROM public.reference_provider_searches
            WHERE tenant_id=t AND business_id=p_business AND actor_id=a AND id=e.search_id;
          SELECT version INTO current_context FROM public.business_context_heads
            WHERE tenant_id=t AND business_id=p_business FOR SHARE;
          PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
          PERFORM 1 FROM public.reference_contacts_lookups WHERE tenant_id=t AND business_id=p_business
            AND actor_id=a AND id=p_lookup FOR UPDATE;
          IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_CONTACTS_INTENT_INVALID'; END IF;
          SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
            AND actor_id=a AND id=p_effect AND provider='apify' FOR UPDATE;
          IF e.state='pending' THEN
            IF current_context IS DISTINCT FROM expected_context THEN RAISE EXCEPTION 'REFERENCE_CONTEXT_STALE'; END IF;
            SELECT * INTO attempt FROM public.reference_contacts_effect_links
              WHERE tenant_id=t AND business_id=p_business
              AND lookup_id=p_lookup AND effect_id=p_effect;
            IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_CONTACTS_INTENT_INVALID'; END IF;
            SELECT count(*) INTO prior_count FROM public.reference_contacts_effect_links x
              JOIN public.reference_provider_effects prior ON prior.tenant_id=x.tenant_id
                AND prior.business_id=x.business_id AND prior.id=x.effect_id AND prior.actor_id=a
              JOIN public.reference_contacts_failure_proofs proof ON proof.tenant_id=x.tenant_id
                AND proof.business_id=x.business_id AND proof.lookup_id=x.lookup_id AND proof.effect_id=x.effect_id
                AND proof.actor_id=a AND proof.reason='not_dispatched'
              JOIN public.reference_cost_reservations r ON r.tenant_id=x.tenant_id AND r.business_id=x.business_id
                AND r.actor_id=a AND r.effect_id=prior.id AND r.provider_search_id=prior.search_id
                AND r.provider='apify' AND r.pilot_id=prior.pilot_id AND r.request_hash=prior.request_mac
                AND r.reserved_usd_micros=prior.reserved_usd_micros AND r.state='uncertain'
              JOIN public.outbox_events o ON o.tenant_id=proof.tenant_id AND o.id=proof.event_id
                AND o.event_type='reference.contacts_not_dispatched' AND o.payload=jsonb_build_object(
                  'business_id',p_business::text,'actor_id',a::text,'operation_id',prior.id::text)
              WHERE x.tenant_id=t AND x.business_id=p_business AND x.lookup_id=p_lookup
                AND x.attempt_no<attempt.attempt_no AND prior.state='failed_definitive';
            IF prior_count<>attempt.attempt_no-1 OR (attempt.attempt_no>1 AND NOT EXISTS(
              SELECT 1 FROM public.reference_contacts_effect_links previous WHERE previous.tenant_id=t
                AND previous.business_id=p_business AND previous.lookup_id=p_lookup
                AND previous.effect_id=attempt.previous_effect_id AND previous.attempt_no=attempt.attempt_no-1)) THEN
              RAISE EXCEPTION 'REFERENCE_CONTACTS_RETRY_BLOCKED'; END IF;
          END IF;
        END IF;
        RETURN public.reference_contacts_claim_retry_inner(p_business,p_lookup,p_effect,p_event,p_mac,p_pilot,p_amount,
          p_key,p_tariff,p_credential,p_class);
      END $$""")
    op.execute(f"ALTER FUNCTION public.reference_contacts_claim({_CLAIM}) OWNER TO meu_braco_direito_reference_ledger")
    op.execute(
        f"REVOKE ALL ON FUNCTION public.reference_contacts_claim({_CLAIM}) FROM PUBLIC,meu_braco_direito_correlator"
    )


def downgrade():
    op.execute("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))")
    op.execute("LOCK TABLE reference_provider_effects,reference_contacts_effect_links IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_contacts_failure_proofs) OR
      EXISTS(SELECT 1 FROM reference_contacts_effect_links WHERE attempt_no>1) OR
      EXISTS(SELECT 1 FROM reference_provider_effects WHERE state='failed_definitive') THEN
      RAISE EXCEPTION 'REFERENCE_CONTACTS_RETRY_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute(f"DROP FUNCTION public.reference_contacts_claim({_CLAIM})")
    op.execute(
        f"ALTER FUNCTION public.reference_contacts_claim_retry_inner({_CLAIM}) RENAME TO reference_contacts_claim"
    )
    op.execute(
        f"REVOKE ALL ON FUNCTION public.reference_contacts_claim({_CLAIM}) FROM PUBLIC,meu_braco_direito_correlator"
    )
    op.execute("DROP FUNCTION public.reference_contacts_not_dispatched(uuid,uuid,uuid,uuid)")
    op.execute("DROP POLICY reference_contacts_failure_event_emit ON outbox_events")
    op.execute("DROP POLICY reference_contacts_failure_event_read ON outbox_events")
    op.execute("DROP TABLE reference_contacts_failure_proofs")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed',
       'reference.provider_effect_requested','reference.provider_cost_changed','reference.provider_effect_completed',
       'reference.provider_search_requested','reference.provider_search_cancelled','reference.real_selection_confirmed',
       'reference.private_shortlist_prepared','reference.feed_resources_recorded'))""")
    op.execute("ALTER TABLE reference_contacts_effect_links DROP COLUMN previous_effect_id,DROP COLUMN attempt_no")
    op.execute("""ALTER TABLE reference_contacts_effect_links
      ADD UNIQUE(tenant_id,business_id,lookup_id)""")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_definitive_failure_contacts_only")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_check")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_state_check")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_effects_state_check
      CHECK(state IN ('pending','running','uncertain','completed_empty','completed_filtered')),
      ADD CONSTRAINT reference_provider_effects_check CHECK(
        (state='pending' AND executor_token IS NULL) OR
        (state IN ('running','uncertain','completed_empty','completed_filtered') AND executor_token IS NOT NULL))""")
