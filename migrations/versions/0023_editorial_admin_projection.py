"""Permit audited staff reads of editorial operation metadata."""

from alembic import op

revision = "0023_editorial_admin_projection"
down_revision = "0022_editorial_proposals"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE FUNCTION public.admin_editorial_operations(p_tenant uuid,p_limit integer)
      RETURNS TABLE(id uuid,operation_id uuid,tenant_id uuid,business_id uuid,state text,
        error_code text,context_version integer,model text,reserved_tokens integer,
        input_tokens integer,output_tokens integer,created_at timestamptz,
        updated_at timestamptz,usage_state text)
      LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      BEGIN
        IF NOT public.is_platform_staff() THEN
          RAISE EXCEPTION 'Staff access required' USING ERRCODE='42501';
        END IF;
        IF p_limit IS NULL OR p_limit < 1 OR p_limit > 100 THEN
          RAISE EXCEPTION 'Invalid limit' USING ERRCODE='22023';
        END IF;
        RETURN QUERY SELECT p.id,p.operation_id,p.tenant_id,p.business_id,p.state,
          p.error_code,p.context_version,p.model,p.reserved_tokens,
          p.input_tokens,p.output_tokens,p.created_at,p.updated_at,u.state
          FROM public.editorial_proposals p
          LEFT JOIN public.editorial_ai_usage u ON u.proposal_id=p.id
          WHERE p_tenant IS NULL OR p.tenant_id=p_tenant
          ORDER BY p.created_at DESC,p.id DESC LIMIT p_limit;
      END $$""")
    op.execute("REVOKE ALL ON FUNCTION public.admin_editorial_operations(uuid,integer) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION public.admin_editorial_operations(uuid,integer) TO meu_braco_direito_app")


def downgrade():
    op.execute("DROP FUNCTION IF EXISTS public.admin_editorial_operations(uuid,integer)")
    # Clean up the first local 0023 draft if it was applied before this revision settled.
    op.execute("DROP POLICY IF EXISTS staff_usage_read ON editorial_ai_usage")
    op.execute("DROP POLICY IF EXISTS staff_proposal_read ON editorial_proposals")
    op.execute("REVOKE SELECT ON editorial_ai_usage FROM meu_braco_direito_app")
