"""Read-only access to the business selected by an authenticated lab run."""

from alembic import op

revision = "0121_creation_lab_context"
down_revision = "0120_creation_lab_attachments"
branch_labels = None
depends_on = None

TABLES = (
    "business_context_heads",
    "business_context_versions",
    "business_brand_kit_heads",
    "business_brand_kit_versions",
    "business_collection_photos",
    "visual_ai_consents",
    "visual_consent_gates",
    "service_agreement_acceptances",
)


def upgrade():
    # SECURITY INVOKER deliberately keeps the run's own FORCE RLS active.
    # The transaction-local scope is set by the service, never an HTTP header.
    op.execute("""CREATE FUNCTION creation_lab_read_scope(target_tenant uuid,target_business uuid)
      RETURNS boolean LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog,public AS $$
      SELECT target_tenant=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND public.is_platform_staff()
        AND EXISTS(SELECT 1 FROM public.creation_lab_runs r
          WHERE r.id=nullif(current_setting('app.creation_lab_run_id',true),'')::uuid
            AND r.actor_id=nullif(current_setting('app.actor_id',true),'')::uuid
            AND r.tenant_id=target_tenant AND r.business_id=target_business)
      $$""")
    op.execute("REVOKE ALL ON FUNCTION creation_lab_read_scope(uuid,uuid) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION creation_lab_read_scope(uuid,uuid) TO meu_braco_direito_app")
    for table in TABLES:
        op.execute(f"""CREATE POLICY lab_context_read ON {table} FOR SELECT TO meu_braco_direito_app
          USING(public.creation_lab_read_scope(tenant_id,business_id))""")


def downgrade():
    for table in reversed(TABLES):
        op.execute(f"DROP POLICY lab_context_read ON {table}")
    op.execute("DROP FUNCTION creation_lab_read_scope(uuid,uuid)")
