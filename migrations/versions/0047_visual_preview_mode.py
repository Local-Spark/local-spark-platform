"""Track an explicitly simulated visual preview and its validated context."""

from alembic import op

revision = "0047_visual_preview_mode"
down_revision = "0046_visual_attempts"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE media_previews
      ADD COLUMN generation_mode text NOT NULL DEFAULT 'local'
        CHECK(generation_mode IN ('local','visual_fake')),
      ADD COLUMN visual_fingerprint char(64),
      ADD CONSTRAINT media_previews_visual_fingerprint CHECK
        ((generation_mode='local' AND visual_fingerprint IS NULL) OR
         (generation_mode='visual_fake' AND visual_fingerprint IS NOT NULL))""")
    op.execute("GRANT SELECT(generation_mode,visual_fingerprint) ON media_previews TO meu_braco_direito_app")
    op.execute("GRANT INSERT(generation_mode,visual_fingerprint) ON media_previews TO meu_braco_direito_app")
    op.execute("GRANT SELECT(generation_mode,visual_fingerprint) ON media_previews TO meu_braco_direito_correlator")


def downgrade():
    op.execute("ALTER TABLE media_previews DROP CONSTRAINT media_previews_visual_fingerprint")
    op.execute("ALTER TABLE media_previews DROP COLUMN visual_fingerprint,DROP COLUMN generation_mode")
