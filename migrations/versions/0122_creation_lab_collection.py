"""Private selection of confirmed business collection photos for lab drafts."""

from alembic import op

revision = "0122_creation_lab_collection"
down_revision = "0121_creation_lab_context"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE creation_lab_collection_choices (
      run_id uuid PRIMARY KEY REFERENCES creation_lab_runs(id),
      selection_ciphertext text NOT NULL,
      updated_at timestamptz NOT NULL DEFAULT clock_timestamp())""")
    op.execute("""CREATE TABLE creation_lab_collection_changes (
      run_id uuid NOT NULL REFERENCES creation_lab_runs(id), operation_id uuid NOT NULL,
      request_hash char(64) NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(run_id,operation_id))""")
    for table in ("creation_lab_collection_choices", "creation_lab_collection_changes"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY lab_private ON {table} TO meu_braco_direito_app
          USING(EXISTS(SELECT 1 FROM creation_lab_runs r WHERE r.id=run_id))
          WITH CHECK(EXISTS(SELECT 1 FROM creation_lab_runs r WHERE r.id=run_id))""")
        op.execute(f"GRANT SELECT,INSERT ON {table} TO meu_braco_direito_app")
    op.execute(
        "GRANT UPDATE(selection_ciphertext,updated_at) ON creation_lab_collection_choices TO meu_braco_direito_app"
    )
    op.execute("ALTER TABLE creation_lab_events DROP CONSTRAINT creation_lab_events_kind_check")
    op.execute("""ALTER TABLE creation_lab_events ADD CHECK(kind IN
      ('draft.created','attachment.uploading','attachment.ready','attachment.uncertain','collection.selected'))""")


def downgrade():
    op.execute("DELETE FROM creation_lab_events WHERE kind='collection.selected'")
    op.execute("ALTER TABLE creation_lab_events DROP CONSTRAINT creation_lab_events_kind_check")
    op.execute("""ALTER TABLE creation_lab_events ADD CHECK(kind IN
      ('draft.created','attachment.uploading','attachment.ready','attachment.uncertain'))""")
    op.execute("DROP TABLE creation_lab_collection_changes")
    op.execute("DROP TABLE creation_lab_collection_choices")
