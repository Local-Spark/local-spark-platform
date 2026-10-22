"""Durable business phone challenges; phone_verified remains false until provider approval."""

from alembic import op

revision = "0010_phone_verification"
down_revision = "0009_staff_invitations"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE phone_verification_requests (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),
      phone varchar(30) NOT NULL, e164 varchar(16) NOT NULL,
      request_id uuid NOT NULL, provider_sid text,
      state text NOT NULL CHECK(state IN ('starting','pending','approved','failed')),
      requested_at timestamptz NOT NULL, expires_at timestamptz NOT NULL,
      attempts smallint NOT NULL DEFAULT 0 CHECK(attempts BETWEEN 0 AND 5),
      verified_at timestamptz,
      PRIMARY KEY(tenant_id,business_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES business_profiles(tenant_id,business_id)
    )""")
    op.execute("ALTER TABLE phone_verification_requests ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE phone_verification_requests FORCE ROW LEVEL SECURITY")
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    owner = f"""EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id=phone_verification_requests.tenant_id
      AND m.actor_id={actor} AND m.role='owner' AND m.active)"""
    op.execute(f"""CREATE POLICY owner_phone_request ON phone_verification_requests TO meu_braco_direito_app
      USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute("GRANT SELECT,INSERT,UPDATE ON phone_verification_requests TO meu_braco_direito_app")
    # Updating the verified flag is allowed to the active owner only.
    op.execute("DROP POLICY tenant_isolation ON business_profiles")
    op.execute(
        "CREATE POLICY profile_tenant_read ON business_profiles FOR SELECT TO meu_braco_direito_app "
        f"USING(tenant_id={tenant})"
    )
    op.execute(
        "CREATE POLICY profile_tenant_insert ON business_profiles FOR INSERT TO meu_braco_direito_app "
        f"WITH CHECK(tenant_id={tenant})"
    )
    profile_owner = f"""EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id=business_profiles.tenant_id
      AND m.actor_id={actor} AND m.role='owner' AND m.active)"""
    op.execute(f"""CREATE POLICY profile_owner_update ON business_profiles FOR UPDATE TO meu_braco_direito_app
      USING(tenant_id={tenant} AND {profile_owner}) WITH CHECK(tenant_id={tenant} AND {profile_owner})""")
    op.execute("GRANT UPDATE(phone_verified) ON business_profiles TO meu_braco_direito_app")


def downgrade():
    op.execute("REVOKE UPDATE(phone_verified) ON business_profiles FROM meu_braco_direito_app")
    op.execute("DROP POLICY IF EXISTS profile_owner_update ON business_profiles")
    op.execute("DROP POLICY IF EXISTS profile_tenant_insert ON business_profiles")
    op.execute("DROP POLICY IF EXISTS profile_tenant_read ON business_profiles")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON business_profiles")
    op.execute("""CREATE POLICY tenant_isolation ON business_profiles TO meu_braco_direito_app
      USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid)
      WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid)""")
    op.execute("DROP TABLE phone_verification_requests")
