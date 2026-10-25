"""Track private MP4 previews alongside the existing JPEG recipe."""

from alembic import op

revision = "0032_video_previews"
down_revision = "0031_static_media_previews"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE media_previews ADD COLUMN mime_type text NOT NULL
      DEFAULT 'image/jpeg' CHECK(mime_type IN ('image/jpeg','video/mp4'))""")
    op.execute("""ALTER TABLE media_previews ADD COLUMN duration_ms integer
      CHECK(duration_ms IS NULL OR duration_ms BETWEEN 1 AND 30000)""")
    op.execute("GRANT UPDATE(duration_ms) ON media_previews TO meu_braco_direito_correlator")


def downgrade():
    op.execute("REVOKE UPDATE(duration_ms) ON media_previews FROM meu_braco_direito_correlator")
    op.execute("ALTER TABLE media_previews DROP COLUMN duration_ms")
    op.execute("ALTER TABLE media_previews DROP COLUMN mime_type")
