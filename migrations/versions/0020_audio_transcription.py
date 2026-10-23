"""Durable, private speech transcript and budget reservation."""

from alembic import op

revision = "0020_audio_transcription"
down_revision = "0019_whatsapp_groups"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE whatsapp_processing_consents ADD COLUMN audio_transcription_accepted_at timestamptz")
    op.execute("""ALTER TABLE whatsapp_material_assets
      ADD COLUMN transcription_state text CHECK(transcription_state IN
        ('submitted','completed','uncertain','rejected','budget_exceeded')),
      ADD COLUMN transcript_ciphertext text,
      ADD COLUMN transcription_error text""")
    op.execute("""CREATE TABLE audio_transcription_usage (
      event_id uuid PRIMARY KEY, tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      reserved_seconds integer NOT NULL CHECK(reserved_seconds BETWEEN 1 AND 180),
      state text NOT NULL CHECK(state IN ('submitted','completed','uncertain')),
      created_at timestamptz NOT NULL DEFAULT now(),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("CREATE INDEX audio_usage_daily ON audio_transcription_usage(tenant_id,created_at)")
    op.execute("ALTER TABLE audio_transcription_usage ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE audio_transcription_usage FORCE ROW LEVEL SECURITY")
    op.execute("""CREATE POLICY correlator_usage ON audio_transcription_usage
      TO meu_braco_direito_correlator USING(true) WITH CHECK(true)""")
    op.execute("GRANT SELECT,INSERT,UPDATE(state) ON audio_transcription_usage TO meu_braco_direito_correlator")
    op.execute("""GRANT UPDATE(transcription_state,transcript_ciphertext,transcription_error)
      ON whatsapp_material_assets TO meu_braco_direito_correlator""")


def downgrade():
    op.execute("""REVOKE UPDATE(transcription_state,transcript_ciphertext,transcription_error)
      ON whatsapp_material_assets FROM meu_braco_direito_correlator""")
    op.execute("DROP TABLE audio_transcription_usage")
    op.execute("ALTER TABLE whatsapp_processing_consents DROP COLUMN audio_transcription_accepted_at")
    op.execute("""ALTER TABLE whatsapp_material_assets DROP COLUMN transcription_state,
      DROP COLUMN transcript_ciphertext,DROP COLUMN transcription_error""")
