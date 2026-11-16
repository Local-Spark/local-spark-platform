"""Retain generated public copy with the piece, independently of diagnostic traces."""

from alembic import op

revision = "0126_creation_lab_copy"
down_revision = "0125_creation_lab_pipeline"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE creation_lab_versions ADD COLUMN copy_ciphertext text")


def downgrade():
    op.execute("ALTER TABLE creation_lab_versions DROP COLUMN copy_ciphertext")
