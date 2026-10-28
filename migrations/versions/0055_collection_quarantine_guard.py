"""Prevent old writers from transitioning quarantined photo intents to deletion."""

from alembic import op

revision = "0055_collection_quarantine_guard"
down_revision = "0054_editorial_consent_epoch"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE business_collection_photos
      ADD COLUMN upload_quarantined boolean NOT NULL DEFAULT false""")
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM business_collection_photos
        WHERE state='deleting' AND sha256 IS NOT NULL AND NOT upload_single_attempt_confirmed) THEN
        RAISE EXCEPTION 'Unverified collection delete in progress; drain and investigate before migration';
      END IF;
    END $$""")
    # Preserve quarantine intents created by 0053 before the guard existed.
    op.execute("""UPDATE business_collection_photos SET upload_quarantined=true
      WHERE state='pending' AND version=0 AND status='archived' AND sha256 IS NOT NULL
        AND upload_owner IS NULL""")
    op.execute("""ALTER TABLE business_collection_photos ADD CONSTRAINT collection_quarantine_immutable
      CHECK (NOT upload_quarantined OR (state='pending' AND version=0 AND status='archived'
        AND sha256 IS NOT NULL AND upload_owner IS NULL))""")
    op.execute("GRANT UPDATE(upload_quarantined) ON business_collection_photos TO meu_braco_direito_app")


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM business_collection_photos WHERE upload_quarantined) THEN
        RAISE EXCEPTION 'Cannot remove quarantine guard while quarantined uploads exist';
      END IF;
    END $$""")
    op.execute("REVOKE UPDATE(upload_quarantined) ON business_collection_photos FROM meu_braco_direito_app")
    op.execute("ALTER TABLE business_collection_photos DROP CONSTRAINT collection_quarantine_immutable")
    op.execute("ALTER TABLE business_collection_photos DROP COLUMN upload_quarantined")
