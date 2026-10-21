"""Allow the active business owner to correct the phone before verification."""

from alembic import op

revision = "0012_business_phone_edit"
down_revision = "0011_invitation_token_lookup"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("GRANT UPDATE(phone) ON business_profiles TO local_spark_app")


def downgrade():
    op.execute("REVOKE UPDATE(phone) ON business_profiles FROM local_spark_app")
