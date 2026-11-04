"""Versioned immutable scores for newly created simulated candidates."""

from alembic import op

revision = "0073_reference_score_snapshot"
down_revision = "0072_reference_effect_simulation"
branch_labels = None
depends_on = None


def upgrade():
    # Existing identities have no provable historical score. Refuse to invent
    # one or silently erase their history; an operator must resolve them first.
    op.execute("LOCK TABLE reference_discovery_candidates IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM reference_discovery_candidates) THEN
        RAISE EXCEPTION 'REFERENCE_CANDIDATES_REQUIRE_SCORE_RECONCILIATION';
      END IF;
    END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("""ALTER TABLE reference_discovery_candidates
      ADD COLUMN reputation_score_snapshot numeric NOT NULL,
      ADD COLUMN reputation_formula_version text NOT NULL,
      ADD COLUMN reputation_fixture_version text NOT NULL,
      ADD CONSTRAINT reference_candidate_score_snapshot CHECK (
        reputation_score_snapshot BETWEEN 0 AND 10
        AND reputation_formula_version ~ '^[a-zA-Z0-9_.-]{1,64}$'
        AND reputation_fixture_version ~ '^[a-zA-Z0-9_.-]{1,64}$')""")


def downgrade():
    # Never erase score history as an automatic downgrade.
    op.execute("LOCK TABLE reference_discovery_candidates IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM reference_discovery_candidates
                WHERE reputation_score_snapshot IS NOT NULL) THEN
        RAISE EXCEPTION 'REFERENCE_SCORE_SNAPSHOTS_PREVENT_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("""ALTER TABLE reference_discovery_candidates
      DROP CONSTRAINT reference_candidate_score_snapshot,
      DROP COLUMN reputation_score_snapshot,
      DROP COLUMN reputation_formula_version,
      DROP COLUMN reputation_fixture_version""")
