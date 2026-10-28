"""Enforce at most one business per organization, without modifying existing data."""

from alembic import op

revision = "0057_one_business_per_tenant"
down_revision = "0056_service_agreement"
branch_labels = None
depends_on = None


def upgrade():
    # Explicitly fail rather than selecting or deleting any existing business.
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT tenant_id FROM businesses GROUP BY tenant_id HAVING count(*) > 1) THEN
        RAISE EXCEPTION 'ONE_BUSINESS_PER_TENANT_REQUIRES_LEGACY_REVIEW';
      END IF;
    END $$""")
    op.execute("ALTER TABLE businesses ADD CONSTRAINT one_business_per_tenant UNIQUE (tenant_id)")


def downgrade():
    op.execute("ALTER TABLE businesses DROP CONSTRAINT one_business_per_tenant")
