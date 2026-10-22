"""Restricted, durable WhatsApp message-to-business correlation."""

from alembic import op

revision = "0015_whatsapp_message_routing"
down_revision = "0015_product_brand"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_correlator')
      THEN CREATE ROLE meu_braco_direito_correlator NOLOGIN NOSUPERUSER NOBYPASSRLS; END IF; END $$""")
    op.execute("GRANT USAGE ON SCHEMA public TO meu_braco_direito_correlator")
    op.execute("GRANT SELECT ON alembic_version TO meu_braco_direito_correlator")
    op.execute("""CREATE POLICY correlator_inbox ON whatsapp_inbox TO meu_braco_direito_correlator
      USING(true) WITH CHECK(true)""")
    op.execute("GRANT SELECT ON whatsapp_inbox TO meu_braco_direito_correlator")
    op.execute("GRANT UPDATE(state) ON whatsapp_inbox TO meu_braco_direito_correlator")
    op.execute("CREATE POLICY correlator_links ON whatsapp_channel_links TO meu_braco_direito_correlator USING(true)")
    op.execute("GRANT SELECT ON whatsapp_channel_links TO meu_braco_direito_correlator")
    op.execute("CREATE POLICY correlator_audit ON audit_events TO meu_braco_direito_correlator WITH CHECK(true)")
    op.execute("GRANT INSERT ON audit_events TO meu_braco_direito_correlator")
    op.execute("""CREATE TABLE whatsapp_material_events (
      id uuid PRIMARY KEY,
      tenant_id uuid NOT NULL REFERENCES tenants(id),
      business_id uuid NOT NULL,
      kind text NOT NULL CHECK(kind IN ('text','image','audio','video')),
      ciphertext text NOT NULL,
      state text NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','processing','processed','failed')),
      created_at timestamptz NOT NULL DEFAULT now(),
      expires_at timestamptz NOT NULL,
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("""CREATE INDEX whatsapp_material_pending ON whatsapp_material_events(created_at,id)
      WHERE state='pending'""")
    op.execute("CREATE INDEX whatsapp_material_expiry ON whatsapp_material_events(expires_at)")
    op.execute("ALTER TABLE whatsapp_material_events ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE whatsapp_material_events FORCE ROW LEVEL SECURITY")
    op.execute("""CREATE POLICY correlator_material ON whatsapp_material_events TO meu_braco_direito_correlator
      USING(true) WITH CHECK(true)""")
    op.execute("GRANT SELECT,INSERT,DELETE ON whatsapp_material_events TO meu_braco_direito_correlator")


def downgrade():
    op.execute("DROP TABLE whatsapp_material_events")
    op.execute("DROP POLICY correlator_audit ON audit_events")
    op.execute("REVOKE INSERT ON audit_events FROM meu_braco_direito_correlator")
    op.execute("DROP POLICY correlator_links ON whatsapp_channel_links")
    op.execute("REVOKE SELECT ON whatsapp_channel_links FROM meu_braco_direito_correlator")
    op.execute("DROP POLICY correlator_inbox ON whatsapp_inbox")
    op.execute("REVOKE SELECT,UPDATE(state) ON whatsapp_inbox FROM meu_braco_direito_correlator")
    op.execute("REVOKE SELECT ON alembic_version FROM meu_braco_direito_correlator")
