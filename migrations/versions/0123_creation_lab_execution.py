"""Private execution accounting and expiring diagnostic evidence."""

from alembic import op

revision = "0123_creation_lab_execution"
down_revision = "0122_creation_lab_collection"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE creation_lab_runs DROP CONSTRAINT creation_lab_runs_state_check")
    op.execute("""ALTER TABLE creation_lab_runs
      ADD CHECK(state IN ('draft','queued','running','awaiting_approval','completed','failed','uncertain','cancelled')),
      ADD COLUMN execution_token uuid,
      ADD COLUMN finished_at timestamptz,
      ADD COLUMN trace_expires_at timestamptz,
      ADD COLUMN trace_purged_at timestamptz,
      ADD COLUMN failure_code text,
      ADD COLUMN committed_usd_micros bigint NOT NULL DEFAULT 0 CHECK(committed_usd_micros>=0)""")
    op.execute("""GRANT UPDATE(state,execution_token,finished_at,trace_expires_at,trace_purged_at,
      failure_code,committed_usd_micros) ON creation_lab_runs TO meu_braco_direito_app""")
    op.execute("""CREATE TABLE creation_lab_effects (
      id uuid PRIMARY KEY,run_id uuid NOT NULL REFERENCES creation_lab_runs(id),
      kind text NOT NULL,request_hash char(64) NOT NULL,
      state text NOT NULL CHECK(state IN ('claimed','submitted','received','uncertain')),
      provider text,model text,
      reserved_usd_micros bigint NOT NULL CHECK(reserved_usd_micros>=0),
      estimated_usd_micros bigint CHECK(estimated_usd_micros>=0),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),finished_at timestamptz)""")
    op.execute("""CREATE TABLE creation_lab_trace (
      id uuid PRIMARY KEY,run_id uuid NOT NULL REFERENCES creation_lab_runs(id),
      effect_id uuid REFERENCES creation_lab_effects(id),
      stage text NOT NULL,slot text NOT NULL CHECK(slot IN ('request','response','partial','evidence')),
      payload_ciphertext text,created_at timestamptz NOT NULL DEFAULT clock_timestamp())""")
    for table in ("creation_lab_effects", "creation_lab_trace"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY lab_private ON {table} TO meu_braco_direito_app
          USING(EXISTS(SELECT 1 FROM creation_lab_runs r WHERE r.id=run_id))
          WITH CHECK(EXISTS(SELECT 1 FROM creation_lab_runs r WHERE r.id=run_id))""")
        op.execute(f"GRANT SELECT,INSERT ON {table} TO meu_braco_direito_app")
    op.execute("GRANT UPDATE(state,estimated_usd_micros,finished_at) ON creation_lab_effects TO meu_braco_direito_app")
    op.execute("CREATE INDEX creation_lab_effects_run ON creation_lab_effects(run_id,created_at)")
    op.execute("CREATE INDEX creation_lab_trace_run ON creation_lab_trace(run_id,created_at)")
    op.execute("ALTER TABLE creation_lab_events ADD COLUMN trace_id uuid REFERENCES creation_lab_trace(id)")
    op.execute("ALTER TABLE creation_lab_events DROP CONSTRAINT creation_lab_events_kind_check")
    op.execute("""ALTER TABLE creation_lab_events ADD CHECK(kind ~
      '^(draft|attachment|collection|run|effect|checkpoint|artifact|feedback|trace)\\.[a-z_]{1,48}$')""")
    # Only already expired diagnostics may be purged; materials and financial
    # evidence are deliberately outside this narrow capability.
    op.execute("""CREATE FUNCTION creation_lab_expire_trace(p_run uuid) RETURNS bigint
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE r public.creation_lab_runs%ROWTYPE;
      BEGIN
        PERFORM pg_advisory_xact_lock(hashtextextended(p_run::text,120));
        SELECT * INTO r FROM public.creation_lab_runs WHERE id=p_run;
        IF NOT FOUND OR r.finished_at IS NULL OR r.trace_expires_at IS NULL THEN RETURN -1; END IF;
        IF r.trace_purged_at IS NOT NULL THEN RETURN 0; END IF;
        IF r.trace_expires_at>clock_timestamp() THEN
          RETURN greatest(1,ceil(extract(epoch FROM r.trace_expires_at-clock_timestamp()))::bigint); END IF;
        UPDATE public.creation_lab_trace SET payload_ciphertext=NULL WHERE run_id=p_run;
        UPDATE public.creation_lab_runs SET trace_purged_at=clock_timestamp() WHERE id=p_run;
        INSERT INTO public.creation_lab_events(run_id,sequence,event_id,kind)
          SELECT p_run,coalesce(max(sequence),0)+1,gen_random_uuid(),'trace.expired'
          FROM public.creation_lab_events WHERE run_id=p_run;
        RETURN 0;
      END $$""")
    op.execute("REVOKE ALL ON FUNCTION creation_lab_expire_trace(uuid) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION creation_lab_expire_trace(uuid) TO meu_braco_direito_app")
    op.execute("""DO $$ DECLARE previous text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO previous FROM pg_constraint
        WHERE conrelid='outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' ||
        previous || ') OR event_type=''creation_lab.trace_cleanup_requested'')';
    END $$""")


def downgrade():
    op.execute("DROP FUNCTION creation_lab_expire_trace(uuid)")
    op.execute("ALTER TABLE creation_lab_events DROP COLUMN trace_id")
    op.execute("DROP TABLE creation_lab_trace")
    op.execute("DROP TABLE creation_lab_effects")
    op.execute("""ALTER TABLE creation_lab_runs DROP COLUMN execution_token,DROP COLUMN finished_at,
      DROP COLUMN trace_expires_at,DROP COLUMN trace_purged_at,DROP COLUMN failure_code,
      DROP COLUMN committed_usd_micros""")
    # A rollback with real executions requires explicit data handling, never
    # silently rewriting terminal executions into drafts.
    op.execute("ALTER TABLE creation_lab_runs DROP CONSTRAINT creation_lab_runs_state_check")
    op.execute("ALTER TABLE creation_lab_runs ADD CHECK(state IN ('draft'))")
