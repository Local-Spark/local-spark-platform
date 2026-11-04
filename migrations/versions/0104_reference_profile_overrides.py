"""Let an active owner correct an existing suggested Instagram association."""

from alembic import op

revision = "0104_reference_profile_overrides"
down_revision = "0103_business_geocoding"
branch_labels = None
depends_on = None

_ROLE = "meu_braco_direito_reference_ledger"
_SIGNATURE = "uuid,uuid,uuid,bigint,uuid,uuid,text"


def upgrade():
    op.execute("""CREATE TABLE reference_profile_overrides (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,place_identity uuid NOT NULL,
      version bigint NOT NULL CHECK(version>0),instagram_handle text NOT NULL CHECK(
        instagram_handle ~ '^[a-z0-9_]([a-z0-9_.]{0,28}[a-z0-9_])?$' AND position('..' in instagram_handle)=0),
      actor_id uuid NOT NULL REFERENCES user_accounts(id),operation_id uuid NOT NULL,
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(tenant_id,business_id,place_identity,version),
      FOREIGN KEY(tenant_id,business_id,place_identity)
        REFERENCES reference_provider_places(tenant_id,business_id,id))""")
    op.execute("""CREATE TABLE reference_profile_override_heads (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,place_identity uuid NOT NULL,version bigint NOT NULL,
      PRIMARY KEY(tenant_id,business_id,place_identity),
      FOREIGN KEY(tenant_id,business_id,place_identity,version)
        REFERENCES reference_profile_overrides(tenant_id,business_id,place_identity,version))""")
    op.execute("""CREATE TABLE reference_profile_override_operations (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,operation_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),place_identity uuid NOT NULL,
      request jsonb NOT NULL,response jsonb NOT NULL,event_id uuid,
      PRIMARY KEY(tenant_id,business_id,operation_id),
      FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id),
      FOREIGN KEY(tenant_id,business_id,place_identity)
        REFERENCES reference_provider_places(tenant_id,business_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"tenant_id={tenant} AND EXISTS(SELECT 1 FROM memberships m JOIN user_accounts u ON u.id=m.actor_id "
        f"WHERE m.tenant_id={tenant} AND m.actor_id={actor} AND m.active AND m.role='owner' AND u.active)"
    )
    for table in (
        "reference_profile_overrides",
        "reference_profile_override_heads",
        "reference_profile_override_operations",
    ):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY reference_profile_ledger ON {table} TO {_ROLE} "
            f"USING(tenant_id={tenant}) WITH CHECK(tenant_id={tenant})"
        )
        op.execute(f"GRANT SELECT,INSERT ON {table} TO {_ROLE}")
    op.execute(f"GRANT UPDATE(version) ON reference_profile_override_heads TO {_ROLE}")
    for table in ("reference_profile_overrides", "reference_profile_override_heads"):
        op.execute(
            f"CREATE POLICY reference_profile_owner ON {table} FOR SELECT TO meu_braco_direito_app USING({owner})"
        )
        op.execute(f"GRANT SELECT ON {table} TO meu_braco_direito_app")
    op.execute("""DO $$ DECLARE expression text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO expression FROM pg_constraint
        WHERE conrelid='public.outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE public.outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE public.outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' ||
        expression || ') OR event_type=''reference.profile_changed'')';
    END $$""")
    op.execute(f"""CREATE POLICY reference_profile_event ON outbox_events FOR INSERT TO {_ROLE}
      WITH CHECK(tenant_id={tenant} AND event_type='reference.profile_changed'
        AND payload->>'actor_id'={actor}::text)""")
    op.execute("""CREATE FUNCTION public.reference_save_profile_override(
      p_business uuid,p_place uuid,p_operation uuid,p_expected bigint,p_result uuid,p_candidate uuid,p_handle text)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        current_cycle uuid;current_version bigint;canonical jsonb;reply jsonb;event uuid;
        previous public.reference_profile_override_operations%ROWTYPE;
        current_profile public.reference_profile_overrides%ROWTYPE;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_place IS NULL OR p_operation IS NULL
          OR p_expected IS NULL OR p_expected<0 OR p_result IS NULL OR p_candidate IS NULL OR p_handle IS NULL
          OR p_handle !~ '^[a-z0-9_]([a-z0-9_.]{0,28}[a-z0-9_])?$' OR position('..' in p_handle)>0 THEN
          RAISE EXCEPTION 'REFERENCE_PROFILE_INVALID'; END IF;
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        SELECT cycle_id INTO current_cycle FROM public.reference_real_heads
          WHERE tenant_id=t AND business_id=p_business FOR UPDATE;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_PROFILE_OCCURRENCE_INVALID'; END IF;
        canonical := jsonb_build_object('place_identity',p_place,'expected_version',p_expected,
          'result_id',p_result,'candidate_id',p_candidate,'instagram_handle',p_handle);
        SELECT * INTO previous FROM public.reference_profile_override_operations
          WHERE tenant_id=t AND business_id=p_business AND operation_id=p_operation;
        IF FOUND THEN
          IF previous.actor_id IS DISTINCT FROM a OR previous.request IS DISTINCT FROM canonical THEN
            RAISE EXCEPTION 'REFERENCE_PROFILE_OPERATION_CONFLICT'; END IF;
          RETURN previous.response;
        END IF;
        IF NOT EXISTS(SELECT 1 FROM public.reference_provider_result_candidates c
          JOIN public.reference_provider_results r ON
            (r.tenant_id,r.business_id,r.id)=(c.tenant_id,c.business_id,c.result_id)
          JOIN public.reference_real_published_results pub ON (pub.tenant_id,pub.business_id,pub.result_id)
            =(r.tenant_id,r.business_id,r.id)
          JOIN public.reference_provider_searches s ON (s.tenant_id,s.business_id,s.id)
            =(r.tenant_id,r.business_id,r.search_id)
          WHERE c.tenant_id=t AND c.business_id=p_business AND c.result_id=p_result AND c.id=p_candidate
            AND c.place_id=p_place AND s.state='completed' AND (s.cycle_id=current_cycle OR EXISTS(
              SELECT 1 FROM public.reference_real_selected selected WHERE selected.tenant_id=t
                AND selected.business_id=p_business AND selected.place_id=p_place))) THEN
          RAISE EXCEPTION 'REFERENCE_PROFILE_OCCURRENCE_INVALID'; END IF;
        SELECT v.* INTO current_profile FROM public.reference_profile_override_heads h
          JOIN public.reference_profile_overrides v USING(tenant_id,business_id,place_identity,version)
          WHERE h.tenant_id=t AND h.business_id=p_business AND h.place_identity=p_place;
        current_version := coalesce(current_profile.version,0);
        IF p_expected<>current_version THEN RAISE EXCEPTION 'REFERENCE_PROFILE_VERSION_CONFLICT'; END IF;
        IF current_profile.instagram_handle IS DISTINCT FROM p_handle THEN
          current_version := current_version+1;
          INSERT INTO public.reference_profile_overrides
            (tenant_id,business_id,place_identity,version,instagram_handle,actor_id,operation_id)
            VALUES(t,p_business,p_place,current_version,p_handle,a,p_operation) RETURNING * INTO current_profile;
          INSERT INTO public.reference_profile_override_heads VALUES(t,p_business,p_place,current_version)
            ON CONFLICT(tenant_id,business_id,place_identity) DO UPDATE SET version=excluded.version;
          event := gen_random_uuid();
          INSERT INTO public.outbox_events(id,tenant_id,event_type,payload) VALUES(event,t,'reference.profile_changed',
            jsonb_build_object('business_id',p_business::text,'actor_id',a::text,'operation_id',p_operation::text,
              'place_identity',p_place::text,'profile_version',current_version));
        END IF;
        reply := jsonb_build_object('place_identity',p_place,'version',current_version,'instagram_handle',p_handle,
          'profile_source','owner','updated_at',current_profile.created_at);
        INSERT INTO public.reference_profile_override_operations
          VALUES(t,p_business,p_operation,a,p_place,canonical,reply,event);
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_operation,'reference.profile_override_saved',p_place);
        RETURN reply;
      END $$""")
    op.execute(f"ALTER FUNCTION public.reference_save_profile_override({_SIGNATURE}) OWNER TO {_ROLE}")
    op.execute(f"REVOKE ALL ON FUNCTION public.reference_save_profile_override({_SIGNATURE}) FROM PUBLIC")
    op.execute(
        f"GRANT EXECUTE ON FUNCTION public.reference_save_profile_override({_SIGNATURE}) TO meu_braco_direito_app"
    )


def downgrade():
    op.execute("""LOCK TABLE reference_profile_override_heads,reference_profile_overrides,
      reference_profile_override_operations IN ACCESS EXCLUSIVE MODE""")
    op.execute("SET LOCAL row_security=off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_profile_overrides)
      OR EXISTS(SELECT 1 FROM reference_profile_override_operations)
      OR EXISTS(SELECT 1 FROM outbox_events WHERE event_type='reference.profile_changed') THEN
      RAISE EXCEPTION 'REFERENCE_PROFILES_PREVENT_AUTOMATIC_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security=on")
    op.execute(f"DROP FUNCTION public.reference_save_profile_override({_SIGNATURE})")
    op.execute("DROP POLICY reference_profile_event ON outbox_events")
    op.execute(
        "DROP TABLE reference_profile_override_heads,reference_profile_override_operations,reference_profile_overrides"
    )
    # The existing allowlist remains valid for other slices. Remove this event
    # semantically without rewriting unrelated migrations' event additions.
    op.execute("""DO $$ DECLARE expression text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO expression FROM pg_constraint
        WHERE conrelid='public.outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE public.outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE public.outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' ||
        expression || ') AND event_type<>''reference.profile_changed'')';
    END $$""")
