"""Tenant- and author-scoped worker recovery for revoked simulated work."""

from alembic import op

revision = "0069_reference_recovery"
down_revision = "0068_fixture_canonical"
branch_labels = None
depends_on = None


def upgrade():
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    op.execute(f"""CREATE POLICY reference_recovery_worker ON reference_discoveries
      TO meu_braco_direito_correlator USING(tenant_id={tenant} AND actor_id={actor})
      WITH CHECK(tenant_id={tenant} AND actor_id={actor})""")
    op.execute("""GRANT SELECT,UPDATE(state,completed_at) ON reference_discoveries
      TO meu_braco_direito_correlator""")
    op.execute(f"""CREATE POLICY reference_selection_recovery ON reference_selection_operations
      FOR SELECT TO meu_braco_direito_correlator USING(tenant_id={tenant} AND actor_id={actor})""")
    op.execute("GRANT SELECT ON reference_selection_operations TO meu_braco_direito_correlator")
    op.execute(f"""CREATE POLICY reference_recovery_events ON outbox_events FOR SELECT
      TO meu_braco_direito_correlator USING(tenant_id={tenant} AND
      event_type IN ('reference.search_requested','reference.selection_confirmed')
      AND payload->>'actor_id'={actor}::text)""")
    op.execute("GRANT SELECT(id,tenant_id,event_type,payload) ON outbox_events TO meu_braco_direito_correlator")
    allowed = (
        f"tenant_id={tenant} AND EXISTS(SELECT 1 FROM outbox_events e "
        f"WHERE e.id=event_id AND e.tenant_id={tenant} AND "
        f"e.event_type IN ('reference.search_requested','reference.selection_confirmed') "
        f"AND e.payload->>'actor_id'={actor}::text)"
    )
    op.execute(f"""CREATE POLICY reference_recovery_processed ON processed_events
      TO meu_braco_direito_correlator USING({allowed}) WITH CHECK({allowed})""")
    op.execute("GRANT SELECT,INSERT ON processed_events TO meu_braco_direito_correlator")


def downgrade():
    op.execute("REVOKE SELECT,INSERT ON processed_events FROM meu_braco_direito_correlator")
    op.execute("DROP POLICY reference_recovery_processed ON processed_events")
    op.execute("REVOKE SELECT(id,tenant_id,event_type,payload) ON outbox_events FROM meu_braco_direito_correlator")
    op.execute("DROP POLICY reference_recovery_events ON outbox_events")
    op.execute("REVOKE SELECT ON reference_selection_operations FROM meu_braco_direito_correlator")
    op.execute("DROP POLICY reference_selection_recovery ON reference_selection_operations")
    op.execute("REVOKE SELECT,UPDATE(state,completed_at) ON reference_discoveries FROM meu_braco_direito_correlator")
    op.execute("DROP POLICY reference_recovery_worker ON reference_discoveries")
