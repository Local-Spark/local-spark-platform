"""Index recent checkout attempts for the staff conversion view."""

from alembic import op

revision = "0007_checkout_opportunities"
down_revision = "0006_checkout_return_origin"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE INDEX billing_jobs_checkout_recent ON billing_jobs(created_at DESC,id DESC) WHERE kind='checkout'"
    )


def downgrade():
    op.execute("DROP INDEX billing_jobs_checkout_recent")
