"""Audited, one-use invitations and revocable staff access."""

from alembic import op

revision = "0009_staff_invitations"
down_revision = "0008_checkout_reconciliation"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE staff_invitations (
      id uuid PRIMARY KEY, invited_by uuid NOT NULL REFERENCES user_accounts(id),
      email text NOT NULL CHECK(email=lower(btrim(email))),
      token_digest char(64) NOT NULL UNIQUE, idempotency_key varchar(128) NOT NULL,
      expires_at timestamptz NOT NULL, accepted_at timestamptz, revoked_at timestamptz,
      created_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE(invited_by,idempotency_key))""")
    op.execute("CREATE INDEX staff_invitations_email ON staff_invitations(email,created_at DESC)")
    op.execute("ALTER TABLE staff_invitations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE staff_invitations FORCE ROW LEVEL SECURITY")
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    own_email = f"email=(SELECT lower(email) FROM user_accounts WHERE id={actor})"
    op.execute(f"""CREATE POLICY auth_staff_invitation_read ON staff_invitations
      FOR SELECT TO local_spark_auth USING(public.is_platform_staff() OR {own_email})""")
    op.execute(f"""CREATE POLICY auth_staff_invitation_create ON staff_invitations
      FOR INSERT TO local_spark_auth WITH CHECK(public.is_platform_staff() AND invited_by={actor})""")
    op.execute(f"""CREATE POLICY auth_staff_invitation_change ON staff_invitations
      FOR UPDATE TO local_spark_auth USING(public.is_platform_staff() OR
        ({own_email} AND accepted_at IS NULL AND revoked_at IS NULL AND expires_at>now()))
      WITH CHECK(public.is_platform_staff() OR
        ({own_email} AND accepted_at IS NOT NULL AND revoked_at IS NULL))""")
    op.execute("GRANT SELECT,INSERT,UPDATE(accepted_at,revoked_at) ON staff_invitations TO local_spark_auth")
    op.execute("ALTER TABLE auth_mail ALTER COLUMN action_digest DROP NOT NULL")
    op.execute("""ALTER TABLE auth_mail ADD COLUMN staff_invitation_id uuid
      REFERENCES staff_invitations(id) ON DELETE CASCADE""")
    op.execute("""ALTER TABLE auth_mail ADD CONSTRAINT auth_mail_exactly_one_action CHECK
      ((action_digest IS NOT NULL) <> (staff_invitation_id IS NOT NULL))""")
    valid_invitation = """EXISTS(SELECT 1 FROM staff_invitations i JOIN user_accounts u
      ON u.id=platform_staff.actor_id AND i.email=lower(u.email)
      WHERE i.accepted_at IS NULL AND i.revoked_at IS NULL AND i.expires_at>now()
        AND u.active AND u.email_verified)"""
    op.execute("CREATE POLICY auth_staff_read ON platform_staff FOR SELECT TO local_spark_auth USING(true)")
    op.execute(
        f"""CREATE POLICY auth_staff_grant ON platform_staff FOR INSERT TO local_spark_auth
          WITH CHECK(actor_id={actor} AND active AND {valid_invitation})"""
    )
    op.execute(
        f"""CREATE POLICY auth_staff_change ON platform_staff FOR UPDATE TO local_spark_auth
          USING(public.is_platform_staff() OR actor_id={actor})
          WITH CHECK((NOT active AND public.is_platform_staff())
            OR (active AND actor_id={actor} AND {valid_invitation}))"""
    )
    op.execute("GRANT SELECT,INSERT,UPDATE(active) ON platform_staff TO local_spark_auth")
    op.execute("""CREATE POLICY auth_platform_audit ON platform_audit FOR INSERT TO local_spark_auth
      WITH CHECK(actor_id=nullif(current_setting('app.actor_id',true),'')::uuid
        AND public.is_platform_staff())""")
    op.execute("GRANT INSERT ON platform_audit TO local_spark_auth")


def downgrade():
    op.execute("REVOKE INSERT ON platform_audit FROM local_spark_auth")
    op.execute("DROP POLICY auth_platform_audit ON platform_audit")
    op.execute("REVOKE SELECT,INSERT,UPDATE(active) ON platform_staff FROM local_spark_auth")
    op.execute("DROP POLICY IF EXISTS auth_staff_change ON platform_staff")
    op.execute("DROP POLICY IF EXISTS auth_staff_grant ON platform_staff")
    op.execute("DROP POLICY IF EXISTS auth_staff_read ON platform_staff")
    op.execute("DROP POLICY IF EXISTS auth_staff_access ON platform_staff")
    op.execute("DELETE FROM auth_mail WHERE staff_invitation_id IS NOT NULL")
    op.execute("ALTER TABLE auth_mail DROP CONSTRAINT auth_mail_exactly_one_action")
    op.execute("ALTER TABLE auth_mail DROP COLUMN staff_invitation_id")
    op.execute("ALTER TABLE auth_mail ALTER COLUMN action_digest SET NOT NULL")
    op.execute("DROP TABLE staff_invitations")
