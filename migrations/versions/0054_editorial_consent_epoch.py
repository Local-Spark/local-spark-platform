"""Fence editorial requests against withdrawal and later reauthorization."""

from alembic import op

revision = "0054_editorial_consent_epoch"
down_revision = "0053_collection_put_proof"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE editorial_ai_consents ADD COLUMN generation bigint NOT NULL DEFAULT 0")
    # Existing queued rows predate the consent fence. NULL makes them fail
    # closed without deleting history or guessing which grant authorized them.
    op.execute("ALTER TABLE editorial_proposals ADD COLUMN consent_generation bigint")
    op.execute("GRANT UPDATE(generation) ON editorial_ai_consents TO meu_braco_direito_app")


def downgrade():
    op.execute("ALTER TABLE editorial_proposals DROP COLUMN consent_generation")
    op.execute("ALTER TABLE editorial_ai_consents DROP COLUMN generation")
