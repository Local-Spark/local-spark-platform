"""Allow the restricted material worker to create decisions from linked messages."""

from alembic import op

revision = "0027_inbound_editorial"
down_revision = "0026_editorial_conversation"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE POLICY correlator_business_timezone ON businesses FOR SELECT
      TO meu_braco_direito_correlator USING(true)""")
    op.execute("GRANT SELECT(id,tenant_id,timezone) ON businesses TO meu_braco_direito_correlator")
    op.execute("""CREATE POLICY correlator_conversation_insert ON editorial_conversation_decisions
      FOR INSERT TO meu_braco_direito_correlator WITH CHECK (true)""")
    op.execute("""CREATE POLICY correlator_conversation_read ON editorial_conversation_decisions
      FOR SELECT TO meu_braco_direito_correlator USING (true)""")
    op.execute("""GRANT INSERT ON editorial_conversation_decisions
      TO meu_braco_direito_correlator""")
    op.execute("""GRANT SELECT(tenant_id,business_id,operation_id)
      ON editorial_conversation_decisions TO meu_braco_direito_correlator""")


def downgrade():
    op.execute("""REVOKE SELECT(tenant_id,business_id,operation_id)
      ON editorial_conversation_decisions FROM meu_braco_direito_correlator""")
    op.execute("REVOKE INSERT ON editorial_conversation_decisions FROM meu_braco_direito_correlator")
    op.execute("DROP POLICY IF EXISTS correlator_conversation_read ON editorial_conversation_decisions")
    op.execute("DROP POLICY correlator_conversation_insert ON editorial_conversation_decisions")
    op.execute("REVOKE SELECT(id,tenant_id,timezone) ON businesses FROM meu_braco_direito_correlator")
    op.execute("DROP POLICY correlator_business_timezone ON businesses")
