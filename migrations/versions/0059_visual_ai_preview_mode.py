"""Identify provider-generated previews without relabeling existing simulations."""

from alembic import op

revision = "0059_visual_ai_preview_mode"
down_revision = "0058_whatsapp_durable_materials"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE media_previews DROP CONSTRAINT media_previews_generation_mode_check")
    op.execute("ALTER TABLE media_previews DROP CONSTRAINT media_previews_visual_fingerprint")
    op.execute("""ALTER TABLE media_previews
      ADD CONSTRAINT media_previews_generation_mode_check
        CHECK(generation_mode IN ('local','visual_fake','visual_ai')),
      ADD CONSTRAINT media_previews_visual_fingerprint CHECK
        ((generation_mode='local' AND visual_fingerprint IS NULL) OR
         (generation_mode IN ('visual_fake','visual_ai') AND visual_fingerprint IS NOT NULL))""")


def downgrade():
    # A paid result must never become a simulation or lose its durable identity.
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM media_previews WHERE generation_mode='visual_ai') THEN
        RAISE EXCEPTION 'VISUAL_AI_PREVIEWS_PREVENT_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("ALTER TABLE media_previews DROP CONSTRAINT media_previews_generation_mode_check")
    op.execute("ALTER TABLE media_previews DROP CONSTRAINT media_previews_visual_fingerprint")
    op.execute("""ALTER TABLE media_previews
      ADD CONSTRAINT media_previews_generation_mode_check
        CHECK(generation_mode IN ('local','visual_fake')),
      ADD CONSTRAINT media_previews_visual_fingerprint CHECK
        ((generation_mode='local' AND visual_fingerprint IS NULL) OR
         (generation_mode='visual_fake' AND visual_fingerprint IS NOT NULL))""")
