"""Consent, durable dispatch and private tenant-scoped material receipts."""

from alembic import op

revision = "0016_whatsapp_material"
down_revision = "0015_whatsapp_message_routing"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE whatsapp_processing_consents (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),
      accepted_at timestamptz NOT NULL DEFAULT now(), revoked_at timestamptz,
      PRIMARY KEY(tenant_id,business_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES business_profiles(tenant_id,business_id))""")
    op.execute("""CREATE TABLE whatsapp_material_assets (
      id uuid PRIMARY KEY,
      tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      kind text NOT NULL CHECK(kind IN ('text','image','audio','video')),
      ciphertext text NOT NULL, object_key text, mime_type text,
      size_bytes bigint CHECK(size_bytes>=0), sha256 char(64),
      created_at timestamptz NOT NULL DEFAULT now(),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute(
        "CREATE INDEX whatsapp_material_assets_business ON "
        "whatsapp_material_assets(tenant_id,business_id,created_at DESC,id DESC)"
    )
    op.execute("ALTER TABLE whatsapp_material_events ADD COLUMN attempts integer NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE whatsapp_material_events ADD COLUMN lease_until timestamptz")
    op.execute("ALTER TABLE whatsapp_material_events ADD COLUMN owner_id uuid")
    op.execute("ALTER TABLE whatsapp_material_events ADD COLUMN fencing_token bigint NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE whatsapp_material_events ADD COLUMN processed_at timestamptz")
    op.execute("ALTER TABLE whatsapp_material_events ADD COLUMN error_code text")
    op.execute("ALTER TABLE whatsapp_material_events ADD COLUMN sender_hash char(64)")
    op.execute(
        "CREATE INDEX whatsapp_material_claim ON whatsapp_material_events(created_at,id) "
        "WHERE state IN ('pending','processing')"
    )
    op.execute("""CREATE POLICY correlator_profile_read ON business_profiles FOR SELECT
      TO meu_braco_direito_correlator USING(true)""")
    op.execute("""GRANT SELECT(tenant_id,business_id,phone_verified) ON business_profiles
      TO meu_braco_direito_correlator""")
    op.execute("""CREATE POLICY correlator_membership_read ON memberships FOR SELECT
      TO meu_braco_direito_correlator USING(true)""")
    op.execute("""GRANT SELECT(tenant_id,actor_id,role,active) ON memberships
      TO meu_braco_direito_correlator""")
    op.execute("""CREATE POLICY correlator_account_read ON user_accounts FOR SELECT
      TO meu_braco_direito_correlator USING(true)""")
    op.execute("GRANT SELECT(id,active) ON user_accounts TO meu_braco_direito_correlator")
    for table in ("billing_accounts", "billing_sponsorships"):
        op.execute(
            f"CREATE POLICY correlator_billing_read ON {table} FOR SELECT TO meu_braco_direito_correlator USING(true)"
        )
    op.execute("""GRANT SELECT(tenant_id,livemode,status,paid_until,blocked) ON billing_accounts
      TO meu_braco_direito_correlator""")
    op.execute("""GRANT SELECT(tenant_id,starts_at,ends_at,revoked_at) ON billing_sponsorships
      TO meu_braco_direito_correlator""")
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    for table in ("whatsapp_processing_consents", "whatsapp_material_assets"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY owner_read ON {table} FOR SELECT TO meu_braco_direito_app
          USING(tenant_id={tenant} AND {owner})""")
        op.execute(f"""CREATE POLICY correlator_access ON {table} TO meu_braco_direito_correlator
          USING(true) WITH CHECK(true)""")
        op.execute(f"GRANT SELECT ON {table} TO meu_braco_direito_correlator")
    op.execute("GRANT SELECT ON whatsapp_processing_consents,whatsapp_material_assets TO meu_braco_direito_app")
    op.execute(
        """CREATE POLICY owner_consent_insert ON whatsapp_processing_consents FOR INSERT
      TO meu_braco_direito_app WITH CHECK(tenant_id="""
        + tenant
        + " AND actor_id="
        + actor
        + " AND "
        + owner
        + ")"
    )
    op.execute(
        """CREATE POLICY owner_consent_update ON whatsapp_processing_consents FOR UPDATE
      TO meu_braco_direito_app USING(tenant_id="""
        + tenant
        + " AND "
        + owner
        + ") WITH CHECK(tenant_id="
        + tenant
        + " AND "
        + owner
        + ")"
    )
    op.execute("GRANT INSERT,UPDATE ON whatsapp_processing_consents TO meu_braco_direito_app")
    op.execute("GRANT INSERT ON whatsapp_material_assets TO meu_braco_direito_correlator")
    op.execute(
        "GRANT UPDATE(state,attempts,lease_until,owner_id,fencing_token,processed_at,error_code) "
        "ON whatsapp_material_events TO meu_braco_direito_correlator"
    )
    op.execute(
        """CREATE POLICY owner_material_read ON whatsapp_material_events FOR SELECT TO meu_braco_direito_app
      USING(tenant_id="""
        + tenant
        + " AND "
        + owner
        + ")"
    )
    op.execute(
        "GRANT SELECT(id,tenant_id,business_id,kind,state,created_at,error_code) "
        "ON whatsapp_material_events TO meu_braco_direito_app"
    )


def downgrade():
    op.execute("DROP TABLE whatsapp_material_assets")
    op.execute("DROP TABLE whatsapp_processing_consents")
    op.execute("DROP POLICY owner_material_read ON whatsapp_material_events")
    op.execute(
        "REVOKE SELECT(id,tenant_id,business_id,kind,state,created_at,error_code) "
        "ON whatsapp_material_events FROM meu_braco_direito_app"
    )
    op.execute(
        "REVOKE UPDATE(state,attempts,lease_until,owner_id,fencing_token,processed_at,error_code) "
        "ON whatsapp_material_events FROM meu_braco_direito_correlator"
    )
    op.execute("DROP INDEX whatsapp_material_claim")
    for column in ("attempts", "lease_until", "owner_id", "fencing_token", "processed_at", "error_code", "sender_hash"):
        op.execute(f"ALTER TABLE whatsapp_material_events DROP COLUMN {column}")
    for table in ("billing_accounts", "billing_sponsorships"):
        op.execute(f"DROP POLICY correlator_billing_read ON {table}")
    op.execute(
        "REVOKE SELECT(tenant_id,livemode,status,paid_until,blocked) "
        "ON billing_accounts FROM meu_braco_direito_correlator"
    )
    op.execute(
        "REVOKE SELECT(tenant_id,starts_at,ends_at,revoked_at) "
        "ON billing_sponsorships FROM meu_braco_direito_correlator"
    )
    for table, columns, policy in (
        ("business_profiles", "tenant_id,business_id,phone_verified", "correlator_profile_read"),
        ("memberships", "tenant_id,actor_id,role,active", "correlator_membership_read"),
        ("user_accounts", "id,active", "correlator_account_read"),
    ):
        op.execute(f"DROP POLICY {policy} ON {table}")
        op.execute(f"REVOKE SELECT({columns}) ON {table} FROM meu_braco_direito_correlator")
