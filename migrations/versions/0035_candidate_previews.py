"""Distinguish an automatic candidate from an owner-accepted script preview."""

from alembic import op

revision = "0035_candidate_previews"
down_revision = "0034_static_art_adjustments"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE media_previews ADD COLUMN candidate boolean NOT NULL DEFAULT false")


def downgrade():
    op.execute("ALTER TABLE media_previews DROP COLUMN candidate")
