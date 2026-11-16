"""Scope shared creation executions by transport; laboratory remains private."""

from alembic import op

revision = "0130_message_creation_scope"
down_revision = "0129_content_continuations"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE creation_lab_runs
      ADD COLUMN origin text NOT NULL DEFAULT 'lab' CHECK(origin IN ('lab','whatsapp')),
      ADD COLUMN flow_version integer NOT NULL DEFAULT 1 CHECK(flow_version IN (1,2)),
      ADD COLUMN source_event_id uuid UNIQUE,
      ADD COLUMN normalized_message_ciphertext text,
      ADD COLUMN output_piece_id uuid""")
    op.execute("ALTER TABLE creation_lab_runs DROP CONSTRAINT creation_lab_runs_format_check")
    op.execute(
        "ALTER TABLE creation_lab_runs ADD CONSTRAINT creation_lab_runs_format_check CHECK(format IN ('auto','photo','story','reel'))"
    )
    op.execute(
        "GRANT UPDATE(format,output_piece_id,normalized_message_ciphertext) ON creation_lab_runs TO meu_braco_direito_app"
    )
    op.execute(
        "ALTER TABLE creation_lab_effects ADD COLUMN commercial_reservation_id uuid, ADD COLUMN commercial_tenant_id uuid, ADD FOREIGN KEY(commercial_tenant_id,commercial_reservation_id) REFERENCES visual_cost_reservations(tenant_id,id)"
    )
    op.execute("""CREATE TABLE message_creation_deliveries (
      id uuid PRIMARY KEY,run_id uuid NOT NULL UNIQUE REFERENCES creation_lab_runs(id),
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,actor_id uuid NOT NULL,
      recipient_hash char(64) NOT NULL, provider_message_id text NOT NULL UNIQUE,
      message_ciphertext text NOT NULL,kind text NOT NULL CHECK(kind IN ('question','result')),
      stage text,content_sha256 char(64) NOT NULL,simulated boolean NOT NULL DEFAULT true CHECK(simulated),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      expires_at timestamptz NOT NULL DEFAULT clock_timestamp()+interval '7 days',
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("ALTER TABLE message_creation_deliveries ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE message_creation_deliveries FORCE ROW LEVEL SECURITY")
    op.execute("""CREATE POLICY message_delivery_owner ON message_creation_deliveries TO meu_braco_direito_app
      USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND EXISTS(
        SELECT 1 FROM memberships m WHERE m.tenant_id=message_creation_deliveries.tenant_id
          AND m.actor_id=nullif(current_setting('app.actor_id',true),'')::uuid AND m.role='owner' AND m.active))
      WITH CHECK(EXISTS(SELECT 1 FROM creation_lab_runs r WHERE r.id=run_id AND r.origin='whatsapp'
        AND r.tenant_id=message_creation_deliveries.tenant_id AND r.business_id=message_creation_deliveries.business_id
        AND r.actor_id=message_creation_deliveries.actor_id))""")
    op.execute("GRANT SELECT,INSERT ON message_creation_deliveries TO meu_braco_direito_app")
    op.execute("""CREATE POLICY message_audio_usage ON audio_transcription_usage TO meu_braco_direito_app
      USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND EXISTS(
        SELECT 1 FROM memberships m WHERE m.tenant_id=audio_transcription_usage.tenant_id
        AND m.actor_id=nullif(current_setting('app.actor_id',true),'')::uuid AND m.active AND m.role='owner'))
      WITH CHECK(EXISTS(SELECT 1 FROM creation_lab_runs r WHERE r.id=nullif(current_setting('app.creation_lab_run_id',true),'')::uuid
        AND r.origin='whatsapp' AND r.source_event_id=event_id AND r.tenant_id=audio_transcription_usage.tenant_id
        AND r.business_id=audio_transcription_usage.business_id))""")
    op.execute("GRANT SELECT,INSERT,UPDATE(state) ON audio_transcription_usage TO meu_braco_direito_app")
    op.execute("ALTER TABLE creation_lab_attachments ADD COLUMN active boolean NOT NULL DEFAULT true")
    op.execute("GRANT UPDATE(active) ON creation_lab_attachments TO meu_braco_direito_app")
    # No customer-facing API exposes these execution/trace tables. The scope is
    # set internally and never accepted from a tenant/header supplied by clients.
    op.execute("""CREATE FUNCTION message_creation_owned(t uuid,a uuid) RETURNS boolean
      LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
        SELECT a=nullif(current_setting('app.actor_id',true),'')::uuid AND EXISTS(
          SELECT 1 FROM public.memberships m JOIN public.user_accounts u ON u.id=m.actor_id
          WHERE m.tenant_id=t AND m.actor_id=a AND m.role='owner' AND m.active AND u.active)
      $$""")
    op.execute("REVOKE ALL ON FUNCTION message_creation_owned(uuid,uuid) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION message_creation_owned(uuid,uuid) TO meu_braco_direito_app")
    op.execute("""CREATE POLICY message_creation_owner ON creation_lab_runs TO meu_braco_direito_app
      USING(origin='whatsapp' AND id=nullif(current_setting('app.creation_lab_run_id',true),'')::uuid
        AND public.message_creation_owned(tenant_id,actor_id))
      WITH CHECK(origin='whatsapp' AND id=nullif(current_setting('app.creation_lab_run_id',true),'')::uuid
        AND public.message_creation_owned(tenant_id,actor_id) AND source_event_id IS NOT NULL)""")
    op.execute("""CREATE OR REPLACE FUNCTION creation_lab_read_scope(target_tenant uuid,target_business uuid)
      RETURNS boolean LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog,public AS $$
      SELECT target_tenant=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND EXISTS(SELECT 1 FROM public.creation_lab_runs r
          WHERE r.id=nullif(current_setting('app.creation_lab_run_id',true),'')::uuid
            AND r.actor_id=nullif(current_setting('app.actor_id',true),'')::uuid
            AND r.tenant_id=target_tenant AND r.business_id=target_business
            AND ((r.origin='lab' AND public.is_platform_staff()) OR
              (r.origin='whatsapp' AND public.message_creation_owned(r.tenant_id,r.actor_id))))
      $$""")
    op.execute("""CREATE FUNCTION message_creation_origin_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN IF (NEW.origin,NEW.flow_version,NEW.source_event_id,NEW.actor_id,NEW.tenant_id,NEW.business_id)
        IS DISTINCT FROM (OLD.origin,OLD.flow_version,OLD.source_event_id,OLD.actor_id,OLD.tenant_id,OLD.business_id)
        THEN RAISE EXCEPTION 'MESSAGE_CREATION_SCOPE_IMMUTABLE'; END IF; RETURN NEW; END $$""")
    op.execute(
        "CREATE TRIGGER message_creation_origin_immutable BEFORE UPDATE ON creation_lab_runs FOR EACH ROW EXECUTE FUNCTION message_creation_origin_immutable()"
    )


def downgrade():
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM creation_lab_runs WHERE flow_version=2)
      THEN RAISE EXCEPTION 'MESSAGE_CREATION_EXECUTIONS_EXIST'; END IF; END $$""")
    op.execute("DROP POLICY message_audio_usage ON audio_transcription_usage")
    op.execute("REVOKE SELECT,INSERT,UPDATE(state) ON audio_transcription_usage FROM meu_braco_direito_app")
    op.execute("ALTER TABLE creation_lab_attachments DROP COLUMN active")
    op.execute("DROP TABLE message_creation_deliveries")
    op.execute(
        "ALTER TABLE creation_lab_effects DROP COLUMN commercial_reservation_id,DROP COLUMN commercial_tenant_id"
    )
    op.execute("DROP TRIGGER message_creation_origin_immutable ON creation_lab_runs")
    op.execute("DROP FUNCTION message_creation_origin_immutable()")
    op.execute("DROP POLICY message_creation_owner ON creation_lab_runs")
    op.execute("""CREATE OR REPLACE FUNCTION creation_lab_read_scope(target_tenant uuid,target_business uuid)
      RETURNS boolean LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog,public AS $$
      SELECT target_tenant=nullif(current_setting('app.tenant_id',true),'')::uuid AND public.is_platform_staff()
        AND EXISTS(SELECT 1 FROM public.creation_lab_runs r WHERE r.id=nullif(current_setting('app.creation_lab_run_id',true),'')::uuid
        AND r.actor_id=nullif(current_setting('app.actor_id',true),'')::uuid AND r.tenant_id=target_tenant AND r.business_id=target_business) $$""")
    op.execute("DROP FUNCTION message_creation_owned(uuid,uuid)")
    op.execute(
        "ALTER TABLE creation_lab_runs DROP COLUMN normalized_message_ciphertext,DROP COLUMN origin,DROP COLUMN flow_version,DROP COLUMN source_event_id,DROP COLUMN output_piece_id"
    )
    op.execute("ALTER TABLE creation_lab_runs DROP CONSTRAINT creation_lab_runs_format_check")
    op.execute(
        "ALTER TABLE creation_lab_runs ADD CONSTRAINT creation_lab_runs_format_check CHECK(format IN ('photo','story','reel'))"
    )
