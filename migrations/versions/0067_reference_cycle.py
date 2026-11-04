"""Private simulated search cycles and confirmed fixture selections."""

from alembic import op

revision = "0067_reference_cycle"
down_revision = "0066_reference_candidates"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE reference_search_cycles (
      id uuid PRIMARY KEY, tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      confirmed_at timestamptz, locked_until timestamptz,
      created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(tenant_id,business_id,id),
      CHECK((confirmed_at IS NULL) = (locked_until IS NULL)),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("""CREATE TABLE reference_search_heads (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, cycle_id uuid,
      PRIMARY KEY(tenant_id,business_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id),
      FOREIGN KEY(tenant_id,business_id,cycle_id) REFERENCES reference_search_cycles(tenant_id,business_id,id))""")
    op.execute("""ALTER TABLE reference_discoveries ADD COLUMN cycle_id uuid,
      ADD COLUMN radius_km smallint CHECK(radius_km IN (5,20,50)),
      ADD FOREIGN KEY(tenant_id,business_id,cycle_id) REFERENCES reference_search_cycles(tenant_id,business_id,id)""")
    op.execute("""CREATE UNIQUE INDEX reference_one_completed_or_pending_per_radius
      ON reference_discoveries(tenant_id,business_id,cycle_id,radius_km)
      WHERE state IN ('pending','simulated') AND cycle_id IS NOT NULL""")
    op.execute("ALTER TABLE reference_discovery_candidates ADD COLUMN selected boolean NOT NULL DEFAULT false")
    op.execute("""CREATE TABLE reference_selection_operations (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, operation_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id), cycle_id uuid NOT NULL,
      request_hash char(64) NOT NULL, response jsonb NOT NULL,
      PRIMARY KEY(tenant_id,business_id,operation_id),
      FOREIGN KEY(tenant_id,business_id,cycle_id) REFERENCES reference_search_cycles(tenant_id,business_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    for table in ("reference_search_cycles", "reference_search_heads", "reference_selection_operations"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY owner_access ON {table} TO meu_braco_direito_app
          USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute(
        "GRANT SELECT,INSERT,UPDATE(confirmed_at,locked_until) ON reference_search_cycles TO meu_braco_direito_app"
    )
    op.execute("GRANT SELECT,INSERT,UPDATE(cycle_id) ON reference_search_heads TO meu_braco_direito_app")
    op.execute("GRANT SELECT,INSERT ON reference_selection_operations TO meu_braco_direito_app")
    op.execute("GRANT UPDATE(selected) ON reference_discovery_candidates TO meu_braco_direito_app")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check
      CHECK(event_type IN ('business.created','brand_kit.changed','reference.created','reference.removed',
                          'reference.search_requested','reference.selection_confirmed'))""")


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM reference_search_cycles) OR EXISTS(SELECT 1 FROM reference_selection_operations) OR
         EXISTS(SELECT 1 FROM outbox_events WHERE event_type='reference.selection_confirmed') THEN
        RAISE EXCEPTION 'REFERENCE_CYCLES_PREVENT_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check
      CHECK(event_type IN ('business.created','brand_kit.changed','reference.created','reference.removed',
                          'reference.search_requested'))""")
    op.execute("DROP TABLE reference_selection_operations")
    op.execute("ALTER TABLE reference_discovery_candidates DROP COLUMN selected")
    op.execute("DROP INDEX reference_one_completed_or_pending_per_radius")
    op.execute("ALTER TABLE reference_discoveries DROP COLUMN cycle_id, DROP COLUMN radius_km")
    op.execute("DROP TABLE reference_search_heads")
    op.execute("DROP TABLE reference_search_cycles")
