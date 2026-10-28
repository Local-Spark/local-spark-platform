"""Aggregate visual reservations without exposing another tenant's data."""

from alembic import op

revision = "0049_visual_global_budget"
down_revision = "0048_visual_consent_gate"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE visual_global_monthly_budget (
      month date PRIMARY KEY, committed_usd_micros bigint NOT NULL DEFAULT 0
        CHECK (committed_usd_micros >= 0),
      updated_at timestamptz NOT NULL DEFAULT now(),
      CHECK (month = date_trunc('month', month::timestamp)::date))""")
    # Fail rather than silently backfill an incomplete RLS-filtered aggregate.
    # PostgreSQL rejects the query if the migration login cannot bypass RLS;
    # this setting does not grant any new privilege.
    op.execute("SET LOCAL row_security = off")
    # Preserve any historical OpenAI holds; only aggregate amounts are visible.
    op.execute("""INSERT INTO visual_global_monthly_budget(month, committed_usd_micros)
      SELECT date_trunc('month',created_at AT TIME ZONE 'UTC')::date,
        sum(CASE WHEN state='completed' THEN actual_usd_micros ELSE reserved_usd_micros END)
      FROM visual_cost_reservations WHERE provider='openai'
      GROUP BY 1""")
    op.execute("SET LOCAL row_security = on")
    op.execute("""GRANT SELECT,INSERT,UPDATE(committed_usd_micros,updated_at)
      ON visual_global_monthly_budget TO meu_braco_direito_correlator""")


def downgrade():
    op.execute("DROP TABLE visual_global_monthly_budget")
