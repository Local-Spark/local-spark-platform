"""Pin the selected references and exact derived learning used by each proposal."""

from alembic import op

revision = "0110_reference_generation"
down_revision = "0109_reference_post_analysis"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE editorial_proposals ADD COLUMN reference_generation_snapshot jsonb
      CHECK(reference_generation_snapshot IS NULL OR (
        jsonb_typeof(reference_generation_snapshot)='object'
        AND reference_generation_snapshot ?& ARRAY['version','selected','learnings']
        AND reference_generation_snapshot->'version'='1'::jsonb
        AND jsonb_typeof(reference_generation_snapshot->'selected')='array'
        AND jsonb_typeof(reference_generation_snapshot->'learnings')='array'))""")
    op.execute("""CREATE FUNCTION reference_generation_snapshot_immutable() RETURNS trigger
      LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$ BEGIN
        IF NEW.reference_generation_snapshot IS DISTINCT FROM OLD.reference_generation_snapshot THEN
          RAISE EXCEPTION 'REFERENCE_GENERATION_SNAPSHOT_IMMUTABLE';
        END IF;
        RETURN NEW;
      END $$""")
    op.execute("REVOKE ALL ON FUNCTION reference_generation_snapshot_immutable() FROM PUBLIC")
    op.execute("""CREATE TRIGGER reference_generation_snapshot_immutable
      BEFORE UPDATE OF reference_generation_snapshot ON editorial_proposals FOR EACH ROW
      EXECUTE FUNCTION reference_generation_snapshot_immutable()""")


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM editorial_proposals WHERE reference_generation_snapshot IS NOT NULL) THEN
        RAISE EXCEPTION 'REFERENCE_GENERATION_SNAPSHOTS_PREVENT_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("DROP TRIGGER reference_generation_snapshot_immutable ON editorial_proposals")
    op.execute("DROP FUNCTION reference_generation_snapshot_immutable()")
    op.execute("ALTER TABLE editorial_proposals DROP COLUMN reference_generation_snapshot")
