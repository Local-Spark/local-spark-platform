"""Distinguish a pre-submission budget rejection from an uncertain provider effect."""

from alembic import op

revision = "0044_briefing_budget_block"
down_revision = "0043_intent_usage"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE editorial_briefings DROP CONSTRAINT editorial_briefings_state_check")
    op.execute("""ALTER TABLE editorial_briefings ADD CONSTRAINT editorial_briefings_state_check
      CHECK(state IN ('submitted','prepared','needs_clarification','uncertain','budget_blocked'))""")


def downgrade():
    # Preserve any blocked work conservatively; never label it ready for replay
    # on a version that does not distinguish pre-submission outcomes.
    op.execute("UPDATE editorial_briefings SET state='uncertain' WHERE state='budget_blocked'")
    op.execute("ALTER TABLE editorial_briefings DROP CONSTRAINT editorial_briefings_state_check")
    op.execute("""ALTER TABLE editorial_briefings ADD CONSTRAINT editorial_briefings_state_check
      CHECK(state IN ('submitted','prepared','needs_clarification','uncertain'))""")
