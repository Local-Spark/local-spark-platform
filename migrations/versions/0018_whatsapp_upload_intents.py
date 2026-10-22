"""Persist object keys before uploading so interrupted attempts can be reconciled."""

from alembic import op

revision = "0018_whatsapp_upload_intents"
down_revision = "0017_whatsapp_retention"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE whatsapp_upload_intents (
      id uuid PRIMARY KEY, event_id uuid NOT NULL, tenant_id uuid NOT NULL,
      business_id uuid NOT NULL, object_key text NOT NULL UNIQUE,
      created_at timestamptz NOT NULL DEFAULT now(),
      reconcile_after timestamptz NOT NULL DEFAULT now()+interval '20 minutes',
      delete_lease_until timestamptz, delete_owner uuid,
      delete_fencing_token bigint NOT NULL DEFAULT 0,
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("CREATE INDEX whatsapp_upload_reconcile_due ON whatsapp_upload_intents(reconcile_after,id)")
    op.execute("ALTER TABLE whatsapp_upload_intents ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE whatsapp_upload_intents FORCE ROW LEVEL SECURITY")
    op.execute("""CREATE POLICY correlator_upload_intents ON whatsapp_upload_intents
      TO meu_braco_direito_correlator USING(true) WITH CHECK(true)""")
    op.execute("GRANT SELECT,INSERT,DELETE ON whatsapp_upload_intents TO meu_braco_direito_correlator")
    op.execute("""GRANT UPDATE(delete_lease_until,delete_owner,delete_fencing_token)
      ON whatsapp_upload_intents TO meu_braco_direito_correlator""")


def downgrade():
    op.execute("DROP TABLE whatsapp_upload_intents")
