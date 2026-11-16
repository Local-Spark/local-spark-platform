"""Private lab upload claims; no customer collection or commercial output writes."""

from alembic import op

revision = "0120_creation_lab_attachments"
down_revision = "0119_creation_lab_drafts"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE creation_lab_attachments (
      id uuid PRIMARY KEY, run_id uuid NOT NULL REFERENCES creation_lab_runs(id),
      operation_id uuid NOT NULL, request_hash char(64) NOT NULL,
      name_ciphertext text NOT NULL, object_key text NOT NULL UNIQUE,
      kind text NOT NULL CHECK(kind IN ('image','audio','video')),
      mime_type text NOT NULL, sha256 char(64) NOT NULL,
      byte_size bigint NOT NULL CHECK(byte_size BETWEEN 1 AND 52428800),
      rights_confirmed boolean NOT NULL CHECK(rights_confirmed),
      state text NOT NULL CHECK(state IN ('uploading','ready','uncertain')),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      UNIQUE(run_id,operation_id)
    )""")
    op.execute("ALTER TABLE creation_lab_attachments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE creation_lab_attachments FORCE ROW LEVEL SECURITY")
    op.execute("""CREATE POLICY lab_private ON creation_lab_attachments TO meu_braco_direito_app
      USING (EXISTS(SELECT 1 FROM creation_lab_runs r WHERE r.id=run_id))
      WITH CHECK (EXISTS(SELECT 1 FROM creation_lab_runs r WHERE r.id=run_id))""")
    op.execute("GRANT SELECT,INSERT ON creation_lab_attachments TO meu_braco_direito_app")
    op.execute("GRANT UPDATE(state) ON creation_lab_attachments TO meu_braco_direito_app")
    op.execute("ALTER TABLE creation_lab_events DROP CONSTRAINT creation_lab_events_kind_check")
    op.execute("""ALTER TABLE creation_lab_events ADD CHECK(kind IN
      ('draft.created','attachment.uploading','attachment.ready','attachment.uncertain'))""")


def downgrade():
    op.execute("DELETE FROM creation_lab_events WHERE kind LIKE 'attachment.%'")
    op.execute("ALTER TABLE creation_lab_events DROP CONSTRAINT creation_lab_events_kind_check")
    op.execute("ALTER TABLE creation_lab_events ADD CHECK(kind IN ('draft.created'))")
    op.execute("DROP TABLE creation_lab_attachments")
