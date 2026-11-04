"""Draft: shared owner reads; no effect or selection capability is enabled.

This is not in the project's migration graph. Published markers must first be
created only by a proven writer; the existing selection function remains
ungranted until that happens. Paid effects remain bound to their original actor.
"""

from alembic import op

revision = "0097_reference_shared_read"
down_revision = "0096_reference_contacts_retry"
branch_labels = None
depends_on = None


def upgrade():
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    op.execute(f"""CREATE POLICY reference_published_owner_read ON reference_real_published_results
      FOR SELECT TO meu_braco_direito_app USING(tenant_id={tenant} AND {owner})""")
    op.execute("GRANT SELECT ON reference_real_published_results TO meu_braco_direito_app")
    for table, result_column in (
        ("reference_provider_results", "id"),
        ("reference_provider_result_candidates", "result_id"),
        ("reference_provider_profile_options", "result_id"),
    ):
        op.execute(f"""ALTER POLICY owner_read ON {table} USING (
          tenant_id={tenant} AND {owner} AND EXISTS(
            SELECT 1 FROM reference_real_published_results p
            WHERE p.tenant_id={table}.tenant_id AND p.business_id={table}.business_id
              AND p.result_id={table}.{result_column}))""")
    op.execute(f"""ALTER POLICY owner_read ON reference_provider_places USING (
      tenant_id={tenant} AND {owner} AND EXISTS(
        SELECT 1 FROM reference_provider_result_candidates c
        JOIN reference_real_published_results p ON p.tenant_id=c.tenant_id
          AND p.business_id=c.business_id AND p.result_id=c.result_id
        WHERE c.tenant_id=reference_provider_places.tenant_id
          AND c.business_id=reference_provider_places.business_id
          AND c.place_id=reference_provider_places.id))""")
    op.execute(f"""CREATE POLICY reference_selected_owner_read ON reference_real_selected
      FOR SELECT TO meu_braco_direito_app USING(tenant_id={tenant} AND {owner} AND EXISTS(
        SELECT 1 FROM reference_real_published_results p WHERE p.tenant_id=reference_real_selected.tenant_id
          AND p.business_id=reference_real_selected.business_id AND p.result_id=reference_real_selected.result_id))""")
    op.execute("GRANT SELECT ON reference_real_selected TO meu_braco_direito_app")
    # The selection ledger may see only completed searches with a published
    # result by another owner. Paid effects remain protected by their separate
    # actor-scoped policies and fenced state transitions.
    op.execute(f"""CREATE POLICY reference_published_search_for_selection
      ON reference_provider_searches FOR SELECT TO meu_braco_direito_reference_ledger
      USING(tenant_id={tenant} AND state='completed' AND EXISTS(
        SELECT 1 FROM reference_provider_results r
        JOIN reference_real_published_results p ON p.tenant_id=r.tenant_id
          AND p.business_id=r.business_id AND p.result_id=r.id
        WHERE r.tenant_id=reference_provider_searches.tenant_id
          AND r.business_id=reference_provider_searches.business_id
          AND r.search_id=reference_provider_searches.id))""")


def downgrade():
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    for table in (
        "reference_provider_places",
        "reference_provider_results",
        "reference_provider_result_candidates",
        "reference_provider_profile_options",
    ):
        op.execute(f"ALTER POLICY owner_read ON {table} USING(tenant_id={tenant} AND {owner})")
    op.execute("DROP POLICY reference_published_search_for_selection ON reference_provider_searches")
    op.execute("REVOKE SELECT ON reference_real_selected FROM meu_braco_direito_app")
    op.execute("DROP POLICY reference_selected_owner_read ON reference_real_selected")
    op.execute("REVOKE SELECT ON reference_real_published_results FROM meu_braco_direito_app")
    op.execute("DROP POLICY reference_published_owner_read ON reference_real_published_results")
