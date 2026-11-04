"""Durable local simulation of reference discovery."""

from alembic import op

revision = "0065_reference_discovery"
down_revision = "0064_reference_outbox"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE reference_discoveries (
      id uuid PRIMARY KEY, tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id), operation_id uuid NOT NULL,
      context_version bigint NOT NULL, category text NOT NULL, preference jsonb NOT NULL,
      state text NOT NULL CHECK(state IN ('pending','simulated','stale')),
      created_at timestamptz NOT NULL DEFAULT now(), completed_at timestamptz,
      UNIQUE(tenant_id,business_id,operation_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    op.execute("ALTER TABLE reference_discoveries ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reference_discoveries FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY owner_access ON reference_discoveries TO meu_braco_direito_app
      USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute("GRANT SELECT,INSERT,UPDATE(state,completed_at) ON reference_discoveries TO meu_braco_direito_app")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check
      CHECK(event_type IN ('business.created','brand_kit.changed','reference.created','reference.removed',
                          'reference.search_requested'))""")


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM reference_discoveries) OR
         EXISTS(SELECT 1 FROM outbox_events WHERE event_type='reference.search_requested') THEN
        RAISE EXCEPTION 'REFERENCE_DISCOVERIES_PREVENT_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check
      CHECK(event_type IN ('business.created','brand_kit.changed','reference.created','reference.removed'))""")
    op.execute("DROP TABLE reference_discoveries")
