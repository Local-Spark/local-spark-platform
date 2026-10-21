"""Index unresolved checkouts for bounded Stripe reconciliation scheduling."""

from alembic import op

revision = "0008_checkout_reconciliation"
down_revision = "0007_checkout_opportunities"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE INDEX billing_checkouts_reconciliation
      ON billing_checkouts(livemode,expires_at,id) WHERE status='open' AND session_id IS NOT NULL""")


def downgrade():
    op.execute("DROP INDEX billing_checkouts_reconciliation")
