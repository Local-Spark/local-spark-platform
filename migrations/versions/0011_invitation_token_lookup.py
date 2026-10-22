"""Let a bearer of an invitation token inspect only its matching invitation."""

from alembic import op

revision = "0011_invitation_token_lookup"
down_revision = "0010_phone_verification"
branch_labels = None
depends_on = None


def upgrade():
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    own_email = f"email=(SELECT lower(email) FROM user_accounts WHERE id={actor})"
    exact_token = """(token_digest=nullif(current_setting('app.invitation_digest',true),'')
      AND accepted_at IS NULL AND revoked_at IS NULL AND expires_at>now())"""
    op.execute("DROP POLICY auth_staff_invitation_read ON staff_invitations")
    op.execute(f"""CREATE POLICY auth_staff_invitation_read ON staff_invitations
      FOR SELECT TO meu_braco_direito_auth USING(public.is_platform_staff() OR {own_email} OR {exact_token})""")


def downgrade():
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    own_email = f"email=(SELECT lower(email) FROM user_accounts WHERE id={actor})"
    op.execute("DROP POLICY auth_staff_invitation_read ON staff_invitations")
    op.execute(f"""CREATE POLICY auth_staff_invitation_read ON staff_invitations
      FOR SELECT TO meu_braco_direito_auth USING(public.is_platform_staff() OR {own_email})""")
