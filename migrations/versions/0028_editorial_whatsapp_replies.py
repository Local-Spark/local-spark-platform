"""Durable, encrypted WhatsApp replies tied to editorial decisions."""

from alembic import op

revision = "0028_editorial_replies"
down_revision = "0027_inbound_editorial"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE editorial_whatsapp_replies (
      id uuid PRIMARY KEY REFERENCES editorial_conversation_decisions(id),
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, source_event_id uuid NOT NULL,
      sender_hash char(64) NOT NULL, recipient_ciphertext text NOT NULL,
      state text NOT NULL CHECK(state IN ('pending','submitting','accepted','uncertain','failed','expired')),
      provider_message_id text UNIQUE, error_code text,
      created_at timestamptz NOT NULL DEFAULT now(), expires_at timestamptz NOT NULL,
      attempted_at timestamptz, accepted_at timestamptz,
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("""CREATE INDEX editorial_whatsapp_replies_pending
      ON editorial_whatsapp_replies(created_at,id) WHERE state='pending'""")
    op.execute("ALTER TABLE editorial_whatsapp_replies ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE editorial_whatsapp_replies FORCE ROW LEVEL SECURITY")
    op.execute("""CREATE POLICY correlator_replies ON editorial_whatsapp_replies
      TO meu_braco_direito_correlator USING(true) WITH CHECK(true)""")
    op.execute("""GRANT SELECT,INSERT,DELETE,UPDATE(state,provider_message_id,error_code,attempted_at,accepted_at)
      ON editorial_whatsapp_replies TO meu_braco_direito_correlator""")
    op.execute("""GRANT SELECT(id,actor_id,state,reply)
      ON editorial_conversation_decisions TO meu_braco_direito_correlator""")


def downgrade():
    op.execute("""REVOKE SELECT(id,actor_id,state,reply)
      ON editorial_conversation_decisions FROM meu_braco_direito_correlator""")
    op.execute("DROP TABLE editorial_whatsapp_replies")
