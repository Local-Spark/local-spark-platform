"""Native credentials and revocable sessions, isolated from tenant runtime privileges."""

from alembic import op

revision = "0003_native_auth"
down_revision = "0002_identity_onboarding"
branch_labels = None
depends_on = None

TABLES = (
    "auth_credentials",
    "auth_sessions",
    "auth_refresh_tokens",
    "auth_actions",
    "auth_mail",
    "auth_challenges",
    "auth_limits",
    "auth_audit",
)


def upgrade():
    op.execute(
        """
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_auth')
THEN CREATE ROLE meu_braco_direito_auth NOLOGIN NOSUPERUSER NOBYPASSRLS; END IF; END $$
"""
    )
    statements = [
        """
CREATE TABLE auth_credentials(user_id uuid PRIMARY KEY REFERENCES user_accounts(id),
email text UNIQUE NOT NULL CHECK(email=lower(btrim(email))), password_hash text,
version integer NOT NULL DEFAULT 1, mfa_secret text, mfa_step bigint NOT NULL DEFAULT
-1,
recovery_hashes jsonb NOT NULL DEFAULT '[]')
""",
        """
CREATE TABLE auth_sessions(id uuid PRIMARY KEY, user_id uuid NOT NULL REFERENCES
user_accounts(id),
csrf_hash char(64) NOT NULL, expires_at timestamptz NOT NULL, revoked boolean NOT
NULL DEFAULT false,
mfa_verified boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT
now())
""",
        """
CREATE TABLE auth_refresh_tokens(digest char(64) PRIMARY KEY, session_id uuid NOT
NULL REFERENCES
auth_sessions(id) ON DELETE CASCADE,
used_at timestamptz)
""",
        """
CREATE TABLE auth_actions(digest char(64) PRIMARY KEY, user_id uuid NOT NULL
REFERENCES user_accounts(id),
purpose text NOT NULL CHECK(purpose IN ('verify','reset')), expires_at timestamptz
NOT NULL)
""",
        """
CREATE TABLE auth_mail(id uuid PRIMARY KEY DEFAULT gen_random_uuid(), action_digest
char(64) NOT NULL
REFERENCES auth_actions(digest) ON DELETE CASCADE,
ciphertext text NOT NULL, state text NOT NULL DEFAULT 'pending' CHECK(state IN
('pending','leased','sent','failed')),
attempts integer NOT NULL DEFAULT 0, available_at timestamptz NOT NULL DEFAULT now(),
lease_until timestamptz, lease_token uuid)
""",
        """
CREATE TABLE auth_challenges(digest char(64) PRIMARY KEY, user_id uuid NOT NULL
REFERENCES user_accounts(id),
version integer NOT NULL, setup_secret text, expires_at timestamptz NOT NULL)
""",
        """
CREATE TABLE auth_limits(key char(64) PRIMARY KEY, attempts integer NOT NULL,
expires_at timestamptz NOT NULL)
""",
        """
CREATE TABLE auth_audit(id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid
REFERENCES user_accounts(id),
event text NOT NULL, created_at timestamptz NOT NULL DEFAULT now())
""",
        "CREATE INDEX auth_session_user ON auth_sessions(user_id)",
        "CREATE INDEX auth_session_expiry ON auth_sessions(expires_at)",
        "CREATE INDEX auth_refresh_session ON auth_refresh_tokens(session_id)",
        "CREATE INDEX auth_action_expiry ON auth_actions(expires_at)",
        "CREATE INDEX auth_challenge_expiry ON auth_challenges(expires_at)",
        "CREATE INDEX auth_limits_expiry ON auth_limits(expires_at)",
        "CREATE INDEX auth_mail_delivery ON auth_mail(state,available_at)",
        """
INSERT INTO auth_credentials(user_id,email) SELECT id,lower(btrim(email)) FROM
(SELECT id,email,count(*) OVER(PARTITION BY lower(btrim(email))) n FROM user_accounts
WHERE email
IS NOT NULL AND btrim(email)<>'') accounts WHERE n=1
""",
    ]
    for sql in statements:
        op.execute(sql)
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY auth_service ON {table} TO meu_braco_direito_auth USING(true) WITH CHECK(true)")
        op.execute(f"GRANT SELECT,INSERT,UPDATE,DELETE ON {table} TO meu_braco_direito_auth")
    op.execute("""
CREATE POLICY auth_accounts ON user_accounts TO meu_braco_direito_auth USING(true) WITH
CHECK(true)
""")
    op.execute("GRANT SELECT,INSERT ON user_accounts TO meu_braco_direito_auth")
    op.execute("GRANT UPDATE(email_verified) ON user_accounts TO meu_braco_direito_auth")
    op.execute("GRANT USAGE ON SCHEMA public TO meu_braco_direito_auth")
    op.execute("GRANT SELECT ON alembic_version TO meu_braco_direito_auth")
    op.execute("GRANT EXECUTE ON FUNCTION public.is_platform_staff() TO meu_braco_direito_auth")


def downgrade():
    op.execute("REVOKE SELECT ON alembic_version FROM meu_braco_direito_auth")
    op.execute("REVOKE EXECUTE ON FUNCTION public.is_platform_staff() FROM meu_braco_direito_auth")
    op.execute("REVOKE SELECT,INSERT,UPDATE(email_verified) ON user_accounts FROM meu_braco_direito_auth")
    op.execute("DROP POLICY auth_accounts ON user_accounts")
    for table in reversed(TABLES):
        op.execute(f"DROP TABLE {table}")
    # Keep the cluster role: a different database may already use it.
