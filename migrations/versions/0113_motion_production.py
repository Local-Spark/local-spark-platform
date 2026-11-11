"""Durable private HTML motion requests, effects and immutable render evidence."""

from alembic import op

revision = "0113_motion_production"
down_revision = "0112_piece_reviews"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""DO $$ DECLARE previous text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO previous FROM pg_constraint
        WHERE conrelid='outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' ||
        previous || ') OR event_type IN (''motion.requested'',''motion.completed'',''motion.failed''))';
    END $$""")
    op.execute("""CREATE TABLE motion_requests (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),operation_id uuid NOT NULL,
      request_hash char(64) NOT NULL,source_asset_id uuid NOT NULL,
      format text NOT NULL CHECK(format IN ('reel','story_video')),
      state text NOT NULL CHECK(state IN ('queued','running','completed','failed','uncertain')),
      snapshot_ciphertext text NOT NULL,source_fingerprint char(64) NOT NULL,
      piece_id uuid,failure_code text,execution_token uuid,
      budget_usd_micros bigint NOT NULL CHECK(budget_usd_micros>0),
      max_corrections integer NOT NULL CHECK(max_corrections BETWEEN 0 AND 2),
      created_at timestamptz NOT NULL DEFAULT now(),admitted_at timestamptz,finished_at timestamptz,
      PRIMARY KEY(tenant_id,business_id,id),UNIQUE(tenant_id,operation_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id),
      FOREIGN KEY(tenant_id,business_id,piece_id) REFERENCES content_pieces(tenant_id,business_id,id),
      CHECK((state='completed')=(piece_id IS NOT NULL)))""")
    op.execute("""ALTER TABLE whatsapp_material_assets ADD CONSTRAINT motion_source_scope
      UNIQUE(tenant_id,business_id,id)""")
    op.execute("""CREATE TABLE motion_request_assets (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,request_id uuid NOT NULL,asset_id uuid NOT NULL,
      PRIMARY KEY(tenant_id,business_id,request_id,asset_id),
      FOREIGN KEY(tenant_id,business_id,request_id) REFERENCES motion_requests(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,asset_id) REFERENCES whatsapp_material_assets(tenant_id,business_id,id)
        ON DELETE CASCADE)""")
    op.execute("""CREATE TABLE motion_effects (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,request_id uuid NOT NULL,operation_id uuid NOT NULL,
      kind text NOT NULL CHECK(kind IN ('generate','review','correct','render','upload')),
      state text NOT NULL CHECK(state IN ('claimed','submitted','received','uncertain')),
      request_hash char(64) NOT NULL,request_ciphertext text NOT NULL,reservation_id uuid,
      reserved_usd_micros bigint NOT NULL DEFAULT 0 CHECK(reserved_usd_micros>=0),
      response_ciphertext text,estimated_usd_micros bigint CHECK(estimated_usd_micros>=0),
      created_at timestamptz NOT NULL DEFAULT now(),finished_at timestamptz,
      PRIMARY KEY(tenant_id,operation_id),
      FOREIGN KEY(tenant_id,business_id,request_id) REFERENCES motion_requests(tenant_id,business_id,id))""")
    op.execute("""CREATE TABLE motion_render_versions (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,request_id uuid NOT NULL,number integer NOT NULL,
      operation_id uuid NOT NULL,composition_ciphertext text NOT NULL,review_ciphertext text,
      object_key text NOT NULL,sha256 char(64) NOT NULL,size_bytes bigint NOT NULL,
      evidence_ciphertext text NOT NULL,diagnostics_ciphertext text NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(tenant_id,business_id,request_id,number),UNIQUE(tenant_id,operation_id),
      FOREIGN KEY(tenant_id,business_id,request_id) REFERENCES motion_requests(tenant_id,business_id,id),
      CHECK(number BETWEEN 0 AND 2),CHECK(size_bytes>0 AND size_bytes<=52428800))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    for table in ("motion_requests", "motion_request_assets", "motion_effects", "motion_render_versions"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY motion_owner ON {table} TO meu_braco_direito_app
          USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
        op.execute(f"GRANT SELECT,INSERT ON {table} TO meu_braco_direito_app")
    op.execute("""GRANT UPDATE(state,piece_id,failure_code,execution_token,admitted_at,finished_at)
      ON motion_requests TO meu_braco_direito_app""")
    op.execute("""GRANT UPDATE(state,reservation_id,response_ciphertext,estimated_usd_micros,finished_at)
      ON motion_effects TO meu_braco_direito_app""")
    op.execute("GRANT UPDATE(review_ciphertext) ON motion_render_versions TO meu_braco_direito_app")
    op.execute("""CREATE VIEW creative_active_runs WITH(security_invoker=true) AS
      SELECT tenant_id,business_id,actor_id,operation_id,state FROM visual_consent_runs WHERE state='in_flight'
      UNION ALL SELECT tenant_id,business_id,actor_id,operation_id,'in_flight' FROM motion_requests
        WHERE state IN ('running','uncertain')""")
    op.execute("GRANT SELECT ON creative_active_runs TO meu_braco_direito_app")
    # Retention already operates across tenants. This grants one boolean only, not
    # access to snapshots or creative data, and prevents removing an active input.
    op.execute("""CREATE FUNCTION motion_asset_in_use(source uuid) RETURNS boolean
      LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
        SELECT EXISTS(SELECT 1 FROM public.motion_request_assets a JOIN public.motion_requests r
          ON r.tenant_id=a.tenant_id AND r.business_id=a.business_id AND r.id=a.request_id
          WHERE a.asset_id=source AND r.state IN ('running','uncertain')) $$""")
    op.execute("REVOKE ALL ON FUNCTION motion_asset_in_use(uuid) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION motion_asset_in_use(uuid) TO meu_braco_direito_correlator")
    op.execute("""CREATE FUNCTION motion_record_result(p_tenant uuid,p_business uuid,p_request uuid,
      p_actor uuid,p_token uuid,p_operation uuid,p_response text,p_estimate bigint) RETURNS boolean
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      BEGIN
        IF p_tenant IS DISTINCT FROM nullif(current_setting('app.tenant_id',true),'')::uuid
          OR p_actor IS DISTINCT FROM nullif(current_setting('app.actor_id',true),'')::uuid
          OR length(p_response)>8388608 OR p_estimate<0 THEN RETURN false; END IF;
        UPDATE public.motion_effects e SET state='received',response_ciphertext=p_response,
          estimated_usd_micros=p_estimate,finished_at=clock_timestamp()
          WHERE e.tenant_id=p_tenant AND e.business_id=p_business AND e.request_id=p_request
            AND e.operation_id=p_operation AND e.state IN ('claimed','submitted') AND EXISTS(
              SELECT 1 FROM public.motion_requests r WHERE r.tenant_id=p_tenant AND r.business_id=p_business
                AND r.id=p_request AND r.actor_id=p_actor AND r.execution_token=p_token
                AND r.state IN ('running','uncertain'));
        IF NOT FOUND THEN RETURN false; END IF;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(p_tenant,p_actor,p_operation,'motion.effect_received',p_business);
        RETURN true;
      END $$""")
    op.execute("""CREATE FUNCTION motion_quarantine_request(p_tenant uuid,p_business uuid,p_request uuid,
      p_actor uuid,p_token uuid,p_code text,p_event uuid) RETURNS boolean
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE operation uuid;
      BEGIN
        IF p_tenant IS DISTINCT FROM nullif(current_setting('app.tenant_id',true),'')::uuid
          OR p_actor IS DISTINCT FROM nullif(current_setting('app.actor_id',true),'')::uuid
          OR p_code !~ '^[A-Z0-9_]{1,100}$' THEN RETURN false; END IF;
        UPDATE public.motion_requests SET state='uncertain',failure_code=p_code,finished_at=clock_timestamp()
          WHERE tenant_id=p_tenant AND business_id=p_business AND id=p_request AND actor_id=p_actor
            AND execution_token=p_token AND state='running' RETURNING operation_id INTO operation;
        IF NOT FOUND THEN RETURN false; END IF;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(p_tenant,p_actor,operation,'motion.failed',p_business);
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(p_event,p_tenant,'motion.failed',jsonb_build_object('business_id',p_business,
            'actor_id',p_actor,'operation_id',operation));
        RETURN true;
      END $$""")
    for signature in (
        "motion_record_result(uuid,uuid,uuid,uuid,uuid,uuid,text,bigint)",
        "motion_quarantine_request(uuid,uuid,uuid,uuid,uuid,text,uuid)",
    ):
        op.execute(f"REVOKE ALL ON FUNCTION {signature} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {signature} TO meu_braco_direito_correlator")
    role = "meu_braco_direito_motion_recorder"
    op.execute(f"""DO $$ BEGIN
      IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='{role}') THEN
        CREATE ROLE {role} NOLOGIN NOSUPERUSER NOBYPASSRLS; END IF;
      IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='{role}' AND (rolcanlogin OR rolsuper OR rolbypassrls)) THEN
        RAISE EXCEPTION 'UNSAFE_MOTION_RECORDER_ROLE'; END IF;
      END $$""")
    op.execute(f"GRANT USAGE ON SCHEMA public TO {role}")
    op.execute(f"""GRANT SELECT(tenant_id,business_id,id,actor_id,operation_id,execution_token,state),
      UPDATE(state,failure_code,finished_at) ON motion_requests TO {role}""")
    op.execute(f"""GRANT SELECT(tenant_id,business_id,request_id,operation_id,state),
      UPDATE(state,response_ciphertext,estimated_usd_micros,finished_at) ON motion_effects TO {role}""")
    op.execute(f"GRANT SELECT ON motion_request_assets TO {role}")
    for table in ("motion_requests", "motion_effects", "motion_request_assets"):
        # Functions check exact tenant/actor/token; this no-login owner only sees
        # structural columns. The retention function needs one cross-tenant bit.
        op.execute(f"CREATE POLICY motion_recorder ON {table} TO {role} USING(true) WITH CHECK(true)")
    op.execute(f"GRANT INSERT ON audit_events,outbox_events TO {role}")
    op.execute(f"""CREATE POLICY motion_recorder_audit ON audit_events FOR INSERT TO {role}
      WITH CHECK(tenant_id={tenant} AND actor_id={actor}
        AND action IN ('motion.effect_received','motion.failed'))""")
    op.execute(f"""CREATE POLICY motion_recorder_event ON outbox_events FOR INSERT TO {role}
      WITH CHECK(tenant_id={tenant} AND event_type='motion.failed')""")
    for signature in (
        "motion_asset_in_use(uuid)",
        "motion_record_result(uuid,uuid,uuid,uuid,uuid,uuid,text,bigint)",
        "motion_quarantine_request(uuid,uuid,uuid,uuid,uuid,text,uuid)",
    ):
        op.execute(f"ALTER FUNCTION {signature} OWNER TO {role}")


def downgrade():
    op.execute("DROP FUNCTION motion_record_result(uuid,uuid,uuid,uuid,uuid,uuid,text,bigint)")
    op.execute("DROP FUNCTION motion_quarantine_request(uuid,uuid,uuid,uuid,uuid,text,uuid)")
    op.execute("DROP FUNCTION motion_asset_in_use(uuid)")
    op.execute("DROP VIEW creative_active_runs")
    op.execute("DROP POLICY IF EXISTS motion_recorder_audit ON audit_events")
    op.execute("DROP POLICY IF EXISTS motion_recorder_event ON outbox_events")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_motion_recorder') THEN
      REVOKE INSERT ON audit_events,outbox_events FROM meu_braco_direito_motion_recorder; END IF; END $$""")
    for table in ("motion_render_versions", "motion_effects", "motion_request_assets", "motion_requests"):
        op.execute(f"DROP TABLE {table}")
    op.execute("ALTER TABLE whatsapp_material_assets DROP CONSTRAINT motion_source_scope")
