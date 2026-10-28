"""Versioned, business-scoped acceptance of the AI service agreement."""

from alembic import op

revision = "0056_service_agreement"
down_revision = "0055_collection_quarantine_guard"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE service_agreement_acceptances (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, version text NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id), notice_hash char(64) NOT NULL,
      accepted_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(tenant_id,business_id,version),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    op.execute("ALTER TABLE service_agreement_acceptances ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE service_agreement_acceptances FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY owner_agreement_select ON service_agreement_acceptances FOR SELECT
      TO meu_braco_direito_app USING(tenant_id={tenant} AND {owner})""")
    op.execute(f"""CREATE POLICY owner_agreement_insert ON service_agreement_acceptances FOR INSERT
      TO meu_braco_direito_app WITH CHECK(tenant_id={tenant} AND actor_id={actor} AND {owner})""")
    op.execute(f"""CREATE POLICY worker_agreement_select ON service_agreement_acceptances FOR SELECT
      TO meu_braco_direito_correlator USING(tenant_id={tenant})""")
    op.execute("GRANT SELECT,INSERT ON service_agreement_acceptances TO meu_braco_direito_app")
    op.execute("""GRANT SELECT(tenant_id,business_id,version,notice_hash)
      ON service_agreement_acceptances TO meu_braco_direito_correlator""")


def downgrade():
    op.execute("DROP TABLE service_agreement_acceptances")
