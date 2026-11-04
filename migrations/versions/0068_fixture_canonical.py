"""Associate simulated occurrences across radii with one identity."""

from alembic import op

revision = "0068_fixture_canonical"
down_revision = "0067_reference_cycle"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE reference_discovery_candidates ADD COLUMN IF NOT EXISTS canonical_id uuid")
    op.execute("UPDATE reference_discovery_candidates SET canonical_id=id WHERE canonical_id IS NULL")
    op.execute("ALTER TABLE reference_discovery_candidates ALTER COLUMN canonical_id SET NOT NULL")


def downgrade():
    op.execute("ALTER TABLE reference_discovery_candidates DROP COLUMN canonical_id")
