"""Retire the unconsumed billing outbox after preserving its missing audit events.

The migration connection must bypass FORCE RLS. row_security=off fails closed
instead of letting a tenant-filtered backfill silently discard another tenant.
Downgrade reconstructs pending intents from audit; it never claims delivery or
removes the retained financial history.
"""

from alembic import op

revision = "0038_retire_billing_outbox"
down_revision = "0037_brand_kits"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("SET LOCAL row_security=off")
    # Follow the writer's audit -> outbox order before copying and removing it.
    op.execute("LOCK TABLE billing_audit IN SHARE ROW EXCLUSIVE MODE")
    op.execute("LOCK TABLE billing_outbox IN ACCESS EXCLUSIVE MODE")
    op.execute("""INSERT INTO billing_audit(id,tenant_id,operation_id,action,actor_id,created_at)
      SELECT id,tenant_id,operation_id,event_type,NULL,created_at FROM billing_outbox
      ON CONFLICT(operation_id,action) DO NOTHING""")
    # An inconsistent legacy tenant cannot be collapsed by the audit unique key.
    op.execute("""DO $$ BEGIN
      IF EXISTS (
        SELECT 1 FROM billing_outbox o LEFT JOIN billing_audit a
          ON a.operation_id=o.operation_id AND a.action=o.event_type AND a.tenant_id=o.tenant_id
        WHERE a.id IS NULL
      ) THEN
        RAISE EXCEPTION 'Billing outbox history is not fully represented in billing_audit';
      END IF;
    END $$""")
    op.execute("DROP TABLE billing_outbox")


def downgrade():
    op.execute("SET LOCAL row_security=off")
    op.execute("LOCK TABLE billing_audit IN SHARE ROW EXCLUSIVE MODE")
    op.execute("""CREATE TABLE billing_outbox (
      id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES tenants(id), event_type varchar(100) NOT NULL,
      operation_id uuid NOT NULL, state text NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','delivered')),
      created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(operation_id,event_type))""")
    op.execute("""INSERT INTO billing_outbox(id,tenant_id,event_type,operation_id,state,created_at)
      SELECT id,tenant_id,action,operation_id,'pending',created_at FROM billing_audit""")
    op.execute("ALTER TABLE billing_outbox ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE billing_outbox FORCE ROW LEVEL SECURITY")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    member = f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} AND m.actor_id={actor} AND m.active)"
    op.execute("""CREATE POLICY billing_processor ON billing_outbox TO meu_braco_direito_billing
      USING(true) WITH CHECK(true)""")
    op.execute(f"""CREATE POLICY billing_read ON billing_outbox FOR SELECT TO meu_braco_direito_app USING (
      (tenant_id={tenant} AND {member}) OR public.is_platform_staff())""")
    op.execute("""CREATE POLICY billing_staff_event ON billing_outbox FOR INSERT TO meu_braco_direito_app
      WITH CHECK(public.is_platform_staff())""")
    op.execute("GRANT SELECT,INSERT ON billing_outbox TO meu_braco_direito_billing,meu_braco_direito_app")
