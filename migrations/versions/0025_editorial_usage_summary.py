"""Bounded, staff-only daily editorial usage projection."""

from alembic import op

revision = "0025_editorial_usage_summary"
down_revision = "0024_editorial_operation_events"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE INDEX editorial_ai_usage_by_day ON editorial_ai_usage(created_at,tenant_id)")
    op.execute("""CREATE FUNCTION public.admin_editorial_usage_today(p_tenant uuid,p_limit integer)
      RETURNS TABLE(tenant_id uuid,request_count bigint,reserved_tokens bigint,
        observed_tokens bigint,measured_count bigint,uncertain_count bigint,
        in_progress_count bigint,completed_count bigint,last_request_at timestamptz)
      LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      BEGIN
        IF NOT public.is_platform_staff() THEN
          RAISE EXCEPTION 'Staff access required' USING ERRCODE='42501';
        END IF;
        IF p_limit IS NULL OR p_limit < 1 OR p_limit > 100 THEN
          RAISE EXCEPTION 'Invalid limit' USING ERRCODE='22023';
        END IF;
        RETURN QUERY SELECT u.tenant_id,count(*),sum(u.reserved_tokens)::bigint,
          sum(coalesce(u.input_tokens,0)+coalesce(u.output_tokens,0))::bigint,
          count(*) FILTER (WHERE u.input_tokens IS NOT NULL AND u.output_tokens IS NOT NULL),
          count(*) FILTER (WHERE u.state='uncertain'),
          count(*) FILTER (WHERE u.state='submitted'),
          count(*) FILTER (WHERE u.state='completed'),max(u.created_at)
          FROM public.editorial_ai_usage u
          WHERE u.created_at >= date_trunc('day',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'
            AND (p_tenant IS NULL OR u.tenant_id=p_tenant)
          GROUP BY u.tenant_id
          ORDER BY sum(u.reserved_tokens) DESC,u.tenant_id LIMIT p_limit;
      END $$""")
    op.execute("REVOKE ALL ON FUNCTION public.admin_editorial_usage_today(uuid,integer) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION public.admin_editorial_usage_today(uuid,integer) TO meu_braco_direito_app")


def downgrade():
    op.execute("DROP FUNCTION IF EXISTS public.admin_editorial_usage_today(uuid,integer)")
    op.execute("DROP INDEX IF EXISTS editorial_ai_usage_by_day")
