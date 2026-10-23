"""Expose correlated, metadata-only editorial audit events to platform staff."""

from alembic import op

revision = "0024_editorial_operation_events"
down_revision = "0023_editorial_admin_projection"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE FUNCTION public.admin_editorial_operation_events(p_proposal uuid)
      RETURNS TABLE(action text,created_at timestamptz)
      LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      BEGIN
        IF NOT public.is_platform_staff() THEN
          RAISE EXCEPTION 'Staff access required' USING ERRCODE='42501';
        END IF;
        RETURN QUERY SELECT a.action,a.created_at FROM public.editorial_proposals p
          JOIN public.audit_events a ON a.tenant_id=p.tenant_id
            AND a.operation_id=p.id
          WHERE p.id=p_proposal AND a.action IN
            ('editorial.proposal_requested','editorial.proposal_dispatching',
             'editorial.proposal_submitted','editorial.proposal_completed',
             'editorial.proposal_rejected','editorial.proposal_budget_exceeded',
             'editorial.proposal_uncertain')
          ORDER BY a.created_at,a.id;
      END $$""")
    op.execute("REVOKE ALL ON FUNCTION public.admin_editorial_operation_events(uuid) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION public.admin_editorial_operation_events(uuid) TO meu_braco_direito_app")


def downgrade():
    op.execute("DROP FUNCTION IF EXISTS public.admin_editorial_operation_events(uuid)")
