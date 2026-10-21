"""Freeze the validated browser origin before asynchronous checkout creation."""

from alembic import op

revision = "0006_checkout_return_origin"
down_revision = "0005_billing"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE billing_jobs ADD COLUMN return_origin text")


def downgrade():
    op.execute("ALTER TABLE billing_jobs DROP COLUMN return_origin")
