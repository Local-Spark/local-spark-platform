"""Preserve the productive pending-context gate in the private administrative scope."""

from alembic import op

revision = "0127_creation_lab_pending"
down_revision = "0126_creation_lab_copy"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE POLICY lab_context_read ON business_visual_pending_changes
      FOR SELECT TO meu_braco_direito_app USING(public.creation_lab_read_scope(tenant_id,business_id))""")


def downgrade():
    op.execute("DROP POLICY lab_context_read ON business_visual_pending_changes")
