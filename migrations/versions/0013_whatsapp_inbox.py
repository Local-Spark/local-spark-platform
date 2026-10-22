"""Encrypted, restricted inbox for signed WhatsApp callbacks."""

from alembic import op

revision = "0013_whatsapp_inbox"
down_revision = "0012_business_phone_edit"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='local_spark_meta')
    THEN CREATE ROLE local_spark_meta NOLOGIN NOSUPERUSER NOBYPASSRLS; END IF; END $$""")
    op.execute("GRANT USAGE ON SCHEMA public TO local_spark_meta")
    op.execute("GRANT SELECT ON alembic_version TO local_spark_meta")
    op.execute("""CREATE TABLE whatsapp_inbox (
      id uuid PRIMARY KEY, dedupe_key char(64) NOT NULL UNIQUE,
      event_kind text NOT NULL CHECK(event_kind IN ('message','status')),
      ciphertext text NOT NULL, state text NOT NULL DEFAULT 'quarantined'
        CHECK(state IN ('quarantined','linked','discarded')),
      received_at timestamptz NOT NULL DEFAULT now(),
      expires_at timestamptz NOT NULL DEFAULT now() + interval '7 days')""")
    op.execute("CREATE INDEX whatsapp_inbox_expiry ON whatsapp_inbox(expires_at)")
    op.execute("ALTER TABLE whatsapp_inbox ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE whatsapp_inbox FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY meta_service ON whatsapp_inbox TO local_spark_meta USING(true) WITH CHECK(true)")
    op.execute("GRANT SELECT,INSERT,UPDATE,DELETE ON whatsapp_inbox TO local_spark_meta")


def downgrade():
    op.execute("DROP TABLE whatsapp_inbox")
    op.execute("REVOKE SELECT ON alembic_version FROM local_spark_meta")
