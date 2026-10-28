"""Persist the pending withdrawal of an existing editorial consent."""

from alembic import op

revision = "0051_editorial_withdrawal"
down_revision = "0050_visual_pending_changes"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE editorial_ai_consents ADD COLUMN withdrawal_requested_at timestamptz")
    op.execute("ALTER TABLE visual_change_completed_previews ADD COLUMN editorial_consent_accepted_at timestamptz")
    op.execute("GRANT UPDATE(withdrawal_requested_at) ON editorial_ai_consents TO meu_braco_direito_app")


def downgrade():
    op.execute("ALTER TABLE visual_change_completed_previews DROP COLUMN editorial_consent_accepted_at")
    op.execute("ALTER TABLE editorial_ai_consents DROP COLUMN withdrawal_requested_at")
