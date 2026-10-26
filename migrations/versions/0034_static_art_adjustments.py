"""Link immutable visual revisions of static previews to their parent piece."""

from alembic import op

revision = "0034_static_art_adjustments"
down_revision = "0033_editorial_script_versions"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE media_previews
      ADD COLUMN parent_preview_id uuid REFERENCES media_previews(id) ON DELETE SET NULL,
      ADD COLUMN emphasis text NOT NULL DEFAULT 'balanced'
        CHECK(emphasis IN ('balanced','photo','text')),
      ADD COLUMN revision integer NOT NULL DEFAULT 1 CHECK(revision>=1)""")
    op.execute("""CREATE INDEX media_previews_revision
      ON media_previews(tenant_id,business_id,proposal_id,created_at DESC,id DESC)""")


def downgrade():
    op.execute("DROP INDEX media_previews_revision")
    op.execute("""ALTER TABLE media_previews
      DROP COLUMN revision,DROP COLUMN emphasis,DROP COLUMN parent_preview_id""")
