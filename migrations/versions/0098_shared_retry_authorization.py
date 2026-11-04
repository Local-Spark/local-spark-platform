"""Inactive business-owner authorization for a new contacts retry.

The NOLOGIN proof role can read only evidence columns, never executor tokens.
No caller receives EXECUTE and no new paid intent or provider request exists.
"""

from alembic import op

revision = "0098_shared_retry_authorization"
down_revision = "0097_reference_shared_read"
branch_labels = None
depends_on = None

_ROLE = "meu_braco_direito_reference_lock"


def upgrade():
    op.execute("""DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_reference_lock'
      AND NOT (rolcanlogin OR rolsuper OR rolbypassrls OR rolcreatedb OR rolcreaterole OR rolreplication)) OR
      EXISTS(SELECT 1 FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid OR r.oid=m.member
        WHERE r.rolname='meu_braco_direito_reference_lock') THEN
      RAISE EXCEPTION 'UNSAFE_REFERENCE_LOCK_ROLE'; END IF; END $$""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    for table in (
        "reference_real_heads",
        "reference_real_cycles",
        "business_context_heads",
        "reference_contacts_lookups",
        "reference_contacts_effect_links",
        "reference_contacts_failure_proofs",
        "reference_provider_effects",
        "reference_cost_reservations",
        "reference_provider_searches",
    ):
        op.execute(f"""CREATE POLICY reference_shared_retry_proof ON {table} FOR SELECT TO {_ROLE}
          USING(tenant_id={tenant})""")
    for table, columns in (
        ("reference_real_heads", "tenant_id,business_id,cycle_id"),
        ("reference_real_cycles", "tenant_id,business_id,id,locked_until"),
        ("business_context_heads", "tenant_id,business_id,version"),
        ("reference_contacts_lookups", "tenant_id,business_id,id,cycle_id,search_id"),
        ("reference_contacts_effect_links", "tenant_id,business_id,lookup_id,effect_id,attempt_no,previous_effect_id"),
        ("reference_contacts_failure_proofs", "tenant_id,business_id,lookup_id,effect_id,actor_id,event_id,reason"),
        (
            "reference_provider_effects",
            "tenant_id,business_id,id,actor_id,search_id,pilot_id,provider,state,request_mac,reserved_usd_micros",
        ),
        (
            "reference_cost_reservations",
            "tenant_id,business_id,actor_id,effect_id,provider_search_id,pilot_id,"
            "provider,request_hash,reserved_usd_micros,state",
        ),
        ("reference_provider_searches", "tenant_id,business_id,id,cycle_id,context_version"),
    ):
        op.execute(f"GRANT SELECT({columns}) ON {table} TO {_ROLE}")
    op.execute(f"""DO $$ BEGIN IF has_column_privilege('{_ROLE}',
      'public.reference_provider_effects','executor_token','SELECT') THEN
      RAISE EXCEPTION 'UNSAFE_REFERENCE_PROOF_TOKEN_ACCESS'; END IF; END $$""")
    for table, column in (
        ("reference_real_heads", "cycle_id"),
        ("reference_real_cycles", "locked_until"),
        ("business_context_heads", "version"),
        ("reference_contacts_lookups", "place_id"),
    ):
        op.execute(f"GRANT UPDATE({column}) ON {table} TO {_ROLE}")
        op.execute(f"""CREATE POLICY reference_shared_retry_lock ON {table} FOR UPDATE TO {_ROLE}
          USING(tenant_id={tenant}) WITH CHECK(tenant_id={tenant})""")
    op.execute(f"""CREATE POLICY reference_shared_retry_proof_event ON outbox_events FOR SELECT TO {_ROLE}
      USING(tenant_id={tenant} AND event_type='reference.contacts_not_dispatched')""")
    op.execute(f"GRANT SELECT(tenant_id,id,event_type,payload) ON outbox_events TO {_ROLE}")
    op.execute("""CREATE TABLE reference_contacts_retry_authorizations (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,id uuid NOT NULL,lookup_id uuid NOT NULL,
      previous_effect_id uuid NOT NULL,actor_id uuid NOT NULL REFERENCES user_accounts(id),
      operation_id uuid NOT NULL,event_id uuid NOT NULL,context_version bigint NOT NULL CHECK(context_version>0),
      PRIMARY KEY(tenant_id,business_id,id),UNIQUE(tenant_id,business_id,operation_id),
      UNIQUE(tenant_id,business_id,lookup_id,previous_effect_id),
      FOREIGN KEY(tenant_id,business_id,lookup_id,previous_effect_id)
        REFERENCES reference_contacts_effect_links(tenant_id,business_id,lookup_id,effect_id),
      FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id))""")
    op.execute("ALTER TABLE reference_contacts_retry_authorizations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reference_contacts_retry_authorizations FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY reference_shared_retry_authorizations ON reference_contacts_retry_authorizations
      TO {_ROLE} USING(tenant_id={tenant}) WITH CHECK(tenant_id={tenant})""")
    op.execute(f"GRANT SELECT,INSERT ON reference_contacts_retry_authorizations TO {_ROLE}")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed',
       'reference.provider_effect_requested','reference.provider_cost_changed','reference.provider_effect_completed',
       'reference.provider_search_requested','reference.provider_search_cancelled','reference.real_selection_confirmed',
       'reference.private_shortlist_prepared','reference.feed_resources_recorded','reference.contacts_not_dispatched',
       'reference.contacts_retry_authorized'))""")
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    op.execute(f"""CREATE POLICY reference_shared_retry_event_emit ON outbox_events FOR INSERT TO {_ROLE}
      WITH CHECK(tenant_id={tenant} AND event_type='reference.contacts_retry_authorized'
        AND payload->>'actor_id'={actor}::text)""")
    op.execute(f"""CREATE POLICY reference_shared_retry_event_read ON outbox_events FOR SELECT TO {_ROLE}
      USING(tenant_id={tenant} AND event_type='reference.contacts_retry_authorized')""")
    op.execute(f"GRANT INSERT(id,tenant_id,event_type,payload) ON outbox_events TO {_ROLE}")
    op.execute(f"""CREATE POLICY reference_shared_retry_audit_emit ON audit_events FOR INSERT TO {_ROLE}
      WITH CHECK(tenant_id={tenant} AND actor_id={actor} AND action='reference.contacts_retry_authorized')""")
    op.execute(f"GRANT INSERT(tenant_id,actor_id,operation_id,action,resource_id) ON audit_events TO {_ROLE}")
    op.execute("""CREATE FUNCTION public.reference_authorize_shared_contacts_retry(
      p_business uuid,p_lookup uuid,p_authorization uuid,p_operation uuid,p_event uuid) RETURNS jsonb
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        v_cycle_id uuid; cycle_end timestamptz; current_version bigint; lookup_cycle uuid; v_search_id uuid;
        expected_version bigint; previous uuid; previous_no integer; prior_count integer;
        prior public.reference_contacts_retry_authorizations%ROWTYPE;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_lookup IS NULL OR p_authorization IS NULL
          OR p_operation IS NULL OR p_event IS NULL THEN RAISE EXCEPTION 'REFERENCE_RETRY_AUTH_INVALID'; END IF;
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        SELECT h.cycle_id INTO v_cycle_id FROM public.reference_real_heads h
          WHERE h.tenant_id=t AND h.business_id=p_business FOR SHARE;
        SELECT h.version INTO current_version FROM public.business_context_heads h
          WHERE h.tenant_id=t AND h.business_id=p_business FOR SHARE;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO prior FROM public.reference_contacts_retry_authorizations WHERE tenant_id=t
          AND business_id=p_business AND operation_id=p_operation;
        IF FOUND THEN
          IF prior.actor_id IS DISTINCT FROM a OR prior.id IS DISTINCT FROM p_authorization
            OR prior.lookup_id IS DISTINCT FROM p_lookup OR NOT EXISTS(
              SELECT 1 FROM public.outbox_events o WHERE o.tenant_id=t AND o.id=prior.event_id
                AND o.event_type='reference.contacts_retry_authorized' AND o.payload=jsonb_build_object(
                  'business_id',p_business::text,'actor_id',a::text,'operation_id',p_operation::text)) THEN
            RAISE EXCEPTION 'REFERENCE_RETRY_AUTH_CONFLICT'; END IF;
          RETURN jsonb_build_object('authorization_id',prior.id,'event_id',prior.event_id,'created',false);
        END IF;
        SELECT c.locked_until INTO cycle_end FROM public.reference_real_cycles c
          WHERE c.tenant_id=t AND c.business_id=p_business AND c.id=v_cycle_id FOR SHARE;
        IF NOT FOUND OR (cycle_end IS NOT NULL AND cycle_end<=clock_timestamp()) THEN
          RAISE EXCEPTION 'REFERENCE_RETRY_CYCLE_INACTIVE'; END IF;
        SELECT l.cycle_id,l.search_id INTO lookup_cycle,v_search_id FROM public.reference_contacts_lookups l
          WHERE l.tenant_id=t AND l.business_id=p_business AND l.id=p_lookup FOR SHARE;
        IF NOT FOUND OR lookup_cycle IS DISTINCT FROM v_cycle_id THEN
          RAISE EXCEPTION 'REFERENCE_RETRY_LOOKUP_INVALID'; END IF;
        SELECT s.context_version INTO expected_version FROM public.reference_provider_searches s
          WHERE s.tenant_id=t AND s.business_id=p_business AND s.id=v_search_id AND s.cycle_id=v_cycle_id;
        IF NOT FOUND OR expected_version IS DISTINCT FROM current_version THEN
          RAISE EXCEPTION 'REFERENCE_CONTEXT_STALE'; END IF;
        SELECT x.effect_id,x.attempt_no INTO previous,previous_no FROM public.reference_contacts_effect_links x
          WHERE x.tenant_id=t AND x.business_id=p_business AND x.lookup_id=p_lookup ORDER BY x.attempt_no DESC LIMIT 1;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_CONTACTS_RETRY_BLOCKED'; END IF;
        SELECT count(*) INTO prior_count FROM public.reference_contacts_effect_links x
          JOIN public.reference_provider_effects e ON e.tenant_id=x.tenant_id AND e.business_id=x.business_id
            AND e.id=x.effect_id AND e.provider='apify' AND e.state='failed_definitive'
          JOIN public.reference_contacts_failure_proofs proof ON proof.tenant_id=x.tenant_id
            AND proof.business_id=x.business_id AND proof.lookup_id=x.lookup_id AND proof.effect_id=x.effect_id
            AND proof.actor_id=e.actor_id AND proof.reason='not_dispatched'
          JOIN public.reference_cost_reservations r ON r.tenant_id=e.tenant_id AND r.business_id=e.business_id
            AND r.actor_id=e.actor_id AND r.effect_id=e.id AND r.provider_search_id=e.search_id
            AND r.provider='apify' AND r.pilot_id=e.pilot_id AND r.request_hash=e.request_mac
            AND r.reserved_usd_micros=e.reserved_usd_micros AND r.state='uncertain'
          JOIN public.outbox_events o ON o.tenant_id=proof.tenant_id AND o.id=proof.event_id
            AND o.event_type='reference.contacts_not_dispatched' AND o.payload=jsonb_build_object(
              'business_id',p_business::text,'actor_id',e.actor_id::text,'operation_id',e.id::text)
          WHERE x.tenant_id=t AND x.business_id=p_business AND x.lookup_id=p_lookup AND e.search_id=v_search_id
            AND (x.attempt_no=1 AND x.previous_effect_id IS NULL OR x.attempt_no>1 AND EXISTS(
              SELECT 1 FROM public.reference_contacts_effect_links older WHERE older.tenant_id=x.tenant_id
                AND older.business_id=x.business_id AND older.lookup_id=x.lookup_id
                AND older.effect_id=x.previous_effect_id AND older.attempt_no=x.attempt_no-1));
        IF prior_count<>previous_no THEN RAISE EXCEPTION 'REFERENCE_CONTACTS_RETRY_BLOCKED'; END IF;
        IF EXISTS(SELECT 1 FROM public.reference_contacts_retry_authorizations WHERE tenant_id=t
          AND business_id=p_business AND lookup_id=p_lookup AND previous_effect_id=previous) THEN
          RAISE EXCEPTION 'REFERENCE_RETRY_ALREADY_AUTHORIZED'; END IF;
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(p_event,t,'reference.contacts_retry_authorized',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_operation::text));
        INSERT INTO public.reference_contacts_retry_authorizations
          (tenant_id,business_id,id,lookup_id,previous_effect_id,actor_id,operation_id,event_id,context_version)
          VALUES(t,p_business,p_authorization,p_lookup,previous,a,p_operation,p_event,current_version);
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_operation,'reference.contacts_retry_authorized',p_lookup);
        RETURN jsonb_build_object('authorization_id',p_authorization,'event_id',p_event,'created',true);
      END $$""")
    op.execute(f"""ALTER FUNCTION public.reference_authorize_shared_contacts_retry(uuid,uuid,uuid,uuid,uuid)
      OWNER TO {_ROLE}""")
    op.execute("""REVOKE ALL ON FUNCTION public.reference_authorize_shared_contacts_retry(uuid,uuid,uuid,uuid,uuid)
      FROM PUBLIC,meu_braco_direito_correlator,meu_braco_direito_app""")


def downgrade():
    op.execute("LOCK TABLE reference_contacts_retry_authorizations,outbox_events IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_contacts_retry_authorizations) OR
      EXISTS(SELECT 1 FROM outbox_events WHERE event_type='reference.contacts_retry_authorized') THEN
      RAISE EXCEPTION 'REFERENCE_SHARED_RETRY_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("DROP FUNCTION public.reference_authorize_shared_contacts_retry(uuid,uuid,uuid,uuid,uuid)")
    op.execute(f"REVOKE INSERT(tenant_id,actor_id,operation_id,action,resource_id) ON audit_events FROM {_ROLE}")
    op.execute("DROP POLICY reference_shared_retry_audit_emit ON audit_events")
    op.execute(
        f"REVOKE INSERT(id,tenant_id,event_type,payload),SELECT(tenant_id,id,event_type,payload) "
        f"ON outbox_events FROM {_ROLE}"
    )
    op.execute("DROP POLICY reference_shared_retry_event_emit ON outbox_events")
    op.execute("DROP POLICY reference_shared_retry_event_read ON outbox_events")
    op.execute("DROP POLICY reference_shared_retry_proof_event ON outbox_events")
    op.execute("DROP TABLE reference_contacts_retry_authorizations")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed',
       'reference.provider_effect_requested','reference.provider_cost_changed','reference.provider_effect_completed',
       'reference.provider_search_requested','reference.provider_search_cancelled','reference.real_selection_confirmed',
       'reference.private_shortlist_prepared','reference.feed_resources_recorded','reference.contacts_not_dispatched'))""")
    for table, column in (
        ("reference_real_heads", "cycle_id"),
        ("reference_real_cycles", "locked_until"),
        ("business_context_heads", "version"),
        ("reference_contacts_lookups", "place_id"),
    ):
        op.execute(f"REVOKE UPDATE({column}) ON {table} FROM {_ROLE}")
        op.execute(f"DROP POLICY reference_shared_retry_lock ON {table}")
    for table, columns in (
        ("reference_real_heads", "tenant_id,business_id,cycle_id"),
        ("reference_real_cycles", "tenant_id,business_id,id,locked_until"),
        ("business_context_heads", "tenant_id,business_id,version"),
        ("reference_contacts_lookups", "tenant_id,business_id,id,cycle_id,search_id"),
        ("reference_contacts_effect_links", "tenant_id,business_id,lookup_id,effect_id,attempt_no,previous_effect_id"),
        ("reference_contacts_failure_proofs", "tenant_id,business_id,lookup_id,effect_id,actor_id,event_id,reason"),
        (
            "reference_provider_effects",
            "tenant_id,business_id,id,actor_id,search_id,pilot_id,provider,state,request_mac,reserved_usd_micros",
        ),
        (
            "reference_cost_reservations",
            "tenant_id,business_id,actor_id,effect_id,provider_search_id,pilot_id,"
            "provider,request_hash,reserved_usd_micros,state",
        ),
        ("reference_provider_searches", "tenant_id,business_id,id,cycle_id,context_version"),
    ):
        op.execute(f"REVOKE SELECT({columns}) ON {table} FROM {_ROLE}")
        op.execute(f"DROP POLICY reference_shared_retry_proof ON {table}")
