"""One immutable owner review per generated storyboard."""

from alembic import op

revision = "0030_editorial_script_review"
down_revision = "0029_whatsapp_delivery"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE editorial_proposals
      ADD COLUMN review_state text CHECK(review_state IN ('accepted','changes_requested')),
      ADD COLUMN review_note text CHECK(review_note IS NULL OR length(review_note)<=600),
      ADD COLUMN review_operation_id uuid,
      ADD COLUMN review_hash char(64),
      ADD COLUMN reviewed_at timestamptz,
      ADD COLUMN reviewed_by uuid REFERENCES user_accounts(id)""")
    op.execute("""CREATE UNIQUE INDEX editorial_proposals_review_operation
      ON editorial_proposals(tenant_id,business_id,review_operation_id)
      WHERE review_operation_id IS NOT NULL""")
    op.execute("""GRANT UPDATE(review_state,review_note,review_operation_id,review_hash,
      reviewed_at,reviewed_by) ON editorial_proposals TO meu_braco_direito_app""")


def downgrade():
    op.execute("DROP INDEX editorial_proposals_review_operation")
    op.execute("""ALTER TABLE editorial_proposals
      DROP COLUMN reviewed_by,DROP COLUMN reviewed_at,DROP COLUMN review_hash,
      DROP COLUMN review_operation_id,DROP COLUMN review_note,DROP COLUMN review_state""")
