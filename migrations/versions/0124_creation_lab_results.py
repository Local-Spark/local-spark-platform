"""Private immutable generated files and human feedback, independent of trace expiry."""

from alembic import op

revision = "0124_creation_lab_results"
down_revision = "0123_creation_lab_execution"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE creation_lab_versions (
      id uuid PRIMARY KEY,run_id uuid NOT NULL REFERENCES creation_lab_runs(id),
      number integer NOT NULL CHECK(number>=0),object_key text NOT NULL UNIQUE,
      sha256 char(64) NOT NULL,mime_type text NOT NULL CHECK(mime_type IN ('video/mp4','image/png','image/jpeg')),
      size_bytes bigint NOT NULL CHECK(size_bytes BETWEEN 1 AND 52428800),
      selected boolean NOT NULL DEFAULT false,review_verdict text,
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),UNIQUE(run_id,number))""")
    op.execute("""CREATE TABLE creation_lab_feedback (
      id uuid PRIMARY KEY,run_id uuid NOT NULL REFERENCES creation_lab_runs(id),
      version_id uuid NOT NULL REFERENCES creation_lab_versions(id),operation_id uuid NOT NULL,
      request_hash char(64) NOT NULL,note_ciphertext text NOT NULL,
      timestamp_ms integer CHECK(timestamp_ms BETWEEN 0 AND 60000),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),UNIQUE(run_id,operation_id))""")
    for table in ("creation_lab_versions", "creation_lab_feedback"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY lab_private ON {table} TO meu_braco_direito_app
          USING(EXISTS(SELECT 1 FROM creation_lab_runs r WHERE r.id=run_id))
          WITH CHECK(EXISTS(SELECT 1 FROM creation_lab_runs r WHERE r.id=run_id))""")
        op.execute(f"GRANT SELECT,INSERT ON {table} TO meu_braco_direito_app")
    op.execute("GRANT UPDATE(selected,review_verdict) ON creation_lab_versions TO meu_braco_direito_app")
    op.execute("CREATE UNIQUE INDEX creation_lab_selected_version ON creation_lab_versions(run_id) WHERE selected")


def downgrade():
    op.execute("DROP TABLE creation_lab_feedback")
    op.execute("DROP TABLE creation_lab_versions")
