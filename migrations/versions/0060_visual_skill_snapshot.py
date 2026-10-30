"""Bind an optional reviewed visual skill to each experimental preview."""

from alembic import op

revision = "0060_visual_skill_snapshot"
down_revision = "0059_visual_ai_preview_mode"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE media_previews
      ADD COLUMN visual_skill_id text,
      ADD COLUMN visual_skill_sha256 char(64),
      ADD CONSTRAINT media_preview_visual_skill CHECK (
        (visual_skill_id IS NULL AND visual_skill_sha256 IS NULL) OR
        (generation_mode='visual_ai' AND visual_skill_id IS NOT NULL
         AND visual_skill_id IN ('instagram-feed-v1','instagram-story-v1')
         AND visual_skill_sha256 IS NOT NULL AND visual_skill_sha256 ~ '^[0-9a-f]{64}$'))""")


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM media_previews WHERE visual_skill_id IS NOT NULL) THEN
        RAISE EXCEPTION 'VISUAL_SKILL_PREVIEWS_PREVENT_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("ALTER TABLE media_previews DROP CONSTRAINT media_preview_visual_skill")
    op.execute("ALTER TABLE media_previews DROP COLUMN visual_skill_sha256,DROP COLUMN visual_skill_id")
