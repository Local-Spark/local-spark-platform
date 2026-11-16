"""Allow the common owner-scoped execution to reserve productive costs atomically."""

from alembic import op

revision = "0131_message_creation_funding"
down_revision = "0130_message_creation_scope"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE visual_cost_reservations ADD COLUMN estimated_usd_micros bigint CHECK(estimated_usd_micros>=0)"
    )
    op.execute("GRANT UPDATE(estimated_usd_micros) ON visual_cost_reservations TO meu_braco_direito_app")
    # Productive runs use the app-role transaction for fencing, reservation and
    # outbox. A separate correlator transaction would break that atomicity.
    for table in ("visual_cost_reservations", "visual_cost_events"):
        owner = """tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
          AND public.message_creation_owned(tenant_id,nullif(current_setting('app.actor_id',true),'')::uuid)"""
        scoped = f"""{owner} AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid
          AND EXISTS(SELECT 1 FROM creation_lab_runs r
            WHERE r.id=nullif(current_setting('app.creation_lab_run_id',true),'')::uuid
            AND r.origin='whatsapp' AND r.state='running' AND r.execution_token IS NOT NULL
            AND r.tenant_id={table}.tenant_id AND r.actor_id={table}.actor_id)"""
        op.execute(f"CREATE POLICY message_cost_read ON {table} FOR SELECT TO meu_braco_direito_app USING({owner})")
        op.execute(
            f"CREATE POLICY message_cost_insert ON {table} FOR INSERT TO meu_braco_direito_app WITH CHECK({scoped})"
        )
        op.execute(f"GRANT SELECT,INSERT ON {table} TO meu_braco_direito_app")
        if table == "visual_cost_reservations":
            op.execute(
                f"CREATE POLICY message_cost_update ON {table} FOR UPDATE TO meu_braco_direito_app USING({scoped}) WITH CHECK({scoped})"
            )
            op.execute(f"GRANT UPDATE(state,actual_usd_micros,updated_at) ON {table} TO meu_braco_direito_app")
    # This table intentionally contains only aggregate monthly amounts, never
    # tenant identifiers or customer content (same contract as migration 0049).
    op.execute("""GRANT SELECT,INSERT,UPDATE(committed_usd_micros,updated_at)
      ON visual_global_monthly_budget TO meu_braco_direito_app""")


def downgrade():
    raise RuntimeError("Keep funding permissions until productive executions have been reconciled")
