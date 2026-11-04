"""Private shortlist storage for the future, fully evidenced publication.

No runtime role can read or write this table in this slice. Ordering, context
revalidation, recommendation evidence, final copy and temporary-batch cleanup
must be implemented together by a later fenced publication operation.
"""

from alembic import op

revision = "0083_reference_final_publication"
down_revision = "0082_reference_filtered_recovery"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE reference_private_shortlist (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, batch_id uuid NOT NULL,
      candidate_id uuid NOT NULL, position smallint NOT NULL CHECK(position BETWEEN 1 AND 10),
      PRIMARY KEY(tenant_id,business_id,batch_id,candidate_id),
      UNIQUE(tenant_id,business_id,batch_id,position),
      FOREIGN KEY(tenant_id,business_id,batch_id,candidate_id)
        REFERENCES reference_filtered_batch_candidates(tenant_id,business_id,batch_id,candidate_id))""")
    op.execute("ALTER TABLE reference_private_shortlist ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reference_private_shortlist FORCE ROW LEVEL SECURITY")


def downgrade():
    op.execute("LOCK TABLE reference_private_shortlist IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_private_shortlist) THEN
      RAISE EXCEPTION 'REFERENCE_SHORTLIST_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("DROP TABLE reference_private_shortlist")
