"""Pin owner indications to the proposal that can use them."""

from alembic import op

revision = "0063_reference_snapshot"
down_revision = "0062_owner_references"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE editorial_proposals ADD COLUMN owner_reference_snapshot jsonb
      NOT NULL DEFAULT '[]'::jsonb CHECK(jsonb_typeof(owner_reference_snapshot)='array')""")


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM editorial_proposals WHERE owner_reference_snapshot <> '[]'::jsonb) THEN
        RAISE EXCEPTION 'OWNER_REFERENCE_SNAPSHOTS_PREVENT_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("ALTER TABLE editorial_proposals DROP COLUMN owner_reference_snapshot")
