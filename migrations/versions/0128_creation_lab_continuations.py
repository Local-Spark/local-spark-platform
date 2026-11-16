"""Linked attempts retain private materials and the original rehearsal ceiling."""

from alembic import op

revision = "0128_creation_lab_continuations"
down_revision = "0127_creation_lab_pending"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE creation_lab_runs
      ADD COLUMN parent_run_id uuid UNIQUE REFERENCES creation_lab_runs(id),
      ADD COLUMN rehearsal_id uuid REFERENCES creation_lab_runs(id),
      ADD COLUMN continuation_hash char(64),
      ADD COLUMN attempt_number integer NOT NULL DEFAULT 1 CHECK(attempt_number BETWEEN 1 AND 10),
      ADD CHECK((parent_run_id IS NULL AND rehearsal_id IS NULL AND continuation_hash IS NULL AND attempt_number=1)
        OR (parent_run_id IS NOT NULL AND rehearsal_id IS NOT NULL AND continuation_hash IS NOT NULL AND attempt_number>1))""")
    op.execute("CREATE INDEX creation_lab_rehearsal ON creation_lab_runs(rehearsal_id,attempt_number)")
    # Immutable uploads can be referenced by multiple attempts. No storage copy,
    # new external effect, or write to the customer's collection is necessary.
    op.execute("ALTER TABLE creation_lab_attachments DROP CONSTRAINT creation_lab_attachments_object_key_key")


def downgrade():
    raise RuntimeError("Continuation history must be retained; downgrade requires an explicit data migration")
