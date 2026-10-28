"""Distinguish confirmed single-attempt puts from legacy unknown writers."""

from alembic import op

revision = "0053_collection_put_proof"
down_revision = "0051_editorial_withdrawal"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE business_collection_photos
      ADD COLUMN upload_single_attempt_confirmed boolean NOT NULL DEFAULT false""")
    op.execute("""GRANT UPDATE(upload_single_attempt_confirmed)
      ON business_collection_photos TO meu_braco_direito_app""")


def downgrade():
    op.execute(
        "REVOKE UPDATE(upload_single_attempt_confirmed) ON business_collection_photos FROM meu_braco_direito_app"
    )
    op.execute("ALTER TABLE business_collection_photos DROP COLUMN upload_single_attempt_confirmed")
