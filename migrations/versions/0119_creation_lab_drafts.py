"""Private administrative drafts and durable event stream, without generation."""

from alembic import op

revision = "0119_creation_lab_drafts"
down_revision = "0118_motion_checkpoint_events"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE creation_lab_runs (
      id uuid PRIMARY KEY, actor_id uuid NOT NULL REFERENCES user_accounts(id),
      tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      operation_id uuid NOT NULL, request_hash char(64) NOT NULL,
      format text NOT NULL CHECK(format IN ('photo','story','reel')),
      mode text NOT NULL CHECK(mode IN ('automatic','accompanied')),
      instruction_ciphertext text NOT NULL,
      budget_usd_micros bigint NOT NULL CHECK(budget_usd_micros>0),
      state text NOT NULL DEFAULT 'draft' CHECK(state IN ('draft')),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      UNIQUE(actor_id,operation_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id)
    )""")
    op.execute("""CREATE TABLE creation_lab_events (
      run_id uuid NOT NULL REFERENCES creation_lab_runs(id),
      sequence bigint NOT NULL CHECK(sequence>0), event_id uuid NOT NULL UNIQUE,
      kind text NOT NULL CHECK(kind IN ('draft.created')),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(run_id,sequence)
    )""")
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    for table in ("creation_lab_runs", "creation_lab_events"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        predicate = (
            f"actor_id={actor} AND public.is_platform_staff()"
            if table == "creation_lab_runs"
            else "EXISTS(SELECT 1 FROM creation_lab_runs r WHERE r.id=run_id)"
        )
        op.execute(
            f"CREATE POLICY lab_private ON {table} TO meu_braco_direito_app "
            f"USING ({predicate}) WITH CHECK ({predicate})"
        )
        op.execute(f"GRANT SELECT,INSERT ON {table} TO meu_braco_direito_app")
    op.execute("CREATE INDEX creation_lab_runs_history ON creation_lab_runs(actor_id,tenant_id,business_id,created_at)")


def downgrade():
    op.execute("DROP TABLE creation_lab_events")
    op.execute("DROP TABLE creation_lab_runs")
